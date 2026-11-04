#!/usr/bin/env python3
"""Actual DOS imported display startup, baseline/fallback and pre-enable refusal.
Owned PRM media and loopback peer; actual BIOS/keyboard/UART/parser and cleanup.
"""
import argparse,concurrent.futures,hashlib,inspect,json,re,struct,subprocess,types
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def recipes():
 cases=[dict(name=f'rows-{rows}-hidden-{hidden}',selector=2,preferred=rows,mode=0,hidden=hidden,physical=rows) for rows in (25,28,43,50) for hidden in (0,1)]
 cases += [dict(name=f'selector-{selector}-hidden-{hidden}',selector=selector,preferred=28 if selector==4 else 50,mode=3,hidden=hidden,physical=28 if selector==4 else 25) for selector in (0,3,4) for hidden in (0,1)]
 cases += [dict(name=f'fallback-{mode}-hidden-{hidden}',selector=4,preferred=50,mode=mode,hidden=hidden,physical=25) for mode in (0,0x12) for hidden in (0,1)]
 cases += [dict(name=f'invalid-{selector}',selector=selector,preferred=50,mode=3,hidden=0,physical=25,invalid=True) for selector in (5,65535)]
 cases += [dict(name='no-import',selector=2,preferred=50,mode=3,hidden=1,physical=25,no_import=True),dict(name='disabled-control',selector=2,preferred=50,mode=3,hidden=1,physical=25,disabled=True)]
 return cases
def run(binary,out,case):
 out.mkdir(parents=True,exist_ok=False);raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5)
 struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5);struct.pack_into('<HH',raw,0x4e4,8,4)
 struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
 for at,key in [(0x1c2,'hidden'),(0x1c8,'selector'),(0x1ca,'preferred'),(0x4ec,'mode')]:struct.pack_into('<H',raw,at,case[key])
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/display_startup_geometry.asm'),'-o',str(out/'GEOM.COM')],check=True)
 owned=types.ModuleType('startup_harness');owned.__dict__.update(harness.__dict__);owned.BINARY=binary
 owned.SAMPLER=harness.SAMPLER.replace('mov cx,4000','mov cx,8000');source=inspect.getsource(harness.run)
 for old,new in [('len(screen)==4000','len(screen)==8000'),('D:\\\\SNAP S','D:\\\\GEOM\nD:\\\\SNAP S')]:assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
 exec(compile(source,harness.__file__,'exec'),owned.__dict__)
 invalid=case.get('invalid',False);hidden=case['hidden'] if not case.get('no_import') and not case.get('disabled') else 0;logical=case['physical']-(not hidden)
 banner=b'' if invalid else b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c\x1b[18t\x1b[99;1HBOOT\x1b[6n\x1b[1;16H'
 response=b'\x1b[18t\x1b[99;80H\x1b[6n\x1b[1;16H'
 name=out.name;arguments=('/I:3 COM3' if case.get('no_import') else '@D:\\TEST.PRM /I:3')
 result=owned.run(name,'reject' if invalid else 'direct','p900 enter p1500 a p500 a-x',prm=bytes(raw),com=3,irq=4 if case.get('no_import') else 5,cpu='8086',working_drive='d',arguments=arguments,expected=2 if invalid else 0,banner=banner,files={'GEOM.COM':(out/'GEOM.COM').read_bytes()},online_triggers=() if invalid else ((b'a',response),),timeout=25)
 folder=ROOT/'build/connection-dos'/name;geometry=struct.unpack('<4H',(folder/'GEOM.BIN').read_bytes());wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
 physical=case['physical'];checks=dict(result['checks'],actual_BIOS_rows=geometry[0]==physical,actual_font=geometry[1]==(14 if physical==28 else 8 if physical in (43,50) else 16),mode_columns_page=(geometry[2]&255)==3 and geometry[2]>>8==80 and geometry[3]>>8==0,full_capture=len(screen)==8000)
 if invalid:checks.update(no_transmit_before_failure=wire==b'',no_query_reply=b'\x1b[' not in wire)
 else:
  wanted=b'\x1b[0n\x1b[1;16R\x1b[?1;2c'+b'\x1b'+f'[8;{logical};80t'.encode()+b'\x1b'+f'[{logical};5R'.encode()+b'a'+b'\x1b'+f'[8;{logical};80t'.encode()+b'\x1b'+f'[{logical};80R'.encode()
  checks.update(exact_runtime_queries_and_key=wire==wanted,lower_body_visible=screen[(logical-1)*160:(logical-1)*160+8:2]==b'BOOT',status_placement=(b'Alt-Z FOR HELP' in screen[(physical-1)*160:physical*160:2])==bool(not hidden))
 r=dict(passed=all(checks.values()),case=case,checks=checks,terminal_sha256=sha(binary),geometry=list(geometry),parent_result=str((folder/'result.json').relative_to(ROOT)),artifacts={str(p.relative_to(ROOT)):sha(p) for p in folder.rglob('*') if p.is_file()})
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(name,'PASS' if r['passed'] else str([n for n,v in checks.items() if not v]),flush=True);assert r['passed'];return r
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',action='append');p.add_argument('--jobs',type=int,choices=[1,2,3],default=2);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);parents={};sources={}
 for label in ('enabled','disabled'):
  binary=(a.build/label/'TERMINAL.EXE').resolve();m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_display_startup']==(label=='enabled') and sha(binary)==m['binary_sha256'];parents[label]=binary;sources.update(m['sources'])
 for name in ['standalone/test_display_startup_dos.py','standalone/display_startup_geometry.asm','standalone/test_connection_dos.py','standalone/modem_fixtures.py','standalone/test_terminal.py']:sources[name]=sha(ROOT/name)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 selected=[c for c in recipes() if not a.case or c['name'] in a.case];assert selected and (not a.case or {c['name'] for c in selected}==set(a.case))
 def one(c):return run(parents['disabled' if c.get('disabled') else 'enabled'],out/(out.name+'-'+c['name']),c)
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:cases=list(pool.map(one,selected))
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 record=dict(passed=True,cases=cases,parents={n:dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for n,p in parents.items()},sources=sources,scope=__doc__+' Actual geometry read after exit, full frame, queries from accepted startup state; invalid selectors must exit2 with no transmitted bytes and restored hardware. No live NAWS/BBS/physical acceptance.')
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
if __name__=='__main__':main()
