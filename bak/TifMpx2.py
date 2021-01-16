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
import sys # temporarily
import json
import os
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
        tree = etree.parse(mpx_fn)
        r = tree.xpath('/m:museumPlusExport/m:multimediaobjekt', 
            namespaces={'m':'http://www.mpx.org/mpx'})

        for mume_node in r:
            print (f"{mume_node.text}")

### PRIVATE ###

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





if __name__ == "__main__":
    scan_dir = "M:\MuseumPlus\Produktiv\Multimedia\AKU\Archiv_TIF\SSOZ\III_Zentralasien"
    mpx_fn = "Y:/Turfan-Bilder/20201116/2-MPX/levelup-sort.mpx" #unicode problem \\pk.de\spk\Daten\
    target_dir = "\\pk.de\spk\Daten\BKM-Turfan\Turfan-Bilder\tif"
    o = TifMpx (scan_dir)
    o.search_mpx (mpx_fn, target_dir) #if no target, report only
