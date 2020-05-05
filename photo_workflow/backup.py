from pathlib import Path
import argparse, sys
import logging
import shutil

from .config import read_config

logging.basicConfig(level=logging.DEBUG)

def copy_projects(indir,outdir,include_tif=True):
    for p in ('panoramas',):
        for f in (indir/p).glob('**/*'):
            if not include_tif and f.suffix=='.tif':
                continue
            o = outdir/f.relative_to(indir)
            if f.is_dir() and not o.exists():
                logging.debug('create directory {}'.format(o))
                o.mkdir(parents=True)
            else:
                if not o.exists() or f.stat().st_mtime > o.stat().st_mtime:
                    logging.debug('copying file to {}'.format(o))
                    shutil.copy2(f,o)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config',help='read configuration from file')
    args = parser.parse_args()

    cfg = read_config(args.config)
    
    indir = Path(cfg['directories']['tempdir'])
    outdir =  Path(cfg['directories']['project'])
    backupdir =  Path(cfg['directories']['backedup'])

    for d in (indir,outdir,backupdir):
        if not d.is_dir():
            parser.error('no such directory {}'.format(d))
            sys.exit(1)

    copy_projects(indir,outdir)
    copy_projects(outdir,backupdir,include_tif=False)
if __name__ == '__main__':
    main()
