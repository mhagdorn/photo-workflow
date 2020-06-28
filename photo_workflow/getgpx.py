from pathlib import Path
import argparse, sys
import logging
import easywebdav 
import datetime
import keyring,getpass

from .config import read_config

logging.basicConfig(level=logging.INFO)

def get_password(host,user):
    pw = keyring.get_password('photo_workflow_'+host,user)
    if pw is None:
        pw = getpass.getpass('Password for {}@{}: '.format(user,host))
        keyring.set_password('photo_workflow_'+host,user,pw)
    return pw
                             

def download_gpx(dav,date,daterange,outdir,add_datedir=True):
    prefix=date.strftime('%Y-%m-%d')
    if add_datedir:
        outdir = outdir/date.strftime('%Y')/prefix
    for gpx in dav.ls():
        gpx = Path(gpx.name)
        try:
            gpx_date = datetime.datetime.strptime(gpx.name,'%Y-%m-%d_%H-%M_%a.gpx').date()
        except:
            continue
        if daterange[0] is not None:
            if gpx_date < daterange[0] or gpx_date > daterange[1]:
                continue
        else:
            if gpx_date != date:
                continue
        
        o = outdir/gpx.name
        if not o.exists():
            if not outdir.exists():
                logging.info('create directory {}'.format(outdir))
                outdir.mkdir(parents=True)
            logging.info('downloding gpx file {}'.format(o))
            dav.download(gpx.name,str(o))

def main():
    TODAY=datetime.datetime.now()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config',help='read configuration from file')
    parser.add_argument('-y','--year',type=int,default=TODAY.year,help="download data for YEAR, default={}".format(TODAY.year))
    parser.add_argument('-m','--month',type=int,default=TODAY.month,help="download data for MONTH, default={}".format(TODAY.month))
    parser.add_argument('-d','--day',type=int,default=TODAY.day,help="download data for DAY, default={}".format(TODAY.day))
    
    parser.add_argument('-o','--output-dir',metavar="DIR",help="write gpx files to DIR")
    
    parser.add_argument('-s','--start-date',metavar='YYYY-MM-DD',help='the start date from which to extract data')
    parser.add_argument('-e','--end-date',metavar='YYYY-MM-DD',help='the end date until which to extract data')
    
    args=parser.parse_args()

    date = datetime.date(args.year,args.month,args.day)

    start = None
    if args.start_date is not None:
        try:
            start = datetime.datetime.strptime(args.start_date,'%Y-%m-%d').date()
        except Exception as e:
            parser.error('Cannot parse start date: {}'.format(e))
    end = datetime.datetime.now().date()
    if args.end_date is not None:
        try:
            end = datetime.datetime.strptime(args.end_date,'%Y-%m-%d').date()
        except Exception as e:
            parser.error('Cannot parse end date: {}'.format(e))

    
    
    cfg = read_config(args.config)
    if args.output_dir is None:
        add_datedir = True
        outdir = Path(cfg['directories']['assets'])
    else:
        add_datedir = False
        outdir = Path(args.output_dir)
    
    pw = get_password(cfg['webdav']['host'],cfg['webdav']['username'])
    webdav = easywebdav.connect(cfg['webdav']['host'],username=cfg['webdav']['username'],
                                password=pw,
                                protocol=cfg['webdav']['protocol'], port=cfg['webdav']['port'],
                                path= cfg['webdav']['basedir'])

    download_gpx(webdav,date,(start,end),outdir,add_datedir=add_datedir)
    
if __name__ == '__main__':
    main()
