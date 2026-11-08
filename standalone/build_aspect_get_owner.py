#!/usr/bin/env python3
"""Compose recovered GET owner/readers/integer CRT with serviced source field."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--checkpoint',action='store_true');p.add_argument('--serviced',action='store_true');p.add_argument('--context',action='store_true');a=p.parse_args();assert not a.serviced or a.checkpoint;assert not a.context or a.serviced;out=a.output.resolve()
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
 features=['ASPECT_RUNTIME_SERIAL','ASPECT_GET_VM','ASPECT_GET_SERVICE','ASPECT_GET_DISPLAY','ASPECT_ALARM_SERVICE','ASPECT_EXTERNAL_RENDER','ASPECT_EXTERNAL_UNWIND','ASPECT_SNAPSHOT_LEASE','ASPECT_ALARM_VM','ASPECT_EMULATE_VM'] if a.serviced else []
 if a.context:features+=['ASPECT_GET_CONTEXT']
 if a.serviced:modules += [('native-field','src/aspect/get_native_field.asm',[]),('storage','src/aspect/get_runtime_storage.asm',[]),('platform','standalone/get_owner_platform.asm',[])]
 for name,source,flags in modules:
  subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*flags,*['-D'+n for n in features],*(['-DASPECT_GET_SERVICED'] if a.serviced else []),*(['-DASPECT_GET_CHECKPOINT'] if a.checkpoint and name=='binding' else []),str(ROOT/source),'-o',str(out/(name+'.obj'))],check=True)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-nt=GET_FIELD_CODE','-nc=FARCODE','-i='+str(ROOT/'src/aspect'),'-fo='+str(out/'field.obj'),str(ROOT/'src/aspect/get_field.c')],check=True)
 extra=[];cs=[]
 if a.serviced:
  cs=['src/aspect/get_runtime.c','src/aspect/when_runtime.c','src/aspect/resident_render.c','src/aspect/get_native_field.c','standalone/get_owner_platform.c']
  if a.context:cs+=['src/aspect/get_context.c']
  for i,n in enumerate(cs):
   obj=out/f'extra{i}.obj';rename=['-druntime_get_native_field=runtime_get_native_field_inner'] if n.endswith('get_native_field.c') else []
   subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os',*['-d'+f for f in features],*rename,'-i='+str(ROOT/'src/aspect'),'-fo='+str(obj),str(ROOT/n)],check=True);extra.append(str(obj))
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fd=GETOWNER.lnk','-fm=GETOWNER.map','-fe=GETOWNER.EXE',*(['-dASPECT_GET_CHECKPOINT'] if a.checkpoint else []),*(['-dASPECT_GET_SERVICED'] if a.serviced else []),*(['-dASPECT_GET_CONTEXT'] if a.context else []),str(ROOT/'standalone/aspect_get_owner_driver.c'),*[str(out/(n+'.obj')) for n,_,_ in modules],str(out/'field.obj'),*extra],cwd=out,check=True)
 response=out/'GETOWNER.lnk';response.write_text(response.read_text()+('\noption packcode=0\n' if a.serviced else '')+'\norder clname CODE clname PADCODE clname FARCODE'+(' clname FAR_DATA' if a.serviced else '')+' clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@GETOWNER.lnk'],cwd=out,check=True)
 if a.serviced:
  listing=(out/'GETOWNER.map').read_text();storage=[line.split() for line in listing.splitlines() if line.startswith('GET_RUNTIME_STORAGE')];group=[line.split() for line in listing.splitlines() if line.startswith('DGROUP')]
  def linear(s):a,b=s.split(':');return int(a,16)*16+int(b,16)
  assert len(storage)==1 and storage[0][1:3]==['FAR_DATA','AUTO'] and int(storage[0][-1],16)==206 and linear(storage[0][3])+206<=linear(group[0][1]),storage
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nGETOWNER >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\nexit\n:failed\necho FAIL>RESULT.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 transcript=(out/'CHECK.LOG').read_text().strip();assert (out/'RESULT.TXT').read_text().strip()=='PASS',transcript
 expected_transcript=f'PASS GET CHECKPOINT {len(v["cases"])} cases;12 injected faults/retries; recovered owner/readers/integer CRT; native abort restored DS=SS' if a.checkpoint else f'PASS GET OWNER {len(v["cases"])} cases; recovered readers/field/integer CRT; opaque float boundary; DS=SS'
 if a.serviced:expected_transcript=f'PASS SERVICED GET OWNER {len(v["cases"])} cases;137 native matches;5 protected-view refusals; actual field/WHEN/client; opaque float boundary'
 if a.context:expected_transcript='PASS CONTEXT GET OWNER 142 cases;137 native matches;1 view-rebased clip;4 protected-view refusals; shared scratch; origin52'
 assert transcript==expected_transcript,transcript
 names=[source for _,source,_ in modules]+['src/aspect/get_field.c','src/aspect/get_field.h','standalone/aspect_get_owner_driver.c','standalone/build_aspect_get_owner.py','standalone/fixtures/aspect_get_owner_native.json','reconstruction/uart/encodings.inc']
 if a.checkpoint:names+=['src/aspect/get_checkpoint.h']
 if a.serviced:names+=cs+['src/aspect/get_runtime.h','src/aspect/get_native_field.h','src/aspect/runtime.h','src/aspect/get_checkpoint.h','src/aspect/resident_render.h','src/aspect/when_runtime.h','src/aspect/serial.h','src/aspect/serial_handoff.h','src/aspect/serial_runtime.h','src/aspect/receive_runtime.h','src/aspect/alarm_cooperative.h']
 if a.context:names+=['src/aspect/get_context.h']
 result=dict(context=a.context,serviced=a.serviced,checkpoint=a.checkpoint,view_rebased_clips=1 if a.context else 0,native_matching_cases=137 if a.serviced else len(v['cases']),protected_view_refusals=4 if a.context else 5 if a.serviced else 0,injected_fault_cases=12 if a.checkpoint and not a.serviced else 0,passed=True,original_inputs=[],binary_sha256=sha(out/'GETOWNER.EXE'),cases=len(v['cases']),cpu='8086',FPU=False,data_equals_stack=True,transcript=transcript,sources={n:sha(ROOT/n) for n in names},
  scope=(('Recovered native GET/typed readers/integer CRT with actual native field ABI, editor session, WHEN gates and renderer client. Parent display, serial, BIOS keys, native WHEN and confirmation decisions modeled; observer C entry delegates unchanged native field implementation. Five explicit protected-view refusals; FLOAT.RTE opaque. Not full interpreter/live parent/UART/app integration/physical acceptance.') if a.serviced else __doc__+' Synthetic buffered stream, keyboard/display/cursor/cancel decisions and opaque float-service5. Native typed readers/global near-far copy/flush, source serviced field and native integer/long CRT. Not float mathematics, live UART, full ASPECT dispatcher, app integration or physical acceptance.'))
 if a.context:
  result['scope']='Actual checkpoint context hooks and parent anchor before recovered GET operands; scalar view/KEYS aliases, shared script-mode scratch symbol, native field/typed readers/integer CRT and serviced editor/WHEN/client.137 original matches,1 view-rebased clip,4 protected-view refusals; one-shot policy and origin52 probes. Parent, BIOS keys, serial, native WHEN actions, confirmation/final cursor/abort boundaries modeled; FLOAT.RTE opaque. Not full interpreter/real parent parser/UART/BBS/package/physical acceptance.'
  result['context_probes']=['missing policy refuses before operands','invalid policy rejected','live policy change refused','origin52 applied to cursor','old scratch alias poisoned']
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(transcript)

if __name__=='__main__':main()
