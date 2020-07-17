from pathlib import Path
import argparse, sys
import logging
import datetime
import subprocess

from .config import read_config

logging.basicConfig(level=logging.DEBUG)

def generate_tasks(indir,outdir,pattern):
    raw = ['.RW2','.nef']
    for f in indir.glob(str(pattern/'*')):
        if f.suffix in raw:
            xf = Path(str(f)+'.xmp')
            of = outdir/f.relative_to(indir).with_suffix('.jpg')
            if of.exists():
                if xf.exists() and xf.stat().st_mtime > of.stat().st_mtime:
                    yield f,of
                elif f.stat().st_mtime > of.stat().st_mtime:
                    yield f,of
            else:
                yield f,of
                
def create_jpg(infile,outfile):
    if not outfile.parent.exists():
        logging.info('create directory {}'.format(outfile.parent))
        outfile.parent.mkdir(parents=True,exist_ok=True)

    cmd = ['/usr/bin/darktable-cli','--width','2048','--height','2048',str(infile),str(outfile)]
    logging.debug('running {}'.format(' '.join(cmd)))
    try:
        output=subprocess.check_output(cmd)
    except Exception as e:
        logging.error(e)

def main():
    TODAY=datetime.datetime.now()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config',help='read configuration from file')
    parser.add_argument('-n','--num-process',type=int,default=4,help='the number of processes to use, default 4')
    parser.add_argument('-y','--year',type=int,help="process photos for YEAR")
    parser.add_argument('-m','--month',type=int,help="process photos for MONTH")
    parser.add_argument('-d','--day',type=int,help="process photos for DAY")

    args = parser.parse_args()

    cfg = read_config(args.config)

    indir = Path(cfg['directories']['assets'])
    outdir =  Path(cfg['directories']['project'])/'archive'

    if args.year is None:
        year = TODAY.year
    else:
        year = args.year
    
    if args.year is None and args.month is None and args.day is None:
        # today
        inpattern = '{}-{:02d}-{:02d}*'.format(TODAY.year,TODAY.month,TODAY.day)
    else:
        if args.month is None:
            if args.day is None:
                inpattern = '{}-*'.format(year)
            else:
                inpattern = '{}-{:02d}-{:02d}*'.format(year,TODAY.month,args.day)
        else:
            if args.day is None:
                inpattern = '{}-{:02d}-*'.format(year,args.month)
            else:
                inpattern = '{}-{:02d}-{:02d}*'.format(year,args.month,args.day)

    inpattern = Path(str(year),inpattern)


    # generate tasks
    for infile,outfile in generate_tasks(indir,outdir,inpattern):
        create_jpg(infile,outfile)


    
    
if __name__ == '__main__':
    main()
