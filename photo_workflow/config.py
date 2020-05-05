__all__ = ['read_config']

import configparser
import sys
from pathlib import Path

def read_config(cname):
    if cname is None:
        cname = Path.home()/'.photo-workflow.cfg'
    config = configparser.ConfigParser()
    config.read(cname)
    cfg = {}
    for s in config.sections():
        sec = {}
        for o in config.options(s):
            sec[o] = config.get(s,o)
        cfg[s] = sec
    return cfg

if __name__ == '__main__':
    from pprint import pprint
    if len(sys.argv)>1:
        cname = sys.argv[1]
    else:
        cname = None
    cfg = read_config(cname)

    pprint(cfg)
