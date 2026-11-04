#!/usr/bin/env python3
"""Observe staged codec resize updates in the owned ENiGMA fixture before login."""
import argparse,fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
PROBE=r'''
const net=require('node:net'),assert=require('node:assert/strict');
const {TelnetCodec}=require(process.argv[1]);
const socket=net.createConnection({host:'127.0.0.1',port:23233});
const wire=[],updates=[];let phase=0,failed=false,done=false;
const codec=new TelnetCodec({terminalType:'ANSI',terminalCols:80,terminalRows:24,
 send:b=>{wire.push(Buffer.from(b));socket.write(b);},display:b=>{}});
const deadline=setTimeout(()=>{failed=true;socket.destroy(new Error('NAWS probe deadline'));},8000);
socket.on('connect',()=>codec.start());
socket.on('data',data=>{
 codec.feed(data);
 if(phase===0&&codec.local.has(31)){
  phase=1;updates.push(codec.resize(80,25));assert.deepEqual(updates[0],{changed:true,advertised:true});
  setTimeout(()=>{
   if(socket.destroyed)return;
   updates.push(codec.resize(80,24));assert.deepEqual(updates[1],{changed:true,advertised:true});phase=2;
   setTimeout(()=>socket.end(),5000);
  },100);
 }
});
socket.on('error',e=>{failed=true;process.stderr.write(e.message+'\n');});
socket.on('close',()=>{if(done)return;done=true;clearTimeout(deadline);
 if(failed||phase!==2){process.exitCode=1;return;}
 process.stdout.write(JSON.stringify({passed:true,updates,wire_hex:Buffer.concat(wire).toString('hex')})+'\n');
});
'''

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--codec',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 codec=a.codec.resolve();out=a.output.resolve();assert codec.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 lab=ROOT/'build/bbs-lab/enigma';log=lab/'source/logs/enigma-bbs.log'
 with (lab/'.dos-integration.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  start=log.stat().st_size;identity=sha(codec)
  result=subprocess.run(['node','-e',PROBE,str(codec)],capture_output=True,text=True,timeout=12)
  (out/'node.stdout').write_text(result.stdout);(out/'node.stderr').write_text(result.stderr)
  assert result.returncode==0,result.stderr
  node=json.loads(result.stdout);assert node['passed']
  deadline=time.monotonic()+2;observed=[]
  while time.monotonic()<deadline:
   with log.open('rb') as f:f.seek(start);data=f.read()
   entries=[]
   for line in data.splitlines():
    try:entries.append(json.loads(line))
    except (ValueError,UnicodeError):pass
   observed=[d for d in entries if d.get('source')=='NAWS' and d.get('msg')=='Telnet: Windows size updated']
   if len(observed)>=3:break
   time.sleep(.02)
  assert [(x['width'],x['height']) for x in observed]==[(80,24),(80,25),(80,24)],observed
  sessions={x['sessionId'] for x in observed};assert len(sessions)==1
  assert sha(codec)==identity
 source=lab/'source/core/servers/login/telnet.js'
 report=dict(passed=True,codec_sha256=identity,observed_sizes=[dict(width=x['width'],height=x['height'],sessionId=x['sessionId']) for x in observed],
  server_source_sha256=sha(source),node_output_sha256=sha(out/'node.stdout'),checker_sha256=sha(Path(__file__)),
  scope='Actual owned ENiGMA loopback Telnet connection with staged codec; server logs independently report24->25->24 and source assigns terminal dimensions for those NAWS events. No login/draft/post, DOS terminal, serial/modem/SIP/DSP/analog or dynamic editor layout acceptance; no installed bridge/config/service mutation.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS owned ENiGMA independently observed NAWS80x24 ->80x25 ->80x24 in one session')
if __name__=='__main__':main()
