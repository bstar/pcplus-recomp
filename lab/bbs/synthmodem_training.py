#!/usr/bin/env python3
"""Train an originating native DSP with the normal guest answering stack."""
import argparse,hashlib,json,os,shutil,signal,struct,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--v22-patch',type=Path)
 a=p.parse_args();runtime=a.runtime.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 ledger=ROOT/'docs/validation/synthmodem-runtime.json';r=json.loads(ledger.read_text())['cohorts']['auto']
 assert r['passed']
 frozen={str(ledger.relative_to(ROOT)):sha(ledger),**{n:sha(ROOT/n) for n in ['lab/bbs/synthmodem_training.py','lab/bbs/synthmodem_training.js','lab/bbs/synthmodem_vm_control.py','nix/flake.lock','tools/modem-dev']}}
 inputs={str(runtime/'source'/n):h for n,h in r['staged_source_sha256'].items()}
 inputs[str(runtime/'bzImage')]=r['media_sha256']['bzImage'];inputs[str(runtime/'candidate.cpio.gz')]=r['candidate_image_sha256']
 assert all(sha(Path(n))==h for n,h in inputs.items()),'Runtime differs from accepted normal-stack inputs'
 tested=runtime
 if a.v22_patch:
  patch=a.v22_patch.resolve();assert patch.is_relative_to(ROOT)
  frozen[str(patch.relative_to(ROOT))]=sha(patch)
  tested=out/'runtime';shutil.copytree(runtime/'source',tested/'source')
  for n in ('bzImage','candidate.cpio.gz'):shutil.copyfile(runtime/n,tested/n)
  subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=tested/'source',check=True)
  changed=[n for n,h in r['staged_source_sha256'].items() if sha(tested/'source'/n)!=h]
  assert changed==['src/dsp/protocols/V22.js'],changed
  checker=ROOT/'lab/bbs/patches/synthmodem-v22/check.js';frozen[str(checker.relative_to(ROOT))]=sha(checker)
  regression=json.loads(subprocess.check_output(['node',str(checker),str(runtime/'source'),str(tested/'source')],text=True))
 else:regression=None
 tested_inputs={str(p):sha(p) for p in tested.rglob('*') if p.is_file() and (p.is_relative_to(tested/'source') or p.name in ('bzImage','candidate.cpio.gz'))}
 with (out/'node.log').open('w') as log:
  proc=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_training.js'),str(tested),str(out)],stdout=log,stderr=log,start_new_session=True)
  try:proc.wait(timeout=145)
  except BaseException:
   try:os.killpg(proc.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:proc.wait(timeout=3)
   finally:
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   raise
 result=json.loads((out/'node-result.json').read_text())
 pattern=bytes(range(256))*4
 sent=b'PCPLUS-FROM-CALLER\r\n'+pattern+b'\r\nEND-CALLER\r\n'
 answer=b'PCPLUS-FROM-ANSWER\r\n'+pattern[::-1]+b'\r\nEND-ANSWER\r\n'
 received=(out/'answer-decoded.bin').read_bytes();caller=(out/'caller-decoded.bin').read_bytes()
 result['checks']['independent_payloads']=sent==received and answer==caller
 data=(out/'control-wire.bin').read_bytes();at=0;guest_rx=bytearray();frames=0;status=[];response=bytearray()
 while at<len(data):
  assert at+3<=len(data);size,kind=struct.unpack_from('<HB',data,at);assert 1<=size<=4094 and at+size+2<=len(data)
  if kind==0x15:guest_rx.extend(data[at+3:at+size+2])
  if kind==0x12:response.extend(data[at+3:at+size+2])
  if kind==0x13:status.append(json.loads(data[at+3:at+size+2]))
  at+=size+2;frames+=1
 result['checks']['independent_guest_DATA_RX']=sent==guest_rx
 result['checks']['independent_guest_CONNECT']=b'CONNECT 1200' in response and any(s.get('event')=='connect' and s.get('rate')==1200 for s in status)
 result['checks']['independent_BYE_response']='Response msg 200/BYE' in (out/'qemu.log').read_text()
 packet_counts={}
 for name in ('rtp-from-answer.bin','rtp-from-caller.bin'):
  b=(out/name).read_bytes();pos=0;packets=[]
  while pos<len(b):
   assert pos+4<=len(b);n=struct.unpack_from('<I',b,pos)[0];pos+=4
   assert n==172 and pos+n<=len(b);part=b[pos:pos+n];pos+=n
   assert part[0]==0x80 and part[1]&127==0;packets.append(struct.unpack_from('>HII',part,2))
  packet_counts[name]=len(packets)
  result['checks']['independent_'+name]=bool(packets) and all(seq==(packets[0][0]+i)%65536 and ts==(packets[0][1]+160*i)%2**32 and ssrc==packets[0][2] for i,(seq,ts,ssrc) in enumerate(packets))
 result['checks']['immutable_inputs']=all(sha(Path(n))==h for n,h in {**inputs,**tested_inputs}.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 result.update({'passed':proc.returncode==0 and all(result['checks'].values()),'frozen_inputs':frozen,'runtime_inputs':inputs,'tested_inputs':tested_inputs,'signal_regression':regression,
  'expected_bytes':len(sent),'expected_from_caller_sha256':hashlib.sha256(sent).hexdigest(),'expected_from_answer_sha256':hashlib.sha256(answer).hexdigest(),
  'caller_decoded_bytes':len(caller),'answer_decoded_bytes':len(received),'guest_frames':frames,'rtp_packet_counts':packet_counts,
  'captures_sha256':{n:sha(out/n) for n in ['caller-decoded.bin','answer-decoded.bin','control-wire.bin','rtp-from-answer.bin','rtp-from-caller.bin','qemu.log','node.log']}})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':result['checks'],'signal_regression':regression,'result':str(out/'result.json')},indent=2))
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
