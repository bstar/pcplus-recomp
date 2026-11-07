#!/usr/bin/env python3
"""Source-only field replay against frozen, synthetic original CPU traces."""
import argparse,ctypes,hashlib,json,os,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['src/key_mapping/keymap_field.c','src/key_mapping/keymap_field.h','src/key_mapping/keymap_text.c','src/key_mapping/keymap_text.h','standalone/test_keymap_field.py','standalone/keymap_field_driver.c','standalone/fixtures/keymap_field_native.json']
class State(ctypes.Structure):
 _fields_=[(n,ctypes.c_uint) for n in ('cookie','phase','cursor','insert','saved_start','saved_end')]+[('field',ctypes.c_ubyte*10)]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 fixture=json.loads((ROOT/SOURCES[-1]).read_text());assert fixture['passed'] and fixture['original_sha256']=='f079418fca6392cde318e2eb657874a1f5ee10db83616c83054d191441fb6244'
 subprocess.run(['cc','-shared','-fPIC','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-o',str(out/'field.so'),str(ROOT/SOURCES[0]),str(ROOT/SOURCES[2])],check=True)
 lib=ctypes.CDLL(str(out/'field.so'))
 lib.keymap_field_begin.argtypes=[ctypes.POINTER(State),ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint,ctypes.c_uint]
 lib.keymap_field_key.argtypes=[ctypes.POINTER(State),ctypes.c_uint]
 lib.keymap_field_shape.argtypes=[ctypes.POINTER(State)]
 lib.keymap_field_commit.argtypes=[ctypes.POINTER(State),ctypes.c_void_p,ctypes.c_uint]
 lib.keymap_text_decode.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint]
 checked=0
 with (out/'CASES.BIN').open('wb') as f:
  f.write(struct.pack('<HH',0x4b46,len(fixture['cases'])))
  for case in fixture['cases']:
   initial=bytes.fromhex(case['initial']);s=State();assert lib.keymap_field_begin(ctypes.byref(s),initial,len(initial),6,7)==0
   f.write(struct.pack('<H',len(initial))+initial.ljust(10,b'\0')+struct.pack('<H',len(case['states'])))
   bells=0
   for key,frame,cursor,shape,oldbells in case['states']:
    assert (bytes(s.field).hex(),s.cursor,lib.keymap_field_shape(ctypes.byref(s))>>8,bells)==(frame,cursor,shape,oldbells),(case['name'],key,bytes(s.field),frame,s.cursor,cursor)
    f.write(struct.pack('<H',key)+bytes.fromhex(frame)+struct.pack('<HHH',cursor,shape,oldbells))
    status=lib.keymap_field_key(ctypes.byref(s),key)
    if status==4:bells+=1
    checked+=1
   assert bells==case['bells'] and lib.keymap_field_shape(ctypes.byref(s))>>8==case['shape']
   native=bytes.fromhex(case['output']);target=ctypes.create_string_buffer(b'\xa5'*40,40);expected=ctypes.create_string_buffer(b'\xa5'*40,40)
   result=-1
   if case['result']!=65535:
    text=native.split(b'\0',1)[0]
    assert len(text)==case['result']
    result=lib.keymap_text_decode(text,len(text),expected,40)
   actual=lib.keymap_field_commit(ctypes.byref(s),target,40)
   assert actual==result and target.raw==expected.raw,(case['name'],actual,result)
   f.write(struct.pack('<HHHh',case['result'],case['bells'],case['shape'],result)+expected.raw)
   assert s.phase==(2 if case['result']==65535 else 1)
 # Bounded one-past-field mutations: original End and marker can reach width.
 for key in (65,0x5300,0x1e):
  s=State();assert lib.keymap_field_begin(ctypes.byref(s),b'ABCDEFGHIJ',10,6,7)==0
  lib.keymap_field_key(ctypes.byref(s),0x4f00);assert s.cursor==10
  before=bytes(s);assert lib.keymap_field_key(ctypes.byref(s),key)==4 and bytes(s)==before
 s=State();ctypes.memset(ctypes.byref(s),0xa5,ctypes.sizeof(s));before=bytes(s)
 assert lib.keymap_field_begin(ctypes.byref(s),b'A'*11,11,6,7)==3 and bytes(s)==before
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-i='+str(ROOT/'src/key_mapping'),'-fe=KMFIELD.EXE',str(ROOT/'standalone/keymap_field_driver.c'),str(ROOT/SOURCES[0]),str(ROOT/SOURCES[2])],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nKMFIELD >RESULT.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=25)
 message=(out/'RESULT.TXT').read_text();assert 'PASS '+str(len(fixture['cases']))+' FIELD CASES '+str(checked)+' STATES' in message,message
 result=dict(passed=True,original_inputs=[],cases=len(fixture['cases']),native_key_states=checked,cpu='8086',source_only_DOS=True,host_extra_guards=4,sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES},binary_sha256=hashlib.sha256((out/'KMFIELD.EXE').read_bytes()).hexdigest(),scope='Memory-only field/commit API, original instruction traces with modeled UI. No complete helper, actual VGA, file persistence, terminal or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(message)
if __name__=='__main__':main()
