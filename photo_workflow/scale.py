from pathlib import Path
import argparse, sys
from PIL import Image
import numpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--long-side', type=int, default=1500,
                        help="number of pixel of long side, default=1500")
    parser.add_argument('-p', '--prefix', default="small_",
                        help="add prefix to output name, default=small")
    parser.add_argument("image", nargs='+', type=Path,
                        help="image files to be processed")
    args = parser.parse_args()

    for p in args.image:
        out = p.parent / Path(args.prefix + p.name)
        image = Image.open(p)
        scale = args.long_side / max(image.size)
        if scale > 1:
            continue
        new_size = numpy.array(image.size)*scale
        new_image = image.resize(new_size.astype(int))
        new_image.save(out)


if __name__ == '__main__':
    main()
