""" Find *.tif[f] files by identNr 

    Uses a json file as cache to store path information (e.g. .tif_cache.json)

    For command-line front-end see end of this file.

    USAGE as class:
        tf = Tif_finder(cache_fn)

        #working with the cache
        tf.scandir(scan_dir)  # scans recursively for *.tif|*.tiff
        tf.iscandir(scan_dir) # rescans dir if cache is older than 1d
        tf.show_cache()       # prints cache to STDOUT 

        #three different searches
        ls=tf.search (needle) # matching path in list, for single needle
        r = tf.search_xls(needle) # with multiple needles from xls, 
                              # search cache & report to STDOUT

        r = tf.search_xls(xls_fn, outdir) 
                              # search cache for needles from xls, copy found 
                              # tifs to outdir
                              # output: orig-filename (no).tif
        r = tf.search_mpx(mpx_fn, outdir) 
                              # search for all identNr in mpx, copy to outdir
                              # output: objId.hash.tif
        #do stuff with search results
        tf.cp_results(results, target_dir, [policy])
        tf.log_results(results, [policy])
        tf.preview_results(results, target_dir, [policy]) 

    Filename Policy
    - default: Preserve except if not unique
    - hash: objId.hash.tif
    - DAid: DAid.origname.tif

    When a file is copied, the original filename is usually preserved; only if 
    multiple tifs have the same name they are varied by adding a number. The 
    downside of this naming scheme is that if Tif_finder runs multiple times, 
    same files will be copied multiple times (because there is no identity). This 
    naming scheme may be useful for some uses, just beware.
    
    search_mpx uses other naming scheme:
        objId.hash.tif
        
    MulId naming scheme
        DAid.origname.tif
"""

import datetime
import filecmp
import hashlib
import json
import logging
import pprint
from lxml import etree
#import os
import shutil
import time
from PIL import Image
from openpyxl import Workbook, load_workbook
from pathlib import Path
from glob import iglob


class Tif_finder:
    def __init__(self, cache_fn):
        """initialize object

        cache_fn: location (path) of cache file"""
        self.cache_fn = cache_fn
        # print ('cache_fn %s' % cache_fn)

        if Path(self.cache_fn).exists():
            print(f"*cache exists, loading '{self.cache_fn}'")
            with open(self.cache_fn, "r") as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def scandir(self, scan_dir):
        """Scan dir for tif and store result in tif cache.

        Scans directory for *.tif|*.tiff recursively and write results to
        cache file, updating existing cache file or starting new one.

        Does a sloppy update, i.e will not remove cache entries for files that
        have been removed from disk. See iscandir to avoid that.

        Repeat to scan multiple dirs."""
        scan_dir = Path(scan_dir).joinpath("**", "*.ti[f*]")
        for path in iglob(scan_dir, recursive=True):
            abs = Path(path).resolve()
            needle = abs.stem.replace("_", " ")
            print(f"{abs}")
            self.cache[str(abs)] = needle
        self._write_cache()

    def iscandir(self, scan_dir):
        """intelligent directory scan

        scan_dir can be a list

        Do the same scan as in scandir, but also remove cache items whose files
        don't exist on disk anymore and do a repeated scan only if cache is
        older than 1 day.

        Scan multiple directories by passing a list:
            tf.iscandir (['.', '.'])
        """

        print(f"* About to i-scan {scan_dir}")
        cache_mtime = os.path.getmtime(self.cache_fn)
        now = time.time()
        # print (f"DIFF:{now-cache_mtime}")
        # only if cache is older than one day
        if now - cache_mtime > 3600 * 24:
            # remove items from cache if file doesn't exist anymore
            for path in list(self.cache):
                if not os.path.exists(path):
                    print(f"File doesn't exist anymore; remove from cache {path}")
                    del self.cache[path]
            for dir in scan_dir:
                self.scandir(dir)  # writes cache

    def search(self, needle, target_dir=None):
        """Search tif cache for a single needle.

        Return list of matches:
            ls=self.search(needle)

        If target_dir is provided copy matches to that dir."""

        # print ("* Searching cache for needle '%s'" % needle)
        return [path for path in self.cache if needle in self.cache[path]]

    def search_xls(self, xls_fn, target_dir=None):
        """Search tif cache for needles from Excel file.

        Needles are expected (first sheet, column A)
        If target_dir is not None, copy the file to respective directory.
        If target_dir is None just report matching paths to STDOUT"""

        print(f"* Searching cache for needles from Excel file {xls_fn}")

        self.wb = self._prepare_wb(xls_fn)
        # ws = self.wb.active # last active sheet
        ws = self.wb.worksheets[0]
        print(f"* Sheet title: {ws.title}")
        col = ws["A"]  # zero or one based?
        results = []
        for needle in col:
            if needle.value is not None:
                print(f"* Looking for '{needle.value}'")
                found = self.search(needle.value)
                print(f"* FOUND: {len(found)}")
                for each in found:
                    print(f"\teach")
                results.extend(found)
        return results

    def search_mpx(self, mpx_fn, target_dir=None):
        """Search tif cache for identNr from mpx.

        For each identNr from mpx look for corresponding tifs in cache; if
        target_dir exists, copy them to target_dir. If target_dir doesn't exist
        just report them to STDOUT."""

        if target_dir is not None:
            target_dir = os.path.realpath(target_dir)
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
        tree = etree.parse(mpx_fn)
        r = tree.xpath(
            "/m:museumPlusExport/m:sammlungsobjekt/m:identNr",
            namespaces={"m": "http://www.mpx.org/mpx"},
        )

        results = []
        for identNr_node in r:
            tifs = self.search(identNr_node.text)
            objId = tree.xpath(
                f"/m:museumPlusExport/m:sammlungsobjekt/@objId[../m:identNr = '{identNr_node.text}']",
                namespaces={"m": "http://www.mpx.org/mpx"},
            )[0]
            # print(f"{identNr_node.text}->{objId}")
            found = self.search(identNr_node.text)
            for f in found:
                print(f"{identNr_node.text}->{objId}->{f}")
                results.extend(found)
            return results

    def show_cache(self):
        """Prints contents of cache to STDOUT"""

        print("*Displaying cache contents")
        if hasattr(self, "cache"):
            for item in self.cache:
                print(f"  {item}")
            print(f"Number of tifs in cache: {len(self.cache)}")
        else:
            print("Cache does not exist!")

    #
    # output
    #
    def cp_results(self, results, target_dir, policy=None):
        """ Copy files from the search_results to target_dir."""
        self._init_log(target_dir)

        for f in results:
            target_fn = self._default_policy(f, target_dir)
            print(f"{f}->")
            if target_fn is None:
                print(" identical file already exists at target")
            else:
                print(f" {target_fn}")
                self._simple_copy(f, target_fn)

    def log_results(self, results, args):
        """ Just print the log to target_dir, don't copy anything."""
        for f in results:
            print(f)
            #todo logging

    def preview_results(self, results, target_dir, policy=None):
        """Make previews for the search results and copy those to target_dir."""
        for f in results:
            target_fn = self._default_policy(f, target_dir, "jpg")
            if target_fn is None:
                print(" identical file already exists at target")
            else:
                self._preview(f, target_fn)


    ############# PRIVATE STUFF #############

    def _default_policy(self, source, target_dir, new_ext=None):
        """Returns target filename as pathlib object or None if identical
        file is already present at target_dir.
        
        If non identical files with the same exists already in target_dir,
        a numbered variant is returned. 
            target_dir/name.suffix
            target_dir/name (1).suffix
            ...
        Expects a full path as str for source, returns Pathlib object.
        """
        i = 2
        new = Path(source)
        if new_ext is None:
            suffix = Path(new).suffix
        else:
            suffix = "." + new_ext

        parent = new.parent
        target_fn = Path(target_dir).joinpath(new.name)
        #print(f"TTT:{target_fn}")
        while target_fn.exists():  # why while?
            #file with that name exists already
            if filecmp.cmp(source, target_fn, shallow=False):
                #print(f"POLICY: identical file, no copy")
                return None
            else:
                target_fn = parent.joinpath(f"{new.stem} ({i}){suffix}")
            i += 1
        #print(f"POLICY: [{i}] {new}")
        return target_fn

    def _init_log(self, outdir):
        log_fn = Path(outdir).joinpath("report.log")

        logging.basicConfig(
            datefmt="%Y%m%d %I:%M:%S %p",
            filename=log_fn,
            filemode="w",
            level=logging.DEBUG,
            format="%(asctime)s: %(message)s",
        )

    def _simple_copy(self, source, target):
        """Copy source to target. Expects full paths."""

        #print(f"{source} ->\n\t{target}")
        if not target.is_file():  # no overwrite
            try:
                shutil.copy2(source, target)  # copy2 preserves file info
            except:
                logging.debug(f"File not found: {source}")

    def _prepare_wb(self, xls_fn):
        """Read existing xlsx and return workbook"""

        if Path(xls_fn).is_file():
            # print (f"File exists ({xls_fn})")
            return load_workbook(filename=xls_fn)
        else:
            raise ValueError(f"Excel file not found: {xls_fn}")

    def _write_cache(self):
        print("* Writing updated cache file")
        with open(self.cache_fn, "w") as f:
            json.dump(self.cache, f, indent=1)

    def _preview(f, target_fn):
        im = Image.open(f)

        if policy is None:
            new_str = Path(target_dir).joinpath(f.stem + ".jpg")
        else:
            raise (TypeError, "policy not implemented yet")

        if not Path(new_str).exists():
            if im.height > 720:
                ratio = 720 / im.height
                new_size = round(im.width * ratio), round(im.height * ratio)
                print(f"{f}: ({im.width}, {im.height}) -> {new_size} {ratio}")
                im.thumbnail(new_size)
            rgb_im = im.convert("RGB")
            print(f"\t saving {new_str}")
            rgb_im.save(new_str)
        else:
            print(f"{new_str} exists already.")


if __name__ == "__main__":
    """
    USAGE:
    Cache
        #new cache by scanning dir for *.tif[f]
        Tif_finder.py -c cache.json -u scan_dir

        #same, but update cache 
        Tif_finder.py -c cache.json -i -u scan_dir

        #show cache using specified cache_fn
        Tif_finder.py -c cache.json  -S 

    Search
        #Lookup individual needle, cp to pwd
        Tif_finder.py -c cache.json -s needle       

        #Lookup individual needle, cp to target_dir
        Tif_finder.py -c cache.json -s needle -t target_dir      

        #lookup multiple needles from xlsx file
        Tif_finder.py -c cache.json -x excel_fn     

        #read mpx file, lookup all identNr in cache and copy to pwd
        Tif_finder.py -c cache.json -m mpx_fn 

    Output
        #normal search, but don't copy anything, just log what would happen
        Tif_finder.py -c cache.json -s neeedle --justlog

        #write preview instead of original file
        Tif_finder.py -c cache.json -s neeedle --preview
    """

    import argparse
    from pathlib import Path

    # from Tif_finder import Tif_finder
    def _output(self, args, r):
        print("*Using args")
        print(args)
        if args.justlog is not None:
            print(f"*Just log")
            self.log_results(r, args.target_dir, args)
        else:
            if args.preview is not None:
                print(f"*Preview results")
                self.preview_results(r, args.target_dir, args.policy)
            else:
                print(f"*Copying results")
                self.cp_results(r, args.target_dir, args.policy)

    parser = argparse.ArgumentParser()

    # cache
    parser.add_argument("-c", "--cache_fn", required=True)
    parser.add_argument("-S", "--show_cache", action="store_true")
    parser.add_argument("-u", "--update_cache")
    parser.add_argument("-i", "--intelligent", action="store_true")

    # search
    parser.add_argument("-m", "--mpx")
    parser.add_argument("-s", "--search") # needle
    parser.add_argument("-x", "--xls")

    # output
    # if no target_dir, assume current working directory
    parser.add_argument("-t", "--target_dir", default=".")
    parser.add_argument("-P", "--preview") # not implemented
    parser.add_argument("-p", "--policy")  # not implemented
    parser.add_argument("-j", "--justlog") # not implemented
    
    args = parser.parse_args()
    if args.target_dir is None:
        args.target_dir = Path(".")
    
    print(f"*Loading specified cache '{args.cache_fn}'")

    t = Tif_finder(args.cache_fn)

    if args.update_cache is not None:
        print(f"* About to scan {args.update_cache}")
        if args.intelligent is not None:
            t.iscandir(args.update_cache)
        else:
            t.scandir(args.update_cache)

    elif args.show_cache:
        t.show_cache()

    elif args.search is not None:
        print(f"*Searching for '{args.search}'")
        r = t.search(args.search)
        _output(t, args, r)

    elif args.xls is not None:
        print("*Excel input")
        r = t.search_xls(args.xls)
        _output(t, args, r)

    elif args.mpx is not None:
        print("*MPX mode")
        r = t.search_mpx(args.mpx)
        _output(t, args, r)

    else:
        raise ValueError("Unknown command line argument")
