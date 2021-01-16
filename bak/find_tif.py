"""
This script speeds up searches for filenames. It can also copy files that
are found to a target directory (TARGET_DIR).

It works by caching filenames from SCAN_DIR to a CACHE file.

EXAMPLE
(1) make or update cache file
    tif_finder -u SCAN_DIR [-c CACHE]
            # scan SCAN_DIR recursivley for *.tif|*.tiff files and 
            # write new cache to CACHE; default location is .tif_cache.json

(2) simple search (one needle)
    tif_finder.py -s needle -c CACHE
            # search needle in cache and report found files

(3) search and copy
    tif_finder.py -s needle -t target_dir -c CACHE

USAGE:
    tif_finder.py -u scan_dir     starts a new cache by scanning dir for *.tif|*.tiff

    tif_finder.py -s needle       search needle in cache and report found files
    tif_finder.py -s needle -t target_dir
        search needle in cache and copy found tifs to target_dir
    tif_finder.py -x excel_fn     get needles from xlsx file, report found tifs
    tif_finder.py -x excel_fn -t target_dir
        read excel file, look for identNr in first column of first sheet
        look up all identNr in cache and copy found tifs to target dir using
        the convention:
            target_dir/filename.tif
            target_dir/filename (1).tif
    
    tif_finder.py -S              show cache
    tif_finder.py -S -c cache_fn  show cache using specified cache_fn

    tif_finder.py -m mpx_fn -c cache_fn 
        read mpx file, lookup all identNr in cache and REPORT files to STDOUT
    tif_finder.py -m mpx_fn -c cache_fn -t target_dir
        read mpx, lookup all identNr in cache and COPY found files to 
        target_dir using the convention 
            target_dir/objId.hash.tif (CHECK)
"""

import os 
import sys 
import argparse
from os.path import expanduser

lib=os.path.realpath(os.path.join(__file__,'../../lib'))
sys.path.append (lib)

from Tif_finder import Tif_finder

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cache_fn')
    parser.add_argument('-m', '--mpx')
    parser.add_argument('-s', '--search')
    parser.add_argument('-S', '--show_cache', action='store_true')
    parser.add_argument('-t', '--target_dir')
    parser.add_argument('-u', '--update_cache')
    parser.add_argument('-x', '--xls')

    args = parser.parse_args()
    if args.cache_fn is None:
        home = expanduser("~")
        args.cache_fn=os.path.join(home, '.tif_finder.json')
        print ('*No cache specified, looking at default location')
    else:
        print (f"*Loading specified cache '{args.cache_fn}'")

    t=Tif_finder(args.cache_fn)

    if args.update_cache is not None:
        t.scandir(args.update_cache)
    elif args.show_cache:
        t.show_cache()
    elif args.search is not None and args.target_dir is not None:
        print(f"*Searching for '{args.search}' with target_dir '{args.target_dir}'")
        t.search (args.search, args.target_dir)
    elif args.search is not None and not args.target_dir:
        print(f"*Searching for '{args.search}' without target_dir")
        ls=t.search(args.search)
        for positive in ls:
            print(positive)
    elif args.xls is not None and args.target_dir is not None:
        t.search_xls (args.xls, args.target_dir)
    elif args.xls is not None and not args.target_dir:
        t.search_xls(args.xls)
    elif args.mpx is not None:
        print("*MPX mode")
        t.search_mpx(args.mpx, args.target_dir)
    else:
        raise ValueError ('Unknown command line argument')
