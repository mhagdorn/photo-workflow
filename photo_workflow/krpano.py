__all__ = ["KRPano"]

import argparse, sys, os
import logging
import yaml
import shutil
from pathlib import Path
import subprocess
import xml.etree.ElementTree
import pkg_resources
from jinja2 import Template
from .config import read_config

template = Template("""
<!DOCTYPE html>
<html>
<head>
        <title>{{ title }}</title>
        <meta name="description" content="{{ description }}" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, viewport-fit=cover" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
        <meta http-equiv="x-ua-compatible" content="IE=edge" />
        <style>
                html { height:100%; }
                body { height:100%; overflow:hidden; margin:0; padding:0; font-family:Arial, Helvetica, sans-serif; font-size:16px; color:#FFFFFF; background-color:#000000; }
        </style>
</head>
<body>

<script src="krpano.js"></script>

<div id="pano" style="width:100%;height:100%;">
        <noscript><table style="width:100%;height:100%;"><tr style="vertical-align:middle;"><td><div style="text-align:center;">ERROR:<br/><br/>Javascript not activated<br/><br/></div></td></tr></table></noscript>
        <script>
                embedpano({xml:"{{ pname }}.xml", target:"pano", html5:"only", mobilescale:1.0, passQueryParameters:true});
        </script>
</div>

</body>
</html>
""")

class KRPanoBase:
    def __init__(self,krpanotools):
        self._krpanotools = Path(krpanotools)
    @property
    def krpanotools(self):
        return self._krpanotools

    def run(self,cmd,args):
        cmd =  [str(self.krpanotools),cmd] + args
        logging.debug('running command: '+' '.join(cmd))

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            msg = []
            for l in result.stdout.split(b'\n'):
                if len(l) > 0:
                    msg.append(l)
            raise RuntimeError(b' '.join(msg).decode())
        else:
            for l in result.stdout.split(b'\n'):
                if len(l)>0:
                    logging.debug(l.decode())

class KRViewer(KRPanoBase):
    def run(self,viewer,domains):
        if not viewer.parent.exists():
            viewer.parent.mkdir(parents=True)
        krpano_args = ["-noep", "-nolu", "-noex"]
        for d in domains:
            krpano_args.append(f"-domain={d}")
        krpano_args.append(f"-o={viewer}")
        super().run('protect', krpano_args)

class KRPano(KRPanoBase):
    def __init__(self,krpanotools, panoramas, template):
        super().__init__(krpanotools)
        self._panoramas = Path(panoramas)
        self._template = Path(template)

    @property
    def template(self):
        if self._template.exists():
            return self._template
        else:
            return Path(self.krpanotools.parent,'templates',self._template)
        
    def pname(self,fname):
        fname = Path(fname)
        if fname.is_file():
            pname = fname
        else:
            pname = self._panoramas/fname
            if not pname.is_file():
                raise RuntimeError(f'no such file {fname} or {pname}')
        return pname

    def add_data(self,dfile,outdir):
        oc = outdir/dfile
        ic = Path(pkg_resources.resource_filename('photo_workflow',
                                                  'data/'+dfile))
        if not outdir.exists():
            outdir.mkdir(parents=True)
        if not oc.exists():
            logging.debug(f'copying data file {ic} to {oc}')
            shutil.copy(ic,oc)

    def html(self,pano,template,outdir):
        pass

    def hotspots(self,pano,outdir):
        if not outdir.exists():
            outdir.mkdir(parents=True)

        self.add_data('hs_circle.png',outdir)
        self.add_data('showtext.xml',outdir/'plugins')
        if 'hotspots' in pano:
            with open(outdir/Path(pano['pname']+'_hotspots.xml'),'w') as hotspots:
                hotspots.write("""<krpano>
  <include url="%VIEWER%/plugins/showtext.xml" />
  <style name="letter"
               capture="false" handcursor="false"
               fillcolor="0xffff00" fillalpha="0.30"
               bordercolor="0xffff00" borderalpha="0.80"
               onover="tween(alpha, 0.1, 0.25);"
               onout="tween(alpha, 1.0, 0.25);"
               ondown.touch="onover(); asyncloop(pressed, onhover(); );"
               onup.touch="onout();"
               />
  <textstyle name="STYLE7"
             font="Arial" fontsize="14" padding="4" bold="false"
             edge="left" textalign="left" xoffset="15" yoffset="0"
             />
	<style name="button_style"
               type="text"
               bgcolor="0x000000"
               bgalpha="0.5"
               bgroundedge="0"
               css="calc:'color:#FFFFFF;font-size:' + 20 + 'px;'"
               padding="calc:6 + ' ' + 10"
               />

	<layer name="hotspots" style="button_style" html="Toggle Hotspots"     align="lefttop" y="10" x="10"   onclick="toggle_hotspots();"     />

	<action name="toggle_hotspots">
          for(set(i,0), i LT hotspot.count, inc(i),
	  if (hotspot[get(i)].alpha == 0,
	  set(hotspot[get(i)].alpha ,1);,
	  set(hotspot[get(i)].alpha ,0););
          );
        </action>
""")
                for nspot,h in enumerate(pano["hotspots"]):
                    hotspots.write(f'''  <hotspot name="spot{nspot}" style="letter" type="image" url="hs_circle.png"
           scale="0.3" ath="{h['ath']}" atv="{h['atv']}"
           onhover="showtext({h['description']}, STYLE7);"/>
''')
                hotspots.write('</krpano>')

    def run(self,pano,outdir, debug=False, html=False):
        inpano = self.pname(pano['input'])
        logging.debug(f'input panorama: {inpano}')
        outxml = outdir/Path(pano['pname']+'.xml')
        logging.debug(f'output xml: {outxml}')

        if not outdir.exists():
            outdir.mkdir(parents=True)

        # handle preview
        if 'preview' in pano and len(pano['preview']) > 0:
            inpreview = self.pname(pano['preview'])
            outpreview = outdir/Path(pano['pname']+'_small.jpg')

            if not outpreview.exists() or \
               inpreview.stat().st_ctime > outpreview.stat().st_ctime:
                logging.debug(f'copying preview {inpreview} to {outpreview}')
                shutil.copy(inpreview,outpreview)

        # handle twitter card
        if 'twittercard' in pano and len(pano['twittercard'])>0:
            intc = self.pname(pano['twittercard'])
            outtc = outdir/Path(pano['pname']+'_tc.jpg')
    
            if not outtc.exists() or \
               intc.stat().st_ctime > outtc.stat().st_ctime:
                logging.debug(f'copying twittercard {intc} to {outtc}')
                shutil.copy(intc,outtc)

        # check output xml
        if outxml.is_file():
            if inpano.stat().st_ctime > outxml.stat().st_ctime:
                logging.debug(f'removing {outxml} as input is newer')
                outxml.unlink()
            else:
                logging.debug('nothing to do')
                return

        # setup krpano arguments
        krpano_args = [
            f"-panotype={pano['panotype']}",
            f"-hfov={pano['hfov']}",
            "-flash=false",
            f"-tilepath={outdir}/{pano['pname']}.tiles/[mres_c/]l%Al/%Av/l%Al[_c]_%Av_%Ah.jpg",
            f"-xmlpath={outxml}",
            f"-previewpath={outdir}/{pano['pname']}.tiles/preview.jpg",
            f"-customimage[mobile].path={outdir}/{pano['pname']}.tiles/mobile_%s.jpg",
            f"-config={self.template}",
            f"-thumbpath={outdir}/{pano['pname']}.tiles/thumb.jpg",
        ]

        if html:
            krpano_args.append("-html=true")
            krpano_args.append(f"-htmlpath={outdir}/{pano['pname']}.html")
        else:
            krpano_args.append("-html=false")
            
        for o in ['vfov','voffset']:
            if o in pano and pano[o] != '':
                krpano_args.append(f"-{o}={pano[o]}") 

        # run krpano
        super().run('makepano',krpano_args + [str(inpano)])

        et = xml.etree.ElementTree.parse(outxml)
        root = et.getroot()
        view=root.find('view')
        if view is not None:
            for o in ['hlookat','vlookat','fov']:
                if o in pano and pano[o] != '':
                    view.attrib[o] = str(pano[o])
        if 'hotspots' in pano:
            self.hotspots(pano,outdir)
            include = xml.etree.ElementTree.SubElement(et.getroot(), 'include')
            include.attrib['url'] = pano['pname']+'_hotspots.xml'
        if debug:
            events = xml.etree.ElementTree.SubElement(et.getroot(), 'events')
            events.attrib['onviewchange'] = "showlog(true);trace('hlookat ',view.hlookat);trace('vlookat ',view.vlookat);trace('fov ',view.fov);"

            include = xml.etree.ElementTree.SubElement(et.getroot(), 'include')
            include.attrib['url'] = "partialpano_helpertool.xml"
            self.add_data("partialpano_helpertool.xml",outdir)

            for t in ['grid.xml','polygonalhotspot_editor.xml','stickie_data.xml',
                      'stickies.xml','numbers.xml','scrollingtext.xml','stickie_engine.xml',
                      'toolbox.xml','distortedhotspot_editor.xml']:
                self.add_data(t,outdir/'plugins')
            toolbox = xml.etree.ElementTree.SubElement(et.getroot(), 'include')
            toolbox.attrib['url'] = "plugins/toolbox.xml"

        et.write(outxml)
            
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs='?',
                        metavar="FILE",help="name of input file")
    parser.add_argument('-c','--config',help='read configuration from file')
    parser.add_argument('-d','--debug',action="store_true",default=False,
                        help="add debug functionality to panorama")
    parser.add_argument('-D','--domain',action='append',
                        help="generate viewer for domains, multiple domains can be specified")
    parser.add_argument('--js-name',default='krpano.js',
                        help='name of krpano javascript name, default: krpano.js')
    parser.add_argument('-H','--html',action="store_true",default=False,
                        help="generate html file")
    parser.add_argument('-s','--hotspots',action="store_true",default=False,
                        help="generate hotspots file only"),
    parser.add_argument("-o","--output-dir",metavar="DIR",
                        default="panoramas",type=Path,
                        help="name of output base directory")
    args = parser.parse_args()
    
    cfg = read_config(args.config)

    if args.debug:
        level=logging.DEBUG
    else:
        level=logging.INFO
    logging.basicConfig(level=level)
    
    krpano = KRPano(cfg['krpano']['tools'],cfg['directories']['panoramas'],
                    cfg['krpano']['template'])

    if args.domain is not None:
        krviewer = KRViewer(cfg['krpano']['tools'])
        krviewer.run(args.output_dir/args.js_name,args.domain)
    else:
        if args.input is None:
            parser.error('no input specified')
    
        pano = yaml.load(open(args.input,'r'), Loader=yaml.CLoader)

    
        if args.hotspots:
            krpano.hotspots(pano,args.output_dir)
        else:
            krpano.run(pano,args.output_dir, debug=args.debug)

        if args.html:
            with open(args.output_dir/(pano['pname']+'.html'),'w') as out:
                out.write(template.render(**pano))
            
if __name__ == '__main__':
    main()
