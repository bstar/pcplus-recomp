#!/usr/bin/env python3
"""Actual DOS/VGA composed editor load/edit/save and independent restoration."""
import argparse,ast,hashlib,json,os,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 base=json.loads((build/'result.json').read_text());assert base['passed']
 for n,h in base['sources'].items():assert sha(ROOT/n)==h
 objects=sorted(p for p in build.glob('*.obj') if p.name!='meta_editor_flow_driver.obj')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dCAPTURE_FIXED_RESERVATION','-i='+str(ROOT/'src/key_mapping'),'-fd=METAVGA.lnk','-fm=METAVGA.map','-fe=METAVGA.EXE',str(ROOT/'standalone/meta_editor_demo.c'),*[str(p) for p in objects]],cwd=out,check=True)
 response=out/'METAVGA.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@METAVGA.lnk'],cwd=out,check=True)
 listing=(out/'METAVGA.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data and null and data[1]==null[1]
 source=(ROOT/'standalone/path_editor_watch.asm').read_text();old=' cmp word [es:806],0x03b5\n jne .before\n cmp word [es:1126],0x034e\n jne .before';assert old in source
 source=source.replace(old,' cmp word [es:1010],0x7152\n jne .before\n cmp word [es:1012],0x714f\n jne .before\n cmp word [es:2450],0x1f52\n jne .before').replace('D:\\EDITVIEW.BIN','C:\\EDITVIEW.BIN')
 (out/'WATCH.ASM').write_text(source);subprocess.run(['nasm','-fbin',str(out/'WATCH.ASM'),'-o',str(out/'WATCH.COM')],check=True)
 tree=ast.parse((ROOT/'standalone/test_meta_dialog_vga.py').read_text());sampler=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sampler' for t in n.targets))
 for n in ('BEFORE','AFTER'):
  (out/(n+'.ASM')).write_text(sampler.replace('BEFORE.BIN',n+'.BIN'));subprocess.run(['nasm','-fbin',str(out/(n+'.ASM')),'-o',str(out/(n+'.COM'))],check=True)
 (out/'LAB').mkdir();original=b''.join(b'\x03\0ROW'+str(r).encode()+b'\0'+b'\xa5'*47 for r in range(10));assert len(original)==540
 for n in ('TEST.KEY','NEXT.KEY'):(out/'LAB'/n).write_bytes(original)
 (out/'CHECK.BAT').write_text('@echo off\ncls\nBEFORE\nWATCH T\nADDKEY p900 l p700 n e x t p700 enter p700 r p700 enter p700 X p700 enter p700 s p700 escape\ncd \\LAB\nC:\\METAVGA\nif errorlevel 1 goto failed\ncd \\\nAFTER\nWATCH\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\ncd \\\nWATCH\necho FAIL>C:\\FAIL.TXT\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{out}"\nc:\nCHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=30)
 assert (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),(out/'dosbox.log').read_text()[-1500:]
 assert (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes()
 raw=(out/'EDITVIEW.BIN').read_bytes();magic,count,ticks,restored=struct.unpack_from('<4H',raw);assert len(raw)==32044 and magic==0x5056 and 5<=count<=8 and restored==1
 frames=[]
 for i in range(count):
  cur,shape=struct.unpack_from('<2H',raw,8+i*4004);f=raw[12+i*4004:4012+i*4004];t=f[::2];frames.append(dict(cursor=cur,shape=shape,name=t[9*80+17:9*80+25].hex(),definition=t[505:555].hex(),file=t[4*80+15:4*80+35].hex(),sha256=hashlib.sha256(f).hexdigest()))
 checks=dict(overview=any(f['cursor']==0x110c for f in frames),name_field=any(f['cursor']==0x0911 for f in frames),typed_name=any(bytes.fromhex(f['name']).startswith(b'next') for f in frames),loaded_name=any(bytes.fromhex(f['file']).startswith(b'NEXT.KEY') for f in frames),kind=any(f['cursor']==0x0611 for f in frames),text=any(f['cursor']==0x0619 for f in frames),edited_definition=any(bytes.fromhex(f['definition']).startswith(b'XOW0') for f in frames),exact_screen_cursor_restore=True)
 expected=bytearray(original);expected[2]=ord('X');proposal=(out/'RESULT.BIN').read_bytes();assert proposal[:540]==expected and len(proposal)==668 and proposal[540:604].split(b'\0')[0]==b'NEXT.KEY' and proposal[604:].split(b'\0')[0]==b'C:\\LAB\\NEXT.KEY'
 assert (out/'LAB/NEXT.KEY').read_bytes()==expected and (out/'LAB/TEST.KEY').read_bytes()==original;checks['exact_saved_file_and_proposal']=True;assert all(checks.values()),checks
 result=dict(passed=True,checks=checks,frames=frames,cpu='8086',demo_sha256=sha(out/'METAVGA.EXE'),controller_sha256=base['binary_sha256'],sources={n:sha(ROOT/n) for n in ('standalone/test_meta_editor_vga.py','standalone/meta_editor_demo.c','standalone/path_editor_watch.asm','standalone/test_meta_dialog_vga.py')},input_objects={str(p.relative_to(ROOT)):sha(p) for p in objects},scope='Actual source-built DOS/VGA editor probe, BIOS key injection and passive timer observer over synthetic owned KEY files. Exact screen/cursor restore and load/edit/save/proposal bytes. Authored decoration, not native VGA equivalence; no terminal/UART/transient/parent/physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS composed Meta editor VGA:',checks)
if __name__=='__main__':main()
