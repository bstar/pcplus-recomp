#!/usr/bin/env python3
"""Reproduce held N on real PTYs; stage the bounded lookahead candidate."""
import argparse,hashlib,importlib.util,json,os,pty,select,shutil,socket,struct,subprocess,time,tty
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('control_check',HERE.parent/'synthmodem-control/check.py')
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)

def sparse(exe,out,baseline):
 out.mkdir();master,slave=pty.openpty();tty.setraw(slave)
 server=socket.socket(socket.AF_UNIX);server.bind(str(out/'control.sock'));server.listen(1);server.settimeout(3)
 with (out/'helper.log').open('w') as log:
  child=subprocess.Popen([str(exe)],stdout=log,stderr=log,env=dict(os.environ,SYNTHMODEM_CONTROL_PATH=str(out/'control.sock'),SYNTHMODEM_PTY_PATH=os.ttyname(slave)))
  buf=bytearray();frames=[];rx=bytearray();checks={};latencies=[]
  try:
   conn,_=server.accept()
   with conn:
    def observe(seconds):
     end=time.monotonic()+seconds
     while time.monotonic()<end:
      if not select.select([conn],[],[],max(0,end-time.monotonic()))[0]:break
      b=conn.recv(65536);assert b;buf.extend(b)
      while len(buf)>=3:
       n,k=struct.unpack_from('<HB',buf);assert 1<=n<=4094
       if len(buf)<n+2:break
       data=bytes(buf[3:n+2]);del buf[:n+2];frames.append((k,data))
       if k==0x15:rx.extend(data)
    observe(.1);os.write(master,b'\r\nCONNECT 1200\r\n');observe(.1)
    checks['actual_CONNECT']=any(k==0x13 and b'"connect"' in b for k,b in frames)
    os.write(master,b'N');observe(.25)
    if baseline:
     checks['held_N_reproduced']=not rx
     os.write(master,b'X');observe(.15);checks['next_byte_releases_N']=rx==b'NX'
    else:
     checks['single_N_released_as_DATA_RX']=rx==b'N'
     expected=bytearray(b'N')
     for token in (b'N',b'NO',b'NO ',b'NO C',b'NO CA',b'NO CAR',b'NO CARR',b'NO CARRI',b'NO CARRIE',b'NO CARRIER'):
      start=time.monotonic();os.write(master,token);expected.extend(token)
      while len(rx)<len(expected) and time.monotonic()-start<.25:observe(.01)
      latencies.append(time.monotonic()-start)
      assert rx==expected,(token,bytes(rx),bytes(expected))
     checks['all_prefixes_released_without_followup']=True
     checks['prefixes_remain_data_mode']=not any(k==0x13 and b'nocarrier' in b for k,b in frames)
     # The same existing carrier policy still recognizes a fragmented actual
     # result line when its fragments complete within the lookahead budget.
     before_result=len(rx)
     os.write(master,b'\r\nNO CAR');observe(.01);os.write(master,b'RIER\r\n');observe(.1)
     checks['fragmented_result_still_recognized']=any(k==0x13 and b'nocarrier' in b for k,b in frames) and any(k==0x12 and b'NO CARRIER' in b for k,b in frames)
     # Explicitly retain the known data/status collision instead of claiming
     # all-byte transparency for arbitrary literal text in this mode.
     checks['legacy_literal_collision_remains']=b'NO CARRIER' not in bytes(rx[before_result:])
   child.wait(timeout=1);checks['explicit_control_EOF_exit']=child.returncode==1
  finally:
   if child.poll() is None:child.kill();child.wait()
   os.close(master);os.close(slave);server.close()
 r={'passed':all(checks.values()),'checks':checks,'release_latencies_seconds':latencies,'helper_sha256':sha(exe)}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');assert r['passed'],r;return r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 baseline=a.baseline.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 prior=json.loads((ROOT/'docs/validation/synthmodem-control-reverse.json').read_text())
 assert sha(baseline/'vm/ctrl/modemd-ctrl.c')==prior['candidate_sha256']
 inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'sparse.patch',HERE.parent/'synthmodem-control/check.py',HERE.parent/'synthmodem-control/faults.c']}
 shutil.copytree(baseline,out/'baseline');shutil.copytree(baseline,out/'candidate')
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(HERE/'sparse.patch')],cwd=out/'candidate',check=True)
 reports={};commands=[]
 for variant in ('baseline','candidate'):
  source=out/variant/'vm/ctrl';exe=out/(variant+'-helper')
  cmd=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',str(source/'modemd-ctrl.c'),'-o',str(exe)];subprocess.run(cmd,check=True);commands.append(cmd)
  reports[variant]=sparse(exe,out/(variant+'-pty'),variant=='baseline')
  fault=out/(variant+'-faults');subprocess.run(['gcc','-DFIXED','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-I'+str(source),str(HERE.parent/'synthmodem-control/faults.c'),'-o',str(fault)],check=True)
  reports[variant+'_existing_faults']=json.loads(subprocess.check_output([str(fault)],text=True))
 reports['existing_actual_PTY']=control.actual_pty(out/'candidate-helper',out/'regression-pty')
 assert all(sha(ROOT/n)==h for n,h in inputs.items())
 result={'passed':True,'reports':reports,'frozen_inputs':inputs,'baseline_source_sha256':sha(baseline/'vm/ctrl/modemd-ctrl.c'),
  'candidate_source_sha256':sha(out/'candidate/vm/ctrl/modemd-ctrl.c'),'commands':commands,
  'limits':['Literal complete NO CARRIER in data is still ambiguous under the existing in-band policy.','Host PTY only; rebuild the i386 helper and verify real DSP/DOS before claiming a workflow fix.']}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
