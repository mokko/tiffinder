"""
Find and copy tif from mpx

Loop thru mpx/multimedia[erweiterung eq 'jpg'] and look for *.jpg; 
copy their corresponding *.tifs to target_dir

USAGE (object)
    o = TifMpx (scan_dir)
    o.search_mpx (mpx_fn, [target_dir]) #if no target, report only

cache_fn:   Global variable see below; caches the result of the scan_dir; delete
            manually when necessary
logfile:    target_dir/report.log

USAGE Commandline (to do)
    Tifmpx.py -m mpx_fn, -s scan_dir, -t target_dir
"""

import datetime
import json
import os
import shutil 
from lxml import etree
from pathlib import Path

cache_fn = ".tifmpx.json"

class TifMpx:
    def __init__ (self, scan_dir):
        if os.path.exists(cache_fn):
            print (f"*Loading cache '{cache_fn}'")
            with open(cache_fn, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = self._scan_dir (scan_dir)

    def search_mpx (self, mpx_fn, target_dir=None):
        self._init_log (target_dir)

        tree = etree.parse(mpx_fn)
        r = tree.xpath("/m:museumPlusExport/m:multimediaobjekt[m:erweiterung = 'jpg']", 
            namespaces={"m":"http://www.mpx.org/mpx"})

        c = 1
        for mume in r:
            mulId = mume.get("mulId")
            dateiname = mume.findtext("m:dateiname", namespaces={'m':'http://www.mpx.org/mpx'})
            print (f"{c}:{mulId}: '{dateiname}'")
            if dateiname in self.cache.values(): 
                if target_dir is not None:
                    self._copy_fn (target_dir, mulId, dateiname)
            else:
                self._write_log (f"tif equivalent not found: '{dateiname}'")
            c = c + 1
        self._close_log()

### PRIVATE ###

    def _cache_by_name (self, name):
        """ 
        Search the cache for a name and return full path
        
        There could be multiple identical names; this method always returns
        the first path.
        """

        for path, short in self.cache.items():
            if short == name:
                return path
        raise ValueError("Name not found in cache") 
        
    def _close_log (self):
        self._log.close()

    def _copy_fn (self, target_dir, mulId, dateiname):
        target_fn = os.path.join(target_dir, mulId+'.'+ dateiname+'.tif')
        print (f"-> {target_fn}")
        source = self._cache_by_name (dateiname) #finds first only
        if not os.path.exists (target_fn):
            try:
                shutil.copy (source, target_fn)
            except:
                self._write_log(f"Source file not found: {source}")
        #else:
        #    print ("Target exists already, not copied again")

    def _init_log (self,outdir):
        if outdir is None:
            self._log = open(os.devnull,"w")
        else:
            log_fn = os.path.join(outdir,'report.log')
            #line buffer so I can CTRL+C the program at any time
            self._log = open(log_fn, mode="a", buffering=1)

    def _scan_dir (self, scan_dir):
        cache = {}
        files = Path(scan_dir).rglob('*.tif') # returns generator
        files2 = Path(scan_dir).rglob('*.tiff')
        print (f"* About to scan {scan_dir}")
        for path in list(files) + list(files2):
            abs = path.resolve()
            base = os.path.basename(abs)
            (trunk,ext) = os.path.splitext(base)
            print (f"**{trunk}")
            #a path is necessarily unique, a filename not at all
            cache[str(abs)] = str(trunk) 

        with open(cache_fn, 'w') as f:
            json.dump(cache, f)
        return cache

    def _write_log (self, msg):
        self._log.write(f"[{datetime.datetime.now()}] {msg}\n")
        print (msg)


if __name__ == "__main__":
    #scan_dir = r"M:\MuseumPlus\Produktiv\Multimedia\AKU\Archiv_TIF\SSOZ\III_Zentralasien"
    #mpx_fn = r"Y:\Turfan-Bilder\20201116\2-MPX\levelup-sort.mpx" #unicode problem \\pk.de\spk\Daten\
    #target_dir = r"Y:\Turfan-Bilder\tif"
    #o = TifMpx (scan_dir)
    #o.search_mpx (mpx_fn, target_dir) #if no target, report only

    import argparse
    parser = argparse.ArgumentParser(description="Find and copy tif from mpx")
    parser.add_argument("-m", "--mpx_fn", 
        required = True,
        help = "Location of mpx file (full path)")
    parser.add_argument("-s", "--scan_dir", 
        required = True,
        help="The root from which we search recursively for *.tif|*.tiff")
    parser.add_argument("-t", "--target_dir", 
        default = None,
        help="Dir where identified tifs are saved to ($mulId.originalName.tif)")
    args = parser.parse_args()
    o = TifMpx (args.scan_dir)
    o.search_mpx (args.mpx_fn, args.target_dir) #if no target, report only
