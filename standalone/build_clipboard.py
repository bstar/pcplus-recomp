#!/usr/bin/env python3
"""Build the source-owned DOS filename clipboard core and independent harness."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/clipboard';OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'src/clipboard/clipboard.c',ROOT/'src/clipboard/clipboard.h',ROOT/'standalone/clipboard_self_test.c',ROOT/'standalone/clipboard_host.asm']
objects=[]
for source in [sources[0],sources[2]]:
 obj=OUT/(source.stem+'.obj');objects.append(obj)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-i='+str(ROOT/'src/clipboard'),'-fo='+str(obj),str(source)],cwd=OUT,check=True)
host=OUT/'clipboard_host.obj';objects.insert(0,host)
subprocess.run(['nasm','-f','obj',str(sources[3]),'-o',str(host)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'clipboard.map'),'name',str(OUT/'CLIPCORE.EXE'),'file',','.join(map(str,objects)),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
sources.append(Path(__file__).resolve())
manifest=dict(kind='maintained-filename-clipboard-core',binary_sha256=hashlib.sha256((OUT/'CLIPCORE.EXE').read_bytes()).hexdigest(),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},scope='Pure bounded DOS16 filename extraction/list/packet preparation. Independent source-only diagnostic; live UI/UART/PRM binding not yet integrated.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built CLIPCORE.EXE',manifest['binary_sha256'])
