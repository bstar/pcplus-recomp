#!/usr/bin/env python3
"""Compose recovered GET owner/readers/integer CRT with serviced source field."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--checkpoint',action='store_true');a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 fixture=ROOT/'standalone/fixtures/aspect_get_owner_native.json';v=json.loads(fixture.read_text());assert v['passed'] and v['format']=='aspect-get-owner-v1'
 with (out/'CASES.BIN').open('wb') as f:
  def words(*values):f.write(struct.pack('<'+'H'*len(values),*values))
  words(0x474f,len(v['cases']))
  for c in v['cases']:
   tail=b'\0' if c['token']<150 else struct.pack('<H',24)
   stream=bytes([c['token']])+tail+(b'\0' if c['width'] is None else b'\1\xab'+struct.pack('<H',c['width']&65535))
   words(c['token'],c['row'],c['column'],c['wrap'],c['keys_disabled'],c['confirm'],len(stream));f.write(stream)
   words(len(c['keys']),*c['keys']);before=bytes.fromhex(c['before']);words(len(before));f.write(before);f.write(bytes.fromhex(c['output']))
   fields=[e for e in c['events'] if e[0]=='field'];positions=[e for e in c['events'] if e[0]=='cursor'];floats=[e for e in c['events'] if e[0]=='float-service']
   words(c['native_error'] or 0,c['returned'],c['comparison'],c['field_calls'],fields[0][3] if fields else 0,c['token']%10!=0,c['bells'],len(positions),(positions[0][1]<<8)|positions[0][2] if positions else 0,sum(e[0]=='confirm' for e in c['events']),sum(e[0]=='cancel-dispatch' for e in c['events']),len(floats))
   text=bytes.fromhex(floats[0][2]) if floats else b'';words(len(text));f.write(text)
 modules=[('get','src/aspect/get_native.asm',[]),('operands','src/aspect/numeric_operands.asm',[]),('expr','src/aspect/expression_support.asm',[]),('strings','src/aspect/string_operands.asm',[]),('crt','src/aspect/conversion_services.asm',[]),('copy','reconstruction/erase/move_bytes.asm',['-DERASE_OMF']),('binding','standalone/aspect_get_owner_bindings.asm',[]),('padding','standalone/meta_text_padding.asm',[])]
 if a.checkpoint:modules += [('checkpoint','src/aspect/get_checkpoint.asm',[])]
 for name,source,flags in modules:
  subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*flags,*(['-DASPECT_GET_CHECKPOINT'] if a.checkpoint and name=='binding' else []),str(ROOT/source),'-o',str(out/(name+'.obj'))],check=True)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-nt=GET_FIELD_CODE','-nc=FARCODE','-i='+str(ROOT/'src/aspect'),'-fo='+str(out/'field.obj'),str(ROOT/'src/aspect/get_field.c')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fd=GETOWNER.lnk','-fm=GETOWNER.map','-fe=GETOWNER.EXE',*(['-dASPECT_GET_CHECKPOINT'] if a.checkpoint else []),str(ROOT/'standalone/aspect_get_owner_driver.c'),*[str(out/(n+'.obj')) for n,_,_ in modules],str(out/'field.obj')],cwd=out,check=True)
 response=out/'GETOWNER.lnk';response.write_text(response.read_text()+'\norder clname CODE clname PADCODE clname FARCODE clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@GETOWNER.lnk'],cwd=out,check=True)
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nGETOWNER >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\nexit\n:failed\necho FAIL>RESULT.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 transcript=(out/'CHECK.LOG').read_text().strip();assert (out/'RESULT.TXT').read_text().strip()=='PASS',transcript
 expected_transcript=f'PASS GET CHECKPOINT {len(v["cases"])} cases;12 injected faults/retries; recovered owner/readers/integer CRT; native abort restored DS=SS' if a.checkpoint else f'PASS GET OWNER {len(v["cases"])} cases; recovered readers/field/integer CRT; opaque float boundary; DS=SS'
 assert transcript==expected_transcript,transcript
 names=[source for _,source,_ in modules]+['src/aspect/get_field.c','src/aspect/get_field.h','standalone/aspect_get_owner_driver.c','standalone/build_aspect_get_owner.py','standalone/fixtures/aspect_get_owner_native.json','reconstruction/uart/encodings.inc']
 if a.checkpoint:names+=['src/aspect/get_checkpoint.h']
 result=dict(checkpoint=a.checkpoint,injected_fault_cases=12 if a.checkpoint else 0,passed=True,original_inputs=[],binary_sha256=sha(out/'GETOWNER.EXE'),cases=len(v['cases']),cpu='8086',data_equals_stack=True,transcript=transcript,sources={n:sha(ROOT/n) for n in names},
  scope=__doc__+' Synthetic buffered stream, keyboard/display/cursor/cancel decisions and opaque float-service5. Native typed readers/global near-far copy/flush, source serviced field and native integer/long CRT. Not float mathematics, live UART, full ASPECT dispatcher, app integration or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(transcript)

if __name__=='__main__':main()
