from pathlib import Path
import argparse, sys
import subprocess
import logging
import re
import shutil

def get_image_tags(image):
    tags = subprocess.check_output(['exiftool','-Subject',image])
    tags = tags.split(b':')[1]
    new_tags = []
    for t in tags.split(b','):
        new_tags.append(t.strip().decode())
    return new_tags

def create_folder(indir,outprefix,glob='*.tif'):
    re_pano = re.compile('p[0-9]{8}.*')
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
        else:
            logging.warning('unknown tags associated with image {}'.format(p))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input-directory',default='/tmp',help='input directory to be searched for photos')
    parser.add_argument('-o','--output-prefix',default='/tmp',help='where to create the output directory')
    args = parser.parse_args()

    indir = Path(args.input_directory)
    outprefix = Path(args.output_prefix)
    for d in (indir,outprefix):
        if not d.is_dir():
            parser.error('no such directory {}'.format(d))
            sys.exit(1)

    create_folder(indir,outprefix)
    
if __name__ == '__main__':
    main()
