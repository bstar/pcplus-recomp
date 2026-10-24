#!/usr/bin/env python3
"""Build recovered reset services, optionally joined to the real viewport copy."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--viewport',action='store_true');p.add_argument('--shadow-owner',action='store_true');args=p.parse_args()
assert not args.shadow_owner or args.viewport
OUT=ROOT/('build/terminal-reset-shadow'if args.shadow_owner else'build/terminal-reset-viewport'if args.viewport else'build/terminal-reset');OUT.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/terminal_reset/provenance.json').read_text())
for unit in proof['units']:
 dest=OUT/(Path(unit['file']).stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/unit['file']),'-o',str(dest)],check=True)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==unit['sha256']
sources=[]
for module in ['screen', 'erase', 'scroll', 'text', 'cursor_shape', 'terminal_services', 'terminal_reset']:sources+=sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources+=[ROOT/'reconstruction/attributes/reset.asm',ROOT/'standalone/terminal_reset_host.asm']
if args.viewport:
 sources+=sorted((ROOT/'reconstruction/viewport').glob('*.asm'))
 sources+=[ROOT/'reconstruction/ui_windows'/n for n in ['cga_blank.asm','cga_unblank.asm']]
 sources+=[ROOT/'reconstruction/modes/width_request.asm']
if args.shadow_owner:sources+=[ROOT/'standalone/shadow_reset_bridge.asm']
objects=[]
for source in sources:
 obj=OUT/(source.parent.name+'-'+source.stem+'.obj');objects.append(obj)
 flags=['-DRESET_VIEWPORT','-DVIEWPORT_PRESERVE_DS','-DWIDTH_REQUEST_OMF']if args.viewport else[]
 if args.shadow_owner:flags+=['-DRESET_SHADOW']
 subprocess.run(['nasm','-f','obj','-D'+source.parent.name.upper()+'_OMF',*flags,'-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
if args.shadow_owner:
 c_sources=[ROOT/'src/ui/shadow_owner.c',ROOT/'standalone/shadow_reset_driver.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-dSHADOW_DIAGNOSTIC',
  '-i='+str(ROOT/'src/ui'),'-fm=terminal_reset.map','-fe=RESET.EXE',*map(str,c_sources),*map(str,objects)],cwd=OUT,check=True)
 sources+=c_sources+[ROOT/'src/ui/shadow_owner.h']
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-i='+str(ROOT/'src/ui'),
  '-fo='+str(OUT/'shadow-owner-normal.obj'),str(ROOT/'src/ui/shadow_owner.c')],cwd=OUT,check=True)
else:subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'terminal_reset.map'),'name',str(OUT/'RESET.EXE'),'file',','.join(map(str,objects))],check=True)
group=re.search(r'^DGROUP\s+[0-9a-f]+:[0-9a-f]+\s+([0-9a-f]+)',(OUT/'terminal_reset.map').read_text(),re.M|re.I)
assert group and int(group[1],16)<65536,'Diagnostic DS=SS group exceeds near segment'
inputs=sources+[ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/terminal_reset/provenance.json',Path(__file__).resolve()]
manifest={'kind':'source-only-recovered-terminal-reset-diagnostic','viewport_bound':args.viewport,'shadow_owner':args.shadow_owner,'data_stack_bytes':int(group[1],16),'binary_sha256':hashlib.sha256((OUT/'RESET.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'limitations':['Actual native soft-reset stable geometry/status-hidden path; full profile reset and broad UI have explicit boundaries.','Owned shadow variant admits foreground mode3/80-column/24-row hidden-status native layout; other variants still trap allocation.','Full parser/renderer integration remains separate.']}
if args.shadow_owner:manifest['normal_owner_object_sha256']=hashlib.sha256((OUT/'shadow-owner-normal.obj').read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',OUT/'RESET.EXE',manifest['binary_sha256'])
