from pathlib import Path
import argparse, sys
import subprocess
import logging
import re
import shutil

from .config import read_config

def get_image_tags(image):
    tags = subprocess.check_output(['exiftool','-Subject',image])
    tags = tags.split(b':')[1]
    new_tags = []
    for t in tags.split(b','):
        new_tags.append(t.strip().decode())
    return new_tags

def create_folder(indir,outprefix,glob='*.tif'):
    re_pano  = re.compile('p[0-9]{8}.*')
    re_stack = re.compile('s[0-9]{8}.*')
    for p in indir.glob(glob):
        tags = get_image_tags(p)
        if 'panorama' in tags:
            for t in tags:
                if re_pano.match(t):
                    break
            else:
                logging.warning('could not find correct panorama tag')
                continue
            outdir = outprefix/'panoramas'/t
            outdir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p),str(outdir))
        elif 'focus stack' in tags:
            for t in tags:
                if re_stack.match(t):
                    break
            else:
                logging.warning('could not find correct panorama tag')
                continue
            outdir = outprefix/'stack'/t
            outdir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p),str(outdir))
        else:
            logging.warning('unknown tags associated with image {}'.format(p))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config',help='read configuration from file')
    args = parser.parse_args()

    cfg = read_config(args.config)

    indir = Path(cfg['directories']['tempdir'])
    outprefix = Path(cfg['directories']['tempdir'])
    for d in (indir,outprefix):
        if not d.is_dir():
            parser.error('no such directory {}'.format(d))
            sys.exit(1)

    create_folder(indir,outprefix)
    
if __name__ == '__main__':
    main()
