"""Find *.tif[f] files by identNr - Command line interface
USAGE:
Cache
    #new cache by scanning dir for *.tif[f]
    tiffinder.py -c cache.json --new_cache scan_dir

    #same, but use intelligent cache update
    tiffinder.py -c cache.json --update cache scan_dir

    #show cache using specified cache_fn
    tiffinder.py -c cache.json  -S

Search
    #Lookup individual needle, cp to pwd
    tiffinder.py -c cache.json -s needle

    #Lookup individual needle, cp to target_dir
    tiffinder.py -c cache.json -s needle -t target_dir

    #lookup multiple needles from xlsx file
    tiffinder.py -c cache.json -x excel_fn

    #read mpx file, lookup all identNr in cache and copy to pwd
    tiffinder.py -c cache.json -m mpx_fn

Output
    #normal search, but don't copy anything, just log what would happen
    tiffinder.py -c cache.json -s neeedle --justlog

    #write preview instead of original file
    tiffinder.py -c cache.json -s neeedle --preview
"""

import argparse
from pathlib import Path
from Tiffinder import Tiffinder


def _output(self, args, r):
    if args.justlog is not False:
        print(f"*JUST LOG")
        self.log_results(r, args.target_dir)
    elif args.preview is not False:
        print(f"*PREVIEW RESULTS")
        self.preview_results(r, args.target_dir)
    else:
        print(f"*COPYING RESULTS")
        self.cp_results(r, args.target_dir)


parser = argparse.ArgumentParser(
    description="tiffinder: Find *.tif[f] files by identNr"
)

if __name__ == "__main__":

    # cache + target_dir
    parser.add_argument("-c", "--cache_fn", required=True, help="Path cache file")
    parser.add_argument(
        "-t",
        "--target_dir",
        default=Path("."),
        help="target directory to write to; defaults to current working directory",
    )
    # main command
    cmd = parser.add_mutually_exclusive_group(required=True)
    cmd.add_argument(
        "-n", "--new_cache", help="Write new cache, expects scan dir", nargs="?"
    )
    cmd.add_argument(
        "-u",
        "--update_cache",
        help="Update existing cache, expects scan dir",
        nargs="?",
    )
    cmd.add_argument(
        "-S", "--show_cache", action="store_true", help="Show cache; no parameter"
    )
    cmd.add_argument(
        "-s", "--search", help="Search for a single needle", nargs="?"
    )  # needle
    cmd.add_argument(
        "-x",
        "--search_xlsx",
        help="Search for all needles in first column of first sheet",
        nargs="?",
    )
    cmd.add_argument(
        "-m", "--search_mpx", help="Search for all needles in mpx/identNr", nargs="?"
    )

    # modify output
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "-o", "--output", action="store_true", help="Modify output (preview, log)"
    )
    output.add_argument(
        "-p",
        "--preview",
        action="store_true",
        help="Don't copy tif, but make a smaller preview instead",
    )
    output.add_argument(
        "-j",
        "--justlog",
        action="store_true",
        help="Don't write any image files, just log",
    )

    args = parser.parse_args()
    print(args)
    print(f"*Loading specified cache '{args.cache_fn}'")

    t = Tiffinder(args.cache_fn)

    if args.new_cache is not None:
        t.scandir(args.new_cache)
    elif args.update_cache is not None:
        t.iscandir(args.update_cache)
    elif args.show_cache is not False:
        t.show_cache()
    elif args.search is not None:
        print(f"*Searching for '{args.search}'")
        r = t.search(args.search)
        _output(t, args, r)
    elif args.search_xlsx is not None:
        print("*Excel input")
        r = t.search_xlsx(args.search_xlsx)
        _output(t, args, r)
    elif args.search_mpx is not None:
        print("*Excel input")
        r = t.search_mpx(args.search_mpx)
        _output(t, args, r)
