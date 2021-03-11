"""
Convert all tif files in current directory to jpeg and shrink the jpeg to
horizontal 720px if the original is bigger than that.

"""

from pathlib import Path
from PIL import Image

def per_tif(f):
    im = Image.open(f)

    new_str = f.stem + ".jpg"

    if not Path(new_str).exists():
        if im.height > 720:
            ratio = 720 / im.height
        new_size = round(im.width * ratio), round(im.height * ratio)
    
        print(f"{f}: ({im.width}, {im.height}) -> {new_size} {ratio}")
        im.thumbnail(new_size, resample=Image.LANCZOS)
        rgb_im = im.convert('RGB')
        print(f"\t saving {new_str}")
        rgb_im.save(new_str)
    else:
        print(f"{new_str} exists already.")

if __name__ == "__main__":
    files = Path(".").glob("*.tif")
    for f in files:
        # print (f"OPENING {f}")
        per_tif(f)
