#!/usr/bin/env python3
"""Compose real external SIP, CallSession, DSP and Telnet over loopback."""
import argparse,hashlib,json,os,re,shutil,signal,struct,subprocess,time
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from synthmodem_jitter_runtime import validate as validate_jitter
from synthmodem_lifecycle_runtime import validate as validate_lifecycle
from synthmodem_carrier_runtime import validate as validate_carrier

def telnet(wire):
 data=bytearray();sub=[];commands=[];at=0
 while at<len(wire):
  if wire[at]!=255:data.append(wire[at]);at+=1;continue
  assert at+1<len(wire)
  kind=wire[at+1];at+=2
  if kind==255:data.append(255)
  elif kind in (251,252,253,254):
   assert at<len(wire);commands.append([kind,wire[at]]);at+=1
  elif kind==250:
   payload=bytearray()
   while True:
    assert at<len(wire);v=wire[at];at+=1
    if v!=255:payload.append(v);continue
    assert at<len(wire);v=wire[at];at+=1
    if v==240:break
    assert v==255;payload.append(255)
   sub.append(bytes(payload))
  else:raise AssertionError(('Unexpected Telnet command',kind))
 return bytes(data),sub,commands

def records(wire):
 at=0;result=[]
 while at<len(wire):
  assert at+4<=len(wire);n=struct.unpack_from('<I',wire,at)[0];at+=4
  assert at+n<=len(wire);result.append(wire[at:at+n]);at+=n
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--lifecycle',action='store_true');p.add_argument('--carrier',action='store_true');p.add_argument('--dmodem',choices=['baseline','candidate'])
 a=p.parse_args();assert sum(bool(v) for v in (a.lifecycle,a.carrier,a.dmodem))<=1;runtime=a.runtime.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 names=['lab/bbs/synthmodem_gateway.py','lab/bbs/synthmodem_gateway.js','lab/bbs/synthmodem_vm_control.py','lab/bbs/synthmodem_jitter_runtime.py','lab/bbs/synthmodem_sparse_runtime.py','lab/bbs/synthmodem_lifecycle_runtime.py','nix/flake.lock','tools/modem-dev']
 if a.lifecycle or a.carrier or a.dmodem:
  inputs=validate_carrier(runtime) if a.carrier else validate_lifecycle(runtime) if a.lifecycle else validate_jitter(runtime,a.dmodem)
  tested=runtime;changed=[];names+=['docs/validation/synthmodem-gateway.json','docs/validation/synthmodem-sparse.json','docs/validation/synthmodem-jitter-policy.json']
  if a.lifecycle:names+=['docs/validation/synthmodem-pool.json','docs/validation/synthmodem-registrar.json']
  if a.carrier:names+=['lab/bbs/synthmodem_carrier_runtime.py','docs/validation/synthmodem-carrier-runtime.json','docs/validation/synthmodem-carrier-client.json','docs/validation/synthmodem-carrier-helper.json']
 else:
  ledger=ROOT/'docs/validation/synthmodem-training.json';prior=json.loads(ledger.read_text())['cohorts']['candidate'];assert prior['passed']
  reference=ROOT/'build/bbs-lab'/prior['cohort']/'runtime'
  inputs={str(runtime/Path(n).relative_to(reference)):h for n,h in prior['tested_inputs'].items()}
  assert all(sha(Path(n))==h for n,h in inputs.items()),'Runtime differs from trained candidate'
  patch=ROOT/'lab/bbs/patches/synthmodem-bind/bind.patch';names+=[str(ledger.relative_to(ROOT)),str(patch.relative_to(ROOT))]
  tested=out/'runtime';shutil.copytree(runtime/'source',tested/'source')
  for n in ('bzImage','candidate.cpio.gz'):shutil.copyfile(runtime/n,tested/n)
  subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=tested/'source',check=True)
  changed=[str(Path(n).relative_to(runtime)) for n,h in inputs.items() if sha(tested/Path(n).relative_to(runtime))!=h]
  assert sorted(changed)==['source/config.js','source/src/rtp/RtpSession.js','source/src/session/CallSession.js'],changed
 frozen={n:sha(ROOT/n) for n in names}
 tested_inputs={str(p):sha(p) for p in tested.rglob('*') if p.is_file()}
 with (out/'node.log').open('w') as log:
  proc=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_gateway.js'),str(tested),str(out)],stdout=log,stderr=log,start_new_session=True)
  try:proc.wait(timeout=210);exited_ns=time.monotonic_ns()
  except BaseException:
   try:os.killpg(proc.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:proc.wait(timeout=3)
   finally:
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   raise
 r=json.loads((out/'node-result.json').read_text());pattern=bytes(range(256))*2
 timing=json.loads((out/'cleanup-time.json').read_text());timing['actual_process_exit_lag_ms']=(exited_ns-int(timing['resources_closed_ns']))/1e6
 if a.lifecycle or a.carrier:r['checks']['warmup_timer_released']=0<=timing['before_exit_lag_ms']<2000 and 0<=timing['actual_process_exit_lag_ms']<2000
 up=b'GATEWAY-UP\r\n'+pattern+b'\r\nEND-UP\r\n';down=b'GATEWAY-DOWN\r\n'+pattern[::-1]+b'\r\nEND-DOWN\r\n'
 if r['passed']:
  decoded,subs,commands=telnet((out/'peer-0-input.bin').read_bytes())
  r['checks']['independent_Telnet_up']=decoded==up
  r['checks']['independent_TTYPE_NAWS']=b'\x18\x00ANSI' in subs and b'\x1f\x00P\x00\x19' in subs and [251,0] in commands and [253,0] in commands
  output,_,_=telnet((out/'peer-0-output.bin').read_bytes());r['checks']['independent_Telnet_down']=output==down
  second,_,_=telnet((out/'peer-1-input.bin').read_bytes());again,_,_=telnet((out/'peer-1-output.bin').read_bytes())
  r['checks']['independent_reconnect']=second==b'' and again==b'RECONNECTED\r\n'
  data=(out/'control-wire.bin').read_bytes();at=0;received=bytearray();status=[]
  while at<len(data):
   assert at+3<=len(data);size,kind=struct.unpack_from('<HB',data,at);assert 1<=size<=4094 and at+2+size<=len(data)
   payload=data[at+3:at+2+size];at+=2+size
   if kind==0x15:received.extend(payload)
   if kind==0x13:status.append(json.loads(payload))
  # Recover the online destination from the real guest stream, independent of
  # the Node runner's supplied target/config values.
  holds=re.findall(r'Post-train hold complete .*waited (\d+)ms, dropped (\d+) bytes\)',(out/'node.log').read_text())
  r['checks']['independent_post_train_hold']=len(holds)==1 and 6000<=int(holds[0][0])<=15500
  dropped=int(holds[0][1]) if len(holds)==1 else 0;r['guest_preproxy_prefix_hex']=bytes(received[:dropped]).hex();online=bytes(received[dropped:])
  destination=online.split(b'\r',1)[0]+b'\r'
  r['checks']['independent_guest_input']=destination.startswith(b'127.0.0.1:') and online==destination+up+destination+b'QUIT\r'
  r['checks']['independent_one_carrier']=sum(s.get('event')=='connect' and s.get('rate')==1200 for s in status)==1
  caller=(out/'caller-decoded.bin').read_bytes();start=caller.index(down);end=start+len(down)
  r['checks']['independent_caller_output']=caller.count(b'CONNECT> ')==3 and caller[:start].endswith(b'\r\n') and caller[start:end]==down and b'RECONNECTED\r\n' in caller[end:]
  for name in ('rtp-from-caller.bin','rtp-from-answer.bin'):
   packets=records((out/name).read_bytes());headers=[]
   for b in packets:
    assert len(b)==172 and b[0]==0x80 and b[1]&127==0;headers.append(struct.unpack_from('>HII',b,2))
   r['checks']['independent_'+name]=bool(headers) and all(seq==(headers[0][0]+i)%65536 and ts==(headers[0][1]+i*160)%2**32 and ssrc==headers[0][2] for i,(seq,ts,ssrc) in enumerate(headers))
  to_server=records((out/'sip-to-server.bin').read_bytes());to_caller=records((out/'sip-to-caller.bin').read_bytes())
  r['checks']['independent_external_SIP']=any(b.startswith(b'INVITE ') for b in to_server) and any(b.startswith(b'ACK ') for b in to_server) and any(b.startswith(b'BYE ') for b in to_caller) and any(b.startswith(b'SIP/2.0 200') and b' BYE\r\n' in b for b in to_server)
  r['checks']['independent_internal_BYE']='Response msg 200/BYE' in (out/'qemu-0.log').read_text()
 r['checks']['immutable_inputs']=all(sha(Path(n))==h for n,h in {**inputs,**tested_inputs}.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 captures={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.bin','.log')}
 r.update({'passed':proc.returncode==0 and all(r['checks'].values()),'frozen_inputs':frozen,'runtime_inputs':inputs,'tested_inputs':tested_inputs,
  'changed_runtime_files':changed,'captures_sha256':captures,'up_bytes':len(up),'down_bytes':len(down),'cleanup_timing':timing,'cleanup_timing_sha256':sha(out/'cleanup-time.json'),'lifecycle':a.lifecycle,'dmodem_variant':a.dmodem,
  'up_sha256':hashlib.sha256(up).hexdigest(),'down_sha256':hashlib.sha256(down).hexdigest(),'carrier':a.carrier})
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'checks':r['checks'],'result':str(out/'result.json')},indent=2))
 return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
