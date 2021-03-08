"""
Shrink *.tif files proportionally so that the longest size is 3508 px. If 
longest size is already smaller than 3508 px, leave it be. DinA4 is 210x297 mm.
At 300 dpi this makes 2480 x 3508 px. Currently, this script acts on *.tif (on 
pwd).

Pillow's resize creates a new image without exif information.
Pillow is known to have issues with metadata; specifically it's allergic to non
standard tags or tags in the wrong format, so I have to manually delete those
below. 

Internally, pillow seems to use LibTiff to access tiffs.

You can use exif2 for a different libary providing access to metadata. 

For info on exif tags see:
* https://exiv2.org/tags.html
"""

from pathlib import Path
from PIL import Image, TiffTags

# from PIL.ExifTags import TAGS

shape = "-DinA4.tif"


def per_file(f):
    im = Image.open(f)

    if im.width > im.height:
        ratio = 3508 / im.width
    else:
        ratio = 3508 / im.height
    new_size = round(im.width * ratio), round(im.height * ratio)

    if ratio < 1:  # only shrink, dont inflate
        new_str = f.stem + shape
        if not Path(new_str).is_file():
            # print(Image.TiffTags.TAGS_V2)
            print(f"{f}: ({im.width}, {im.height}) -> {new_size} {ratio}")
            # I get error with test image
            # https://github.com/python-pillow/Pillow/issues/5314
            # Image.DEBUG=True
            im.thumbnail(new_size, resample=Image.LANCZOS)
            TiffTags.TAGS_V2[33723] = TiffTags.TagInfo("IptcNaaInfo", TiffTags.BYTE, 0)
            print(f"\t saving {new_str}")
            im.save(new_str)


if __name__ == "__main__":
    files = Path(".").glob("*.tif")
    for f in files:
        if not f.match(f"*{shape}"):
            # print (f"OPENING {f}")
            per_file(f)
