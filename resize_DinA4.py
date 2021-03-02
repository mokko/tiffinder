"""
Shrink *.tif files proportionally so that the longest size is 3508 px.
If longest size is already smaller than 3508 px, leave it be.
DinA4 is 210 x 297 mm; at 300 dpi this makes 2480 x 3508 px.
Currently, always act on the pwd.
"""

from pathlib import Path
from PIL import Image

files = Path(".").glob("*.tif")

for f in files:
    im = Image.open(f)
    if im.width > im.height:
        ratio = 3508 / im.width
    else:
        ratio = 3508 / im.height
    new_size = round(im.width * ratio), round(im.height * ratio)
    print(f"{f}: ({im.width}, {im.height}) -> {new_size} {ratio}")

    if ratio < 1:  # only shrink, dont inflate
        new = Path(f"{f.stem}.DinA4.tif")
        if not new.is_file():
            print(f"\t saving {new}")
            resized = im.resize(new_size, resample=Image.LANCZOS).save(new)
