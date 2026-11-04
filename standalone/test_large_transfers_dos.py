#!/usr/bin/env python3
"""Actual DOS X/Y/ZMODEM at selected heights, with independent BIOS row witnesses.
Owned nullmodem peers provide binary frames, queries and literal BIOS key recipes.
The passive INT10 observer chains the BIOS and never writes product state.
No modem DCD/SIP/BBS/physical acceptance is claimed by these direct-wire cases.
"""
import argparse,concurrent.futures,inspect,json,struct,subprocess,types,time
from pathlib import Path
import test_release_transfers_dos as release
from test_aspect_script_window_dos import symbols
from test_terminal_transfer_dos import Peer
ROOT=release.ROOT;sha=release.sha
def watcher(out,recipe,binary,rows):
 syms=symbols(binary.parent/'terminal.map');text=(binary.parent/'terminal.map').read_text()
 import re
 group=re.search(r'DGROUP\s+([0-9a-f]{4}):',text,re.I);assert group
 segment=syms['terminal_transfer_ui_cursor_read_site'][0]
 assert all(syms[n][0]==segment for n in ['terminal_transfer_ui_prompt_cursor_site','terminal_transfer_ui_restored_cells_site'])
 values=dict(DGROUP_REL=int(group[1],16),PROCESS_PSP=syms['process_psp'][1],UI_CS=segment,
  READ_SITE=syms['terminal_transfer_ui_cursor_read_site'][1],PROMPT_SITE=syms['terminal_transfer_ui_prompt_cursor_site'][1],
  RESTORE_SITE=syms['terminal_transfer_ui_restored_cells_site'][1],PROTOCOL=syms['terminal_transfer_protocol'][1],
  VISIBLE=syms['_terminal_transfer_ui_visible'][1],EXPECTED_PROTOCOL=recipe['protocol'],EXPECTED_ROWS=rows)
 # Bind the restore observer to the actual selected BIOS calls, not a guessed
 # function length: MOV CX,[word];MOV AH,1;INT10;MOV DX,[word];XOR BH,BH;MOV AH,2;INT10.
 image=binary.read_bytes();header=struct.unpack_from('<14H',image);at=header[4]*16+segment*16+values['RESTORE_SITE'];code=image[at:at+18]
 assert code[:2]==b'\x8b\x0e' and code[4:8]==b'\xb4\x01\xcd\x10' and code[8:10]==b'\x8b\x16' and code[12:]==b'\x30\xff\xb4\x02\xcd\x10',code.hex()
 (out/'observer-defines.json').write_text(json.dumps(values,indent=2)+'\n')
 subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in values.items()],str(ROOT/'standalone/transfer_rows_observer.asm'),'-o',str(out/'TRWATCH.COM')],check=True)
def adapter(rows):
 source=inspect.getsource(release.run_case)
 replacements={"(out / 'TEST.PRM').write_bytes(raw)":"(out / 'TEST.PRM').write_bytes(raw)\n    watcher(out,r,binary,SELECTED_ROWS)",
 'sampler = SAMPLER':"sampler = SAMPLER.replace('mov cx,4000','mov cx,8000')",
 'D:\\\\SNAP B\nADDKEY':'D:\\\\SNAP B\nD:\\\\TRWATCH T\nADDKEY',
 'D:\\\\SNAP S\nD:\\\\SNAP A':'D:\\\\SNAP S\nD:\\\\TRWATCH\nD:\\\\SNAP A',
 'cycles=fixed 6000':'cycles=fixed 12000'}
 for old,new in replacements.items():assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
 m=types.ModuleType('large_transfer_release');m.__dict__.update(release.__dict__);m.SELECTED_ROWS=rows;m.watcher=watcher
 exec(compile(source,__file__,'exec'),m.__dict__);return m
def inspect_rows(folder,recipe,rows):
 raw=(folder/'TRWATCH.BIN').read_bytes();assert len(raw)==1988,len(raw)
 magic,version,before,after,*seen=struct.unpack_from('<6H',raw)
 count=2 if recipe.get('retry_after_cancel') else 1;assert (magic,version,before,after)==(0x5254,1,count,count),(magic,version,before,after)
 records=[]
 for i in range(count):
  b=raw[12+i*334:12+(i+1)*334];a=raw[680+i*334:680+(i+1)*334];ui=raw[1348+i*320:1348+(i+1)*320]
  assert b==a,(recipe['name'],i,'exact two-row/cursor/shape/geometry restoration')
  geometry=struct.unpack_from('<7H',b,320);assert geometry[:2]==(rows,14 if rows==28 else 8 if rows in (43,50) else 16) and geometry[4:]==(3,80,0),geometry
  assert seen[i]==1 and ui[1::2]==bytes([31])*160,(recipe['name'],seen)
  protocol=['XMODEM','YMODEM','ZMODEM'][recipe['protocol']].encode();assert protocol in ui[:160:2],(protocol,ui[:160:2])
  records.append(dict(lease=i+1,rows=rows,top_row=rows-2,geometry=geometry,underlay_sha256=release.hashlib.sha256(b).hexdigest(),overlay_sha256=release.hashlib.sha256(ui).hexdigest()))
 return records
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--rows',type=int,choices=[25,28,43,50],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',action='append');p.add_argument('--jobs',type=int,choices=[1,2,3,4],default=1);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 binary=(a.build/str(a.rows)/'TERMINAL.EXE').resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert sha(binary)==manifest['binary_sha256'] and manifest['diagnostic_session_rows_probe']==a.rows and manifest['experimental_row_geometry_owner']
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 selected=[r for r in release.recipes() if not a.case or r['name'] in a.case];assert selected and (not a.case or set(a.case)=={r['name'] for r in selected})
 # The remote supplies ordinary BBS output after the actual DOS readiness DSR.
 # Its lower-row CPR independently proves parsing at the selected logical size.
 original=Peer.ready
 def ready(peer):
  original(peer);logical=a.rows-1
  peer.send(b'\x1b[2J\x1b[HBEFORE TRANSFER'+b'\x1b'+f'[{logical};1HLOWER-{a.rows}'.encode()+b'\x1b[6n\x1b[H')
  peer.log('accepted-height-banner',physical_rows=a.rows)
  reply=b'\x1b'+f'[{logical};9R'.encode();deadline=time.monotonic()+5
  while time.monotonic()<deadline:
   # Finish this explicit terminal dialogue before the independent peer starts
   # binary negotiation. Consume only known readiness/CPR replies, not frames.
   while peer.pending.startswith(b'\x1b[0n'):del peer.pending[:4]
   if peer.pending.startswith(reply):
    del peer.pending[:len(reply)];peer.log('accepted-height-CPR');break
   peer.receive()
  else:raise TimeoutError('Selected lower-row CPR did not finish before protocol')
 Peer.ready=ready;m=adapter(a.rows)
 def run(recipe):
  result=m.run_case(recipe,binary,manifest,out);folder=out/recipe['name']
  leases=inspect_rows(folder,recipe,a.rows)
  checks=dict(result['checks']);wire=(folder/'serial.bin').read_bytes();checks['selected_lower_CPR']=b'\x1b'+f'[{a.rows-1};9R'.encode() in wire
  checks['BIOS_row_leases']=bool(leases);checks['full_physical_capture']=len((folder/'SCREEN.BIN').read_bytes())==8000
  result.update(passed=all(checks.values()),checks=checks,physical_rows=a.rows,leases=leases,captures={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file() and p.name!='result.json'})
  (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(recipe['name'],'ROW PASS' if result['passed'] else 'ROW FAIL',flush=True);assert result['passed'];return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:cases=list(pool.map(run,selected))
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 names=['standalone/test_large_transfers_dos.py','standalone/transfer_rows_observer.asm','standalone/test_release_transfers_dos.py','standalone/test_terminal_transfer_dos.py','standalone/test_terminal_upload_dos.py','standalone/test_terminal_ymodem_dos.py','standalone/test_terminal_zmodem_dos.py','standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py']
 report=dict(passed=True,cases=cases,physical_rows=a.rows,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),sources={n:sha(ROOT/n) for n in names},original_inputs=[],scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
