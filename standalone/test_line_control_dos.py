#!/usr/bin/env python3
"""Actual DOS Ctrl-minus/reference/browser cycles and tracked-online refusal.
Owned serial peers and passive timer/BDA/tail-row witness; no product mutation.
"""
import argparse,concurrent.futures,hashlib,inspect,json,struct,subprocess,types
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def recipes():
 r=[dict(name=f'rows-{rows}-mode-{mode}-hidden-{hidden}',preferred=rows,mode=mode,hidden=hidden,initial=1,heights=([25,rows,25] if not mode else [25,rows,25,rows,25])) for rows in (28,43,50) for mode in (0,3) for hidden in (0,1)]
 r += [dict(name='graphics-fallback-next-key',preferred=43,mode=18,hidden=0,initial=1,heights=[25,43,25,43]),dict(name='tracked-online-refusal',preferred=43,mode=0,hidden=0,initial=2,heights=[43,43],online=True),dict(name='missing-import-refusal',preferred=50,mode=3,hidden=0,initial=1,heights=[25,25],no_import=True)]
 return r
def run(binary,out,c):
 out.mkdir(parents=True,exist_ok=False);count=len(c['heights']);mask=(1<<count)-1
 subprocess.run(['nasm','-fbin','-DEXPECTED_MASK='+str(mask),str(ROOT/'standalone/line_control_watch.asm'),'-o',str(out/'LINEW.COM')],check=True)
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/display_startup_geometry.asm'),'-o',str(out/'GEOM.COM')],check=True)
 raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5);struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
 for at,key in [(0x1c2,'hidden'),(0x1c8,'initial'),(0x1ca,'preferred'),(0x4ec,'mode')]:struct.pack_into('<H',raw,at,c[key])
 owned=types.ModuleType('line_harness');owned.__dict__.update(harness.__dict__);owned.BINARY=binary;owned.SAMPLER=harness.SAMPLER.replace('mov cx,4000','mov cx,8000')
 source=inspect.getsource(harness.run)
 for old,new in [('len(screen)==4000','len(screen)==8000'),('D:\\\\SNAP S','D:\\\\GEOM\nD:\\\\SNAP S'),('cycles=fixed 6000','cycles=fixed 12000')]:assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
 exec(compile(source,harness.__file__,'exec'),owned.__dict__)
 prefix='p900 enter p5000 ' if c.get('online') else 'p900 enter p1600 ';keys=prefix+'a'
 actions=['c--','a-z p150 c--','a-z p150 ` right right l','c--']
 if c['name']=='graphics-fallback-next-key':actions[2]='c--'
 for i in range(1,count):keys+=' p450 '+actions[i-1]+' p650 '+chr(97+i)
 keys+=' p500 a-x';triggers=[]
 for i in range(count):
  marker=f'LC-{chr(65+i)}'.encode();tag=f'STEP-{chr(65+i)}'.encode()
  response=b'\x1b[18t\x1b[99;80H\x1b[6n\x1b[99;1H'+tag+b'\x1b[1;1HFIRST BYTE SAFE\x1b[1;70H'+marker+b'\x1b[1;16H'
  triggers.append((bytes([97+i]),response))
 args='/I:3 COM3' if c.get('no_import') else '@D:\\TEST.PRM /I:3'+(' /D:CaseTest:23' if c.get('online') else '')
 result=owned.run(out.name,'success' if c.get('online') else 'direct',keys,prm=bytes(raw),com=3,irq=4 if c.get('no_import') else 5,cpu='8086',working_drive='d',arguments=args,timeout=35,files={n:(out/n).read_bytes() for n in ('LINEW.COM','GEOM.COM')},observer='LINEW',online_triggers=tuple(triggers))
 folder=ROOT/'build/connection-dos'/out.name;wire=(folder/'serial.bin').read_bytes();samples=(folder/'LINES.BIN').read_bytes();assert len(samples)==1676
 checks=dict(result['checks'],all_timer_stages=struct.unpack_from('<3H',samples)==(0x4c43,1,mask));stages=[]
 for i,physical in enumerate(c['heights']):
  rows,font,cursor,shape,mode,cols,page=struct.unpack_from('<7H',samples,6+i*334);tail=samples[20+i*334:340+i*334];logical=physical-(not c['hidden']);tag=f'STEP-{chr(65+i)}'.encode();at=160 if c['hidden'] else 0
  # Selector3 uses configured AH=0 mode without forcing 400 scanlines.
  # After preferred43 (350 scanlines), mode3 has its native14-pixel font.
  expected_font=14 if physical==28 or (i==2 and c['mode']==3 and c['preferred']==43) else 8 if physical in (43,50) else 16
  ok=(rows,font,mode,cols,page)==(physical,expected_font,3,80,0) and tail[at:at+12:2]==tag
  checks['stage_'+str(i)]=ok;stages.append(dict(rows=rows,font=font,cursor=cursor,shape=shape,logical_rows=logical,passed=ok))
 prefix=b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?1;2c' if c.get('online') else b'\x1b[0n\x1b[1;16R\x1b[?1;2c'
 wanted=prefix
 for i,physical in enumerate(c['heights']):
  logical=physical-(not c['hidden']);wanted+=bytes([97+i])+b'\x1b'+f'[8;{logical};80t'.encode()+b'\x1b'+f'[{logical};80R'.encode()
 if c.get('online'):wanted+=b'+++ATH\r'
 checks.update(exact_wire_queries_and_local_keys=wire==wanted,unchanged_PRM=(folder/'TEST.PRM').read_bytes()==raw,actual_final_BIOS=struct.unpack('<4H',(folder/'GEOM.BIN').read_bytes())[:2]==(c['heights'][-1],14 if c['heights'][-1]==28 else 8 if c['heights'][-1] in (43,50) else 16))
 r=dict(passed=all(checks.values()),case=c,checks=checks,stages=stages,terminal_sha256=sha(binary),parent_result=str((folder/'result.json').relative_to(ROOT)),artifacts={str(p.relative_to(ROOT)):sha(p) for p in folder.rglob('*') if p.is_file()})
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(out.name,'FINAL PASS' if r['passed'] else str([n for n,v in checks.items() if not v]),flush=True);assert r['passed'];return r
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',action='append');p.add_argument('--jobs',type=int,choices=[1,2,3],default=2);a=p.parse_args()
 binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_line_control'] and sha(binary)==m['binary_sha256'];out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 sources=dict(m['sources'])
 for n in ['standalone/test_line_control_dos.py','standalone/line_control_watch.asm','standalone/display_startup_geometry.asm','standalone/test_connection_dos.py','standalone/modem_fixtures.py','standalone/test_terminal.py']:sources[n]=sha(ROOT/n)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 selected=[c for c in recipes() if not a.case or c['name'] in a.case];assert selected and (not a.case or {c['name'] for c in selected}==set(a.case))
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:cases=list(pool.map(lambda c:run(binary,out/(out.name+'-'+c['name']),c),selected))
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 r=dict(passed=True,cases=cases,terminal_path=str(binary.relative_to(ROOT)),terminal_sha256=sha(binary),sources=sources,scope=__doc__+' Real BIOS keyboard via ADDKEY, selector/font calls and physical VRAM tails; tracked connection uses synthetic Hayes replies, not real SIP/DCD. No physical/BBS/live NAWS claim.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()
