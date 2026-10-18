#!/usr/bin/env python3
"""Live BIOS Meta PROGRAM -> real DOS child -> UART/video restoration."""
import hashlib,json,struct,subprocess
from pathlib import Path
from test_connection_dos import run,ROOT,BINARY
from modem_fixtures import fixture

def main():
 cases=[];out=ROOT/'build/program-actions-dos';out.mkdir(parents=True,exist_ok=True)
 for name,com,soft,command in [('COM1-HARD',1,0,b'D:\\CHILD.COM /OWNED'),('COM2-HARD',2,0,b'D:\\CHILD.COM /OWNED'),('COM1-SOFT',1,1,b'D:\\CHILD.COM /OWNED'),('missing-nested-command',1,0,b'D:\\MISSING.COM')]:
  child=out/(name+'.COM');base=0x2f8 if com==2 else 0x3f8;irq=0x0b if com==2 else 0x0c
  subprocess.run(['nasm','-f','bin','-DPORT='+hex(base),'-DIRQ_VECTOR='+hex(irq),str(ROOT/'standalone/program_handoff_child.asm'),'-o',str(child)],check=True)
  keys=bytearray(540)
  for i in range(10):struct.pack_into('<H',keys,i*54,3)
  struct.pack_into('<H',keys,0,1);keys[2:2+len(command)]=command
  settings=bytearray(fixture(timeout=5));struct.pack_into('<HH',settings,0x198,soft,1-soft)
  folder=ROOT/'build/connection-dos'/('program-'+name);folder.mkdir(parents=True,exist_ok=True)
  for filename in ('HANDOFF.BIN','HANDARG.BIN'):(folder/filename).unlink(missing_ok=True)
  rate=19200 if com==2 else 38400
  arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\TEST.KEY COM'+str(com)+' '+str(rate)+' '+('SOFT' if soft else 'HARD')
  proof=run('program-'+name,'success','p3000 a-1 p1800 space p1600 r e a d y p1000 a-x',prm=bytes(settings),arguments=arguments,com=com,files={'TEST.KEY':bytes(keys),'CHILD.COM':child.read_bytes()})
  wire=(folder/'serial.bin').read_bytes();before=(folder/'BEFORE.BIN').read_bytes()
  proof['checks']['normal_keys_resume']=b'ready' in wire
  proof['checks']['PROGRAM_not_sent_to_modem']=b'CHILD.COM' not in wire and b'OWNED' not in wire
  if name!='missing-nested-command':
   sample=(folder/'HANDOFF.BIN').read_bytes() if (folder/'HANDOFF.BIN').exists() else b''
   vector_offset=irq*4-0x20
   proof['checks']['child_ran_with_released_IRQ']=len(sample)==10 and sample[:4]==before[vector_offset:vector_offset+4]
   proof['checks']['child_kept_DTR_paused_RTS_and_IER']=len(sample)==10 and sample[5]==0 and sample[6]&3==1 and sample[9]&(1<<(irq-8))!=0
   proof['checks']['configured_format_inherited']=len(sample)==10 and sample[4]==3 and sample[7:9]==struct.pack('<H',115200//rate)
   tail=b' /OWNED';proof['checks']['child_exact_arguments']=(folder/'HANDARG.BIN').exists() and (folder/'HANDARG.BIN').read_bytes()==bytes([len(tail)])+tail+b'\r'
  else:proof['checks']['missing_child_not_created']=not (folder/'HANDOFF.BIN').exists()
  if soft:proof['checks']['software_peer_pause_resume']=b'\x13' in wire and b'\x11' in wire and wire.index(b'\x13')<wire.index(b'\x11')
  proof['passed']=all(proof['checks'].values());(folder/'result.json').write_text(json.dumps(proof,indent=2)+'\n');cases.append(proof);print(name,'PASS' if proof['passed'] else json.dumps(proof),flush=True)
 summary={'passed':all(c['passed'] for c in cases),'cases':cases,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'scope':'Actual DOS MetaPROGRAM COMSPEC /c with source-owned child, UARTIRQ released, DTRkept/RTSpaused/IERoff observed, childchangedUART/IRQ/video thenparentrestored, ordinarykeydelivery and finalIRQ/UART/PIC exact restoration. Nullmodem has CTSready, no physicalflow timing proof. No ASPECT/HOOK executor or vendorUI claim.'}
 (out/'checks.json').write_text(json.dumps(summary,indent=2)+'\n');return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
