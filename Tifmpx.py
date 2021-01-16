"""
INPUT1: mpx with many multimediaobjekte
INPUT2: dir path where tifs are stored, e.g. M:\MuseumPlus\Produktiv\Multimedia\AKU\Archiv_TIF

First step is to create in memory cache where we associate $dirname with file_tif_path, e.g.

cache={
    "A 110" : "M:\MuseumPlus\Produktiv\Multimedia\AKU\Archiv_TIF\SSOZ\III_Zentralasien\Expeditionsfotos\A 110.tif"
}

only *.tif and *.tiff are allowed case-insensitive

TWO
Then we loop thru mpx multimedia. For every jpg we look for a tif equivalent 
e.g. 
"B 1043 Kara Kodscha Unsere Wohnung pos.jpg" -> "B 1043 Kara Kodscha Unsere Wohnung pos.tif"

THREE
If equivalent found, save it as 
    $mulId.$origFileName.tif

FOUR
If not found, write error log

OTHER THOUGHTS
- We dont want to fake multimediaobjekte this time around. Let the Stabi do that.
- We could write this to use jpg as input or mpx as input. Without mpx we dont have the mulId.

USAGE (object)
    o = TifMpx (scan_dir)
    o.search_mpx (mpx_fn, [target_dir]) #if no target, report only

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
        if target_dir is not None:
            self._init_log (target_dir)

        tree = etree.parse(mpx_fn)
        r = tree.xpath('/m:museumPlusExport/m:multimediaobjekt', 
            namespaces={'m':'http://www.mpx.org/mpx'})

        c = 1
        for mume in r:
            mulId = mume.get("mulId")
            dateiname = mume.findtext("m:dateiname", namespaces={'m':'http://www.mpx.org/mpx'})
            print (f"{c}:{mulId}: '{dateiname}'")
            if dateiname in self.cache: 
                if target_dir is not None:
                    self._copy_fn (target_dir, mulId, dateiname)
            else:
                self._write_log (f"tif equivalent not found: '{dateiname}'")
            c = c + 1

### PRIVATE ###

    def _close_log (self):
        self._log.close()

    def _copy_fn (self, target_dir, mulId, dateiname):
        target_fn = os.path.join(target_dir, mulId+'.'+ dateiname+'.tif')
        print (f"-> {target_fn}")
        if not os.path.exists (target_fn):
            try:
                shutil.copy (self.cache[dateiname], target_fn)
            except:
                self._write_log(f"Source file not found: {self.cache[dateiname]}")
        else:
            print ("Target exists already!")

    def _init_log (self,outdir):
        #line buffer so everything gets written when it's written, so I can CTRL+C the program
        self._log=open(outdir+'/report.log', mode="a", buffering=1)

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
            cache[str(trunk)] = str(abs)
        with open(cache_fn, 'w') as f:
            json.dump(cache, f)
        return cache


    def _write_log (self, msg):
        self._log.write(f"[{datetime.datetime.now()}] {msg}\n")
        print (msg)





if __name__ == "__main__":
    scan_dir = "M:\MuseumPlus\Produktiv\Multimedia\AKU\Archiv_TIF\SSOZ\III_Zentralasien"
    mpx_fn = r"Y:\Turfan-Bilder\20201116\2-MPX\levelup-sort.mpx" #unicode problem \\pk.de\spk\Daten\
    target_dir = r"Y:\Turfan-Bilder\tif"
    o = TifMpx (scan_dir)
    o.search_mpx (mpx_fn, target_dir) #if no target, report only
