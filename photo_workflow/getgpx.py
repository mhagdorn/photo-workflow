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
                             

def download_gpx(dav,date,outdir):
    prefix=date.strftime('%Y-%m-%d')
    outdir = outdir/date.strftime('%Y')/prefix
    for gpx in dav.ls():
        gpx = Path(gpx.name)
        if gpx.name.startswith(prefix):
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
    args = parser.parse_args()

    date = datetime.date(args.year,args.month,args.day)

    cfg = read_config(args.config)
    outdir = Path(cfg['directories']['assets'])

    
    pw = get_password(cfg['webdav']['host'],cfg['webdav']['username'])
    webdav = easywebdav.connect(cfg['webdav']['host'],username=cfg['webdav']['username'],
                                password=pw,
                                protocol=cfg['webdav']['protocol'], port=cfg['webdav']['port'],
                                path= cfg['webdav']['basedir'])

    download_gpx(webdav,date,outdir)
    
if __name__ == '__main__':
    main()
