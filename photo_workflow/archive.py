from pathlib import Path
import argparse, sys
import logging
import datetime
import subprocess
import threading
from queue import Queue
import tempfile

from .config import read_config

logging.basicConfig(level=logging.DEBUG)

def generate_tasks(indir,outdir,pattern):
    raw = ['.RW2','.nef']
    for f in indir.glob(str(pattern/'*')):
        if f.suffix in raw:
            xf = Path(str(f)+'.xmp')
            of = outdir/f.relative_to(indir).with_suffix('.jpg')
            if not xf.exists():
                xf = None
            if of.exists():
                if xf is not None and xf.stat().st_mtime > of.stat().st_mtime:
                    yield f,xf,of
                elif f.stat().st_mtime > of.stat().st_mtime:
                    yield f,xf,of
            else:
                yield f,xf,of

class Worker(threading.Thread):
    def __init__(self,tasks,lock):
        super().__init__(daemon=True)
        self.tasks = tasks
        self.lock = lock
        self.cfgdir = tempfile.TemporaryDirectory()
        
    def run(self):
        while True:
            infile,xmpfile,outfile = self.tasks.get()

            if not outfile.parent.exists():
                with self.lock:
                    if not outfile.parent.exists():
                        logging.info('create directory {}'.format(outfile.parent))
                        outfile.parent.mkdir(parents=True,exist_ok=True)

            cmd = ['/usr/bin/darktable-cli','--width','2048','--height','1024',str(infile)]
            if xmpfile is not None:
                cmd.append(str(xmpfile))
            cmd.append(str(outfile))
            cmd += ['--core','--configdir',self.cfgdir.name]

            logging.info('running {}'.format(' '.join(cmd)))
            try:
                output=subprocess.check_output(cmd)
            except Exception as e:
                logging.error(e)
            self.tasks.task_done()

                
def create_jpg(infile,outfile,lock):
    if not outfile.parent.exists():
        print ('create {}'.format(outfile.parent))

    cmd = ['darktable-cli','--width',2048,'--height',1024,infile,outfile]
    print (cmd)
        
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

    lock = threading.Lock()
    tasks = Queue()

    # start workers
    workers = []
    for i in range(args.num_process):
        w = Worker(tasks,lock)
        w.start()
        workers.append(w)

    # generate tasks
    for t in generate_tasks(indir,outdir,inpattern):
        tasks.put(t)

    tasks.join()
    
    
if __name__ == '__main__':
    main()
