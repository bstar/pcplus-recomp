#!/usr/bin/env python3
"""Source-only dispatch and full VGA-frame diagnostic with original receipts."""
import argparse,ctypes,hashlib,json,os,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['src/key_mapping/keymap_screen.c','src/key_mapping/keymap_screen.h','src/key_mapping/keymap_text.c','src/key_mapping/keymap_text.h','standalone/test_keymap_screen.py','standalone/keymap_screen_driver.c','standalone/fixtures/keymap_dispatch_native.json','docs/validation/keymap-screen.json']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 fixture=json.loads((ROOT/SOURCES[-2]).read_text());reference=json.loads((ROOT/SOURCES[-1]).read_text());assert fixture['passed'] and fixture['cases']==65536 and reference['passed']
 expected=bytearray();offset=0
 for start,end,action in fixture['ranges']:
  assert start==offset and start<end<=65536;expected.extend(bytes([action])*(end-start));offset=end
 assert len(expected)==65536 and hashlib.sha256(expected).hexdigest()==fixture['sha256']
 (out/'KEYS.BIN').write_bytes(expected)
 subprocess.run(['cc','-shared','-fPIC','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-o',str(out/'screen.so'),str(ROOT/SOURCES[0]),str(ROOT/SOURCES[2])],check=True)
 lib=ctypes.CDLL(str(out/'screen.so'));lib.keymap_screen_key.argtypes=[ctypes.c_uint];lib.keymap_screen_render.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_char_p]
 for key in range(65536):assert lib.keymap_screen_key(key)==expected[key],hex(key)
 blank=bytes(948);frame=(ctypes.c_ushort*2000)();assert lib.keymap_screen_render(frame,6,blank,b'SYN.KBD')==1
 assert hashlib.sha256(bytes(frame)).hexdigest()==reference['frame_sha256'],hashlib.sha256(bytes(frame)).hexdigest()
 frames=[];profiles=[]
 lib.keymap_screen_profile.argtypes=[ctypes.c_uint];lib.keymap_screen_profile.restype=ctypes.c_char_p
 for profile in range(33):
  name=lib.keymap_screen_profile(profile);assert name and len(name)==8;profiles.append(name.decode())
  assert lib.keymap_screen_render(frame,profile,blank,b'SYN.KBD')==1;assert bytes(frame)[3840:4000:2][1:9]==name;frames.append(bytes(frame))
 assert lib.keymap_screen_profile(33) is None
 marked=bytearray(948)
 for slot in range(79):marked[slot*12:slot*12+2]=bytes([65+slot%26,0])
 assert lib.keymap_screen_render(frame,6,bytes(marked),b'SYN.KBD')==1
 for slot in range(79):
  pos=lib.keymap_screen_position(slot);at=(pos>>8)*80+(pos&255);assert frame[at]==0x1f00+65+slot%26
 before=bytes(frame);assert lib.keymap_screen_render(frame,33,blank,b'SYN.KBD')==0 and bytes(frame)==before
 marked[:12]=b'\x1e'*11+b'\0';marked[12:24]=b'\xae\0'+bytes(10);frozen=bytes(marked)
 assert lib.keymap_screen_render(frame,6,frozen,b'SYN.KBD')==1 and bytes(marked)==frozen
 pos=lib.keymap_screen_position(0);at=(pos>>8)*80+(pos&255);assert frame[at+9]==0x1f2b
 pos=lib.keymap_screen_position(1);at=(pos>>8)*80+(pos&255);assert bytes(frame)[at*2:at*2+10:2]==b'[RAW]'
 (out/'FRAMES.BIN').write_bytes(b''.join(frames));(out/'PROFILES.TXT').write_text('\n'.join(profiles)+'\n')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-i='+str(ROOT/'src/key_mapping'),'-fe=KMSCREEN.EXE',str(ROOT/'standalone/keymap_screen_driver.c'),str(ROOT/SOURCES[0]),str(ROOT/SOURCES[2])],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nKMSCREEN >RESULT.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=50)
 message=(out/'RESULT.TXT').read_text();assert 'PASS 65536 KEYS 33 VGA FRAMES' in message,message
 result=dict(passed=True,original_inputs=[],dispatch_cases=65536,profiles=33,original_blank_frame_exact=True,source_VGA_roundtrip_frames=33,slot_placement_checks=79,marked_bindings_preserved=True,source_only_DOS=True,cpu='8086',sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES},binary_sha256=hashlib.sha256((out/'KMSCREEN.EXE').read_bytes()).hexdigest(),scope='Memory-only screen/render/key dispatch; exact original blank ANSI frame, all keys and DOS VGA roundtrip. No interactive helper, saving, foreground return or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(message)
if __name__=='__main__':main()
