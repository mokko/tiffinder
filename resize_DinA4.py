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
    w = im.size[0]
    h = im.size[1]
    if w > h:
        ratio = 3508 / w
    else:
        ratio = 3508 / h
    new_size = round(w * ratio), round(h * ratio)

    print(f"{f}: ({w}, {h}) -> {new_size} {ratio}")

    new = Path(f"./{f.stem}.DinA4.tif")
    if ratio < 1:  # only shrink, dont inflate
        if not new.is_file():
            print(f"\t saving {new}")
            resized = im.resize(new_size)
            resized.save(new)
