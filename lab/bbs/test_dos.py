#!/usr/bin/env python3
"""Exercise real loopback BBS servers through the DOS executable and modem model."""
import argparse,asyncio,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from modem import Modem
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from test_terminal import SAMPLER

async def run(args):
 binary=ROOT/'build/terminal/TERMINAL.EXE'
 digest=hashlib.sha256(binary.read_bytes()).hexdigest()
 output=ROOT/'build/bbs-lab/results'/args.name/args.label
 output.mkdir(parents=True,exist_ok=True)
 for name in ('PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN'):(output/name).unlink(missing_ok=True)
 (output/'sampler.asm').write_text(SAMPLER)
 subprocess.run(['nasm','-f','bin',str(output/'sampler.asm'),'-o',str(output/'SNAP.COM')],check=True)
 modem=Modem('127.0.0.1',args.port,output,soft=True)
 server=await asyncio.start_server(modem.accept,'127.0.0.1',0)
 port=server.sockets[0].getsockname()[1]
 keys='p1000 a t d enter '+args.keys+f' p{args.wait*1000} a-x'
 config=f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{binary.parent}"
mount d "{output}"
c:
D:\\SNAP B
ADDKEY {keys}
TERMINAL SOFT
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
D:\\SNAP S
D:\\SNAP A
exit
'''
 (output/'dosbox.conf').write_text(config)
 start=time.monotonic()
 with (output/'dosbox.log').open('w') as log:
  process=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(output/'dosbox.conf'),cwd=output,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log)
  try:code=await asyncio.wait_for(process.wait(),args.timeout)
  except asyncio.TimeoutError:process.terminate();await process.wait();code=-1
 server.close();await server.wait_closed()
 try:await asyncio.wait_for(modem.done.wait(),2)
 except asyncio.TimeoutError:pass
 modem.save()
 screen=(output/'SCREEN.BIN').read_bytes() if (output/'SCREEN.BIN').exists() else b''
 text='\n'.join(screen[row*160:row*160+160:2].decode('cp437') for row in range(25)) if len(screen)==4000 else ''
 (output/'screen.txt').write_text(text+'\n')
 before=(output/'BEFORE.BIN').read_bytes() if (output/'BEFORE.BIN').exists() else b''
 after=(output/'AFTER.BIN').read_bytes() if (output/'AFTER.BIN').exists() else b''
 checks={'dos_normal_exit':code==0 and (output/'PASS.TXT').exists(),'hardware_restored':len(before)==42 and before==after,'screen_captured':len(screen)==4000,'bbs_connected':any(e['kind']=='bbs-connected' for e in modem.events),'bbs_display_received':bool(modem.display)}
 checks['binary_unchanged_during_run']=hashlib.sha256(binary.read_bytes()).hexdigest()==digest
 result={'name':args.name,'label':args.label,'checks':checks,'passed':all(checks.values()),'seconds':round(time.monotonic()-start,3),'binary_sha256':digest,'keyboard':keys,'scope':'Actual local BBS via modeled Hayes/Telnet modem, DOSBox-X UART and source-built DOS terminal. Normal exit alone does not establish successful menu interaction.'}
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));print(text)
 return 0 if result['passed'] else 1

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('name');p.add_argument('--port',type=int,required=True);p.add_argument('--label',default='probe');p.add_argument('--keys',default='');p.add_argument('--wait',type=int,default=12);p.add_argument('--timeout',type=int,default=70)
 raise SystemExit(asyncio.run(run(p.parse_args())))
