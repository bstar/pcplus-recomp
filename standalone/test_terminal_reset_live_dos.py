#!/usr/bin/env python3
"""Actual DOS startup capture and wire RIS restores imported state/keymap."""
import hashlib,json,struct
from test_connection_dos import run,ROOT,BINARY
from modem_fixtures import fixture
def main():
 cases=[]
 library=bytearray(7*948)
 for profile in (4,6):
  for slot,value in [(50,b'\x1b[A'),(72,b'\x1b[A'),(56,b'IMPORTED'),(76,b'IMPORTED')]:
   at=profile*948+slot*12;library[at:at+len(value)]=value
 banner=b'\x1b[2J\x1b[HDIRTY\x1b[31;1m\x1b[5;10r\x1b[?6h\x1b[?1h\x1bc\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'
 for profile,normal in [(6,7),(4,0x1e)]:
  settings=bytearray(fixture(timeout=5));struct.pack_into('<H',settings,0x194,profile);struct.pack_into('<H',settings,0x1ae,normal)
  name='RIS-profile-'+str(profile)
  proof=run(name,'success','p3000 up p120 home p120 r e a d y p500 a-x',prm=bytes(settings),profile=profile,arguments='@D:\\TEST.PRM /D:CaseTest:23 /K:D:\\TEST.KBD',files={'TEST.KBD':bytes(library)},banner=banner)
  folder=ROOT/'build/connection-dos'/name;wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
  proof['checks']['imported_map_restored_after_DECCKM']=b'\x1b[AIMPORTEDready' in wire and b'\x1bOA' not in wire
  proof['checks']['configured_normal_restored']=len(screen)==4000 and screen[1:30:2]==bytes([normal])*15
  proof['passed']=all(proof['checks'].values());(folder/'result.json').write_text(json.dumps(proof,indent=2)+'\n');cases.append(proof);print(name,'PASS' if proof['passed'] else json.dumps(proof),flush=True)
 proof={'passed':all(c['passed'] for c in cases),'cases':cases,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'scope':'Actual DOS startup configured state/KBD capture, UART ESCc after dirtySGR/scroll/origin/DECCKM, restored profileDA/CPR, configured normalcolor and exact selected imported keyslots, unchangedfiles and IRQ/UART/PIC restoration. Supported4/6 maintainedRIS policy; not nativeprofileloader/fullreset.'}
 out=ROOT/'build/terminal-reset-live-dos';out.mkdir(parents=True,exist_ok=True);(out/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
