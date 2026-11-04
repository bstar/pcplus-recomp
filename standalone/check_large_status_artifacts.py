#!/usr/bin/env python3
"""Independent DOS status-size replies, exposed-row frames and renderer canaries.
Owned emulator evidence only; no online NAWS/BBS/physical acceptance.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--report',type=Path,action='append',required=True);p.add_argument('--renderer',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);images={};cases=[];reports={};artifacts={}
 for label in ('ordinary','25','28','43','50','legacy'):
  parent=(a.build/label).resolve();m=json.loads((parent/'manifest.json').read_text());assert sha(parent/'TERMINAL.EXE')==m['binary_sha256']
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
  images[m['binary_sha256']]=(label,m)
 for path in a.report:
  path=path.resolve();r=json.loads(path.read_text());assert r['passed'] and all(r['checks'].values());label,m=images[r['terminal_sha256']];rows=r['rows'];assert (m.get('diagnostic_session_rows_probe') or 25)==rows
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
  for n,h in r['artifacts'].items():assert sha(ROOT/n)==h,n;artifacts[n]=h
  folder=(ROOT/r['parent_result']).parent;v=json.loads((folder/'result.json').read_text());assert v['passed'] and v['binary_sha256']==r['terminal_sha256']
  assert len((folder/'BEFORE.BIN').read_bytes())==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists() and 'cputype=8086' in (folder/'dosbox.conf').read_text()
  wanted=b'\x1b[0n\x1b[1;16R\x1b[?1;2c'
  for marker,height in zip(b'abc',(rows-1,rows,rows-1)):wanted+=bytes([marker])+b'\x1b'+f'[8;{height};80t'.encode()+b'\x1b'+f'[{height};80R'.encode()
  assert (folder/'serial.bin').read_bytes()==wanted
  screen=(folder/'SCREEN.BIN').read_bytes();assert len(screen)==8000 and screen[:30:2]==b'FIRST BYTE SAFE'
  assert screen[(rows-2)*160:(rows-2)*160+14:2]==b'EXPOSED' and b'Alt-Z FOR HELP' in screen[(rows-1)*160:rows*160:2]
  frames=(folder/'PAUSE.BIN').read_bytes();size=rows*160;assert len(frames)==size*2
  for at in (0,size):assert frames[at+size-160:at+size-146:2]==b'EXPOSED'
  observer=(ROOT/'standalone/pause_watch.asm').read_text()
  for old,new in [("message: db 'Screen paused.  Press any key to continue...'","message: db 'EXPOSED'"),('mov di,(PAUSE_ROWS-1)*160+18*2','mov di,(PAUSE_ROWS-1)*160'),('mov cx,44','mov cx,7'),('cmp word [cs:pause_ticks],18','cmp word [cs:pause_ticks],1')]:assert observer.count(old)==1;observer=observer.replace(old,new)
  asm=out/(label+'.asm');exe=out/(label+'.com');asm.write_text(observer);subprocess.run(['nasm','-fbin','-DPAUSE_ROWS='+str(rows),str(asm),'-o',str(exe)],check=True);assert sha(exe)==sha(folder/'STATW.COM')
  cases.append(dict(image=label,rows=rows,area_sequence=[rows-1,rows,rows-1],exposed_frames=2,passed=True));reports[str(path.relative_to(ROOT))]=sha(path)
 assert len(cases)==6 and {c['image'] for c in cases}=={'ordinary','25','28','43','50','legacy'}
 path=a.renderer.resolve();r=json.loads(path.read_text());assert r['passed'] and len(r['cases'])==9;folder=path.parent;m=json.loads((folder/'manifest.json').read_text());assert sha(folder/'STATUS.EXE')==m['binary_sha256']==r['binary_sha256']
 for n,h in m['source_dependencies'].items():assert sha(ROOT/n)==h,n
 assert (folder/'RESULT.TXT').read_text().strip()=='PASS'
 for c in r['cases']:
  f=folder/c['name'];data=f.read_bytes();assert c['passed'] and len(data)==4004 and sha(f)==c['sha256'] and data[4000:4004]==b'\xcc'*4;artifacts[str(f.relative_to(ROOT))]=sha(f)
 normal=next(c for c in json.loads((ROOT/'standalone/fixtures/status_formatter_vectors.json').read_text())['cases'] if c['name']=='normal');text=bytes.fromhex(normal['expected_hex']);assert len(text)==81
 assert (folder/'FDX.BIN').read_bytes()[3840:4000:2]==text[:80]
 assert (folder/'HDX.BIN').read_bytes()[3840:4000:2]==text.replace(b'FDX',b'HDX')[:80]
 reports[str(path.relative_to(ROOT))]=sha(path)
 sources=['standalone/check_large_status_artifacts.py','standalone/test_status_control_dos.py','standalone/check_status_renderer.py','standalone/pause_watch.asm','standalone/fixtures/status_formatter_vectors.json']
 result=dict(passed=True,application_workflows=6,renderer_DOS_cases=9,exposed_physical_frames=12,area_reports=18,cases=cases,reports=reports,artifacts=artifacts,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Actual Ctrl-]/Alt-Z/UART/parser and physical VRAM, exact known81-byte formatter fixture clipped to80 cells and four canary bytes. Rollback faults, synthetic132-column clipping and ABI negatives remain separate CPU evidence.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS independent status captures:6 application workflows,9 renderer cases')
if __name__=='__main__':main()
