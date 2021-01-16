""" Find *.tif and *.tiff files by identNr 

    Uses a json file as cache to store path information (e.g. .tif_cache.json)

    For command-line front-end see bin/tif_finder.py

    USAGE as class:
        tf=Tif_finder(cache_fn)
        #work with cache
        tf.scandir(scan_dir)  # scans recursively for *.tif|*.tiff
        tf.iscandir(scan_dir) # rescans dir if cache is older than 1d
        tf.show_cache()       # prints cache to STDOUT 

        #three different searches
        ls=tf.search (needle) # matching path in list, for single needle
        tf.search_xls(needle) # with multiple needles from xls, 
                              # search cache & report to STDOUT

        tf.search_xls(xls_fn, outdir) 
                              # search cache for needles from xls, copy found 
                              # tifs to outdir
                              # output: orig-filename (no).tif
        tf.search_mpx(mpx_fn, outdir) 
                              # search for all identNr in mpx, copy to outdir
                              # output: objId.hash.tif

    In search_xls the original filename is usually preserved; only if multiple 
    tifs have the same name they are varied by adding a number. The downside 
    of this naming scheme is that if Tif_finder is run multiple times, same  
    files will be copied multiple times (because there is no identity). This 
    may naming scheme may be useful for some uses, just beware.
    
    search_mpx uses other naming scheme:
        objId.hash.tif
"""

import datetime
import hashlib
import json
from lxml import etree
import os
from openpyxl import Workbook, load_workbook
from pathlib import Path
import shutil
import time
import MiniLogger

class Tif_finder:
    def __init__(self, cache_fn): 
        """initialize object

        cache_fn: location (path) of cache file"""
        self.cache_fn=cache_fn
        #print ('cache_fn %s' % cache_fn)

        if os.path.exists(self.cache_fn):
            print (f"*cache exists, loading '{self.cache_fn}'")
            with open(self.cache_fn, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache={}

    def scandir (self, scan_dir):
        """Scan dir for tif and store result in tif cache.
        
        Scans directory for *.tif|*.tiff recursively and write results to
        cache file, updating existing cache file or starting new one.
        
        Does a sloppy update, i.e will not remove cache entries for files that
        have been removed from disk. See iscandir to avoid that.
        
        Repeat to scan multiple dirs."""

        print (f"* About to scan {scan_dir}")

        files=Path(scan_dir).rglob('*.tif') # returns generator
        files2=Path(scan_dir).rglob('*.tiff')
        for path in list(files) + list(files2):
            abs = path.resolve()
            base = os.path.basename(abs)
            (trunk,ext)=os.path.splitext(base)
            print (f"{abs}")
            self.cache[str(abs)]=str(trunk)
        print ('* Writing updated cache file')
        self._write_cache()

    def iscandir (self, scan_dir):
        """intelligent directory scan

        scan_dir can be a list

        Do the same scan as in scandir, but also remove cache items whose files
        don't exist on disk anymore and do a repeated scan only if cache is 
        older than 1 day.
        
        Scan multiple directories by passing a list:
            tf.iscandir (['.', '.']) 
        """

        print (f"* About to i-scan {scan_dir}")
        cache_mtime = os.path.getmtime(self.cache_fn)
        now = time.time()
        # print (f"DIFF:{now-cache_mtime}")
        # only if cache is older than one day
        if now-cache_mtime > 3600*24:
            # remove items from cache if file doesn't exist anymore
            for path in list(self.cache)    :
                if not os.path.exists (path):
                    print (f"File doesn't exist anymore; remove from cache {path}")
                    del self.cache[path]
            for dir in scan_dir:
                self.scandir(dir) # writes cache

    def search (self, needle, target_dir=None):
        """Search tif cache for a single needle.

        Return list of matches:
            ls=self.search(needle)
            
        If target_dir is provided copy matches to that dir."""

        # print ("* Searching cache for needle '%s'" % needle)
        ret = [path for path in self.cache if needle in self.cache[path]]

        if target_dir is not None:
            for f in ret:
                self._simple_copy(f,target_dir)
        return ret

    def search_xls (self, xls_fn, target_dir=None):
        """Search tif cache for needles from Excel file.

        Needles are expected (first sheet, column A)
        If target_dir is not None, copy the file to respective directory.
        If target_dir is None just report matching paths to STDOUT"""

        print (f"* Searching cache for needles from Excel file {xls_fn}")

        self.wb = self._prepare_wb(xls_fn)
        #ws = self.wb.active # last active sheet
        ws = self.wb.worksheets[0]
        print (f"* Sheet title: {ws.title}")
        col = ws['A'] # zero or one based?
        for needle in col:
            #print ('Needle: %s' % needle.value)
            if needle != 'None':
                found = self.search(needle.value)
                print(f'found {found}')
                if target_dir is not None:
                    for f in found:
                        self._simple_copy(f,target_dir)

    def search_mpx (self, mpx_fn, target_dir=None):
        """Search tif cache for identNr from mpx.
        
        For each identNr from mpx look for corresponding tifs in cache; if 
        target_dir exists, copy them to target_dir. If target_dir doesn't exist
        just report them to STDOUT."""
        
        if target_dir is not None:
            target_dir = os.path.realpath(target_dir)
            if not os.path.isdir(target_dir):
                os.makedirs (target_dir)
        tree = etree.parse(mpx_fn)
        r = tree.xpath('/m:museumPlusExport/m:sammlungsobjekt/m:identNr', 
            namespaces={'m':'http://www.mpx.org/mpx'})

        for identNr_node in r:
            tifs = self.search (identNr_node.text)
            objId = tree.xpath(f"/m:museumPlusExport/m:sammlungsobjekt/@objId[../m:identNr = '{identNr_node.text}']", 
                namespaces={'m':'http://www.mpx.org/mpx'})[0]
            #print(f"{identNr_node.text}->{objId}")
            found = self.search(identNr_node.text)
            for f in found:
                print (f"{identNr_node.text}->{objId}->{f}")
                if target_dir is not None:
                    self._hash_copy(f, target_dir, objId)

    def show_cache (self):
        """Prints contents of cache to STDOUT"""

        print ('*Displaying cache contents')
        if hasattr (self, 'cache'):
            for item in self.cache:
                print (f"  {item}")
            print (f"Number of tifs in cache: {len(self.cache)}")
        else:
            print (' Cache does not exist!')


############# PRIVATE STUFF #############

    def _init_log (self,outdir):
        #line buffer so everything gets written when it's written, so I can CTRL+C the program
        self._log=open(outdir+'/report.log', mode="a", buffering=1)

    def _write_log (self, msg):
        self._log.write(f"[{datetime.datetime.now()}] {msg}\n")
        print (msg)

    def _close_log (self):
        self._log.close()

    def _target_fn (self, fn):
        """Return filename that doesn't exist yet. 
        
        Check if target exists and if so, find & return new variant that does 
        not yet exist according to the following schema:
            path/to/base.ext
            path/to/base (1).ext
            path/to/base (2).ext
            ..."""

        new = fn
        i = 1
        while os.path.exists (new):
            #print ('Target exists already')
            trunk,ext = os.path.splitext(fn)
            new = f"{trunk} ({i}).{ext}"
            i += 1
        print (f"[{i}] {new}")
        return new

    def _simple_copy(self, source, target_dir):
        """Copy source file to target dir, typically keeping original 
        filename. Only if there already is a file with that name, find a new
        name that doesn't exist yet. 
        
        Upside: we can have multiple tifs for one identNr. 
        Downside: new filenames don't necessarily match the old one."""


        if not os.path.isdir(target_dir):
            raise ValueError ("Error: Target is not directory!")
        #print ('cp %s -> %s' %(source, target_dir))
        self._init_log(target_dir)
        s_base = os.path.basename(source)
        target_fn = self._target_fn(os.path.join(target_dir, s_base)) # should be full path
        if not os.path.isfile(target_fn): #no overwrite
            self._write_log(f"{source} -> {target_fn}") 
            try: 
                shutil.copy2(source, target_fn) # copy2 preserves file info
            except:
                self._write_log(f"File not found: {source}")
        self._close_log()

    def _hash_copy (self, source, target_dir, objId):
        """ Copy *.tif to target_dir/objId.hash.tif"""

        if not os.path.isdir(target_dir):
            raise ValueError ("Error: Target is not directory!")
        self._init_log(target_dir)
        hash = self._file_hash(source)
        target_fn = os.path.join(target_dir, f"{objId}.{hash}.tif")
        if not os.path.isfile(target_fn): #no overwrite
            self._write_log(f"{source} -> {target_fn}") 
            try: 
                shutil.copy2(source, target_fn) # copy2 preserves file info
            except:
                self._write_log(f"File not found: {source}")
        self._close_log()

    def _file_hash (self, fn):
        print (f"About to hash '{fn}'...", end='')
        with open(fn, "rb") as f:
            file_hash = hashlib.md5()
            #while chunk := f.read(8192): #walrus operator requires python 3.8
            #we dont need that if not necessary
            for chunk in iter(lambda: f.read(8192), b''):
                file_hash.update(chunk)
        print('done')
        return file_hash.hexdigest()

    def _prepare_wb(self, xls_fn):
        """Read existing xlsx and return workbook"""

        if os.path.isfile(xls_fn):
            #print (f"File exists ({xls_fn})")
            return load_workbook(filename = xls_fn)
        else:
            raise ValueError (f"Excel file not found: {xls_fn}")

    def _write_cache (self):
        with open(self.cache_fn, 'w') as f:
            json.dump(self.cache, f)

if __name__ == "__main__":
    tf=Tif_finder('.tif_cache.json')
    tf.iscandir ('.')
    tf.iscandir (['.', '.'])
