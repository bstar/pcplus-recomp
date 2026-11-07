#!/usr/bin/env python3
"""Source-only serviced ASPECT GET field model against frozen native traces."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 fixture=ROOT/'standalone/fixtures/aspect_get_field_native.json';v=json.loads(fixture.read_text());assert v['passed'] and v['format']=='aspect-get-field-v1' and v['original_sha256']=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 with (out/'CASES.BIN').open('wb') as f:
  f.write(struct.pack('<2H',0x4746,len(v['cases'])))
  for case in v['cases']:
   f.write(struct.pack('<6H',case['width'],case['numeric'],case['masked'],case['visible'],case['shape'],case['initial'] is not None))
   initial=bytes.fromhex(case['initial'] or '')+b'\0';f.write(initial+b'\xa5'*(82-len(initial)))
   f.write(struct.pack('<H',len(case['states'])))
   for key,field,cursor,shape,visible,bells in case['states']:
    f.write(struct.pack('<H',key));f.write(bytes.fromhex(v['fields'][field]));f.write(struct.pack('<4H',cursor,shape,visible,bells))
   f.write(bytes.fromhex(case['output']));f.write(struct.pack('<4H',case['result'],case['bells'],case['final_shape'],case['final_visible']))
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-nt=GET_FIELD_CODE','-nc=FARCODE','-i='+str(ROOT/'src/aspect'),'-fo='+str(out/'model.obj'),str(ROOT/'src/aspect/get_field.c')],check=True)
 subprocess.run(['nasm','-fobj',str(ROOT/'standalone/meta_text_padding.asm'),'-o',str(out/'padding.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fd=GETFIELD.lnk','-fm=GETFIELD.map','-fe=GETFIELD.EXE',str(ROOT/'standalone/aspect_get_field_driver.c'),str(out/'padding.obj'),str(out/'model.obj')],cwd=out,check=True)
 response=out/'GETFIELD.lnk';response.write_text(response.read_text()+'\norder clname CODE clname PADCODE clname FARCODE clname DATA clname BSS clname STACK\n')
 subprocess.run(['wlink','@GETFIELD.lnk'],cwd=out,check=True)
 (out/'CHECK.BAT').write_text('@echo off\nGETFIELD >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\ngoto done\n:failed\necho FAIL>RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nCHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 text=(out/'CHECK.LOG').read_text();assert (out/'RESULT.TXT').read_text().strip()=='PASS',text
 count=sum(len(c['states']) for c in v['cases']);assert f'PASS {len(v["cases"])} cases; {count} native key states; 20 API guards; separate CS and DS=SS' in text,text
 names=['standalone/build_aspect_get_field.py','standalone/aspect_get_field_driver.c','standalone/meta_text_padding.asm','standalone/fixtures/aspect_get_field_native.json','src/aspect/get_field.c','src/aspect/get_field.h']
 result=dict(passed=True,original_inputs=[],binary_sha256=sha(out/'GETFIELD.EXE'),cases=len(v['cases']),key_states=count,API_guards=20,state_bytes=104,separate_code_segment=True,data_equals_stack=True,cpu='8086',sources={n:sha(ROOT/n) for n in names},
  scope='Actual source-built DOS8086 memory-only far GET field API against frozen original-instruction traces. Callback, string/field mutation, cursor position/shape and bell counts; peripheral UI services were modeled in the original oracle. No original executable build input, typed conversion/GET owner, runtime/compiler integration, UART, physical or application capacity acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())


if __name__=='__main__':main()
