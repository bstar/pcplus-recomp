#!/usr/bin/env python3
"""Bind a controlled parser-refusal reproduction and its maintained correction."""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from menu_guard_probe import FIELDS
BASELINE='ebe18b1c8c3b23acd656e419500522fa2b1dbad6'

def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def sources(report):
 for name,value in report.get('sources',{}).items():assert sha(name)==value,name
def decode(folder,report,manifest):
 raw=(ROOT/folder/'MGUARD.BIN').read_bytes();magic,version,size,n,count,overflow=struct.unpack_from('<6H',raw)
 assert magic==0x474d and version==1 and n==len(FIELDS) and size==16+n*2+8+240
 assert len(raw)==12+32*size and 0<count<=32 and overflow==0
 rows=[]
 for i in range(count):
  at=12+i*size;key,lo,hi,ip,cs,ds,ss,bp=struct.unpack_from('<8H',raw,at)
  assert ds==ss and cs+manifest['memory_layout']['near_relative_segment']==ds
  guards=dict(zip(FIELDS,struct.unpack_from('<'+str(n)+'H',raw,at+16)))
  mode,cols,page,last=struct.unpack_from('<4H',raw,at+16+n*2);assert (mode,cols,page,last)==(3,80,0,24)
  chars=at+16+n*2+8
  rows.append(dict(key=key,ticks=hi*65536+lo,guards=guards,
   title=raw[chars:chars+80].decode('cp437'),header=raw[chars+80:chars+160].decode('cp437')))
 assert rows==report['records']
 opening=[row for row in rows if row['key']==0x2c00];assert len(opening)==1
 flags=opening[0]['guards'];assert flags['terminal_parser_active']==1
 for name in FIELDS[1:13]:assert flags[name]==0,name
 assert flags['text_video_segment']==0xb800 and flags['screen_attribute_row_bytes']==80 and flags['screen_video_row_bytes']==160
 assert flags['connection_state']==6 and flags['_redisplay_active']==flags['_command_menu_active']==0
 assert flags['terminal_history_end']-flags['terminal_history_start']==63000 and flags['terminal_history_start']<=flags['terminal_history_pointer']<flags['terminal_history_end']
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',required=True);p.add_argument('--after',required=True);a=p.parse_args()
 for label in (a.before,a.after):assert label and all(c.isalnum() or c in '-_' for c in label)
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json');assert manifest['binary_sha256']==runtime;sources(manifest)
 old=read('build/checkpoints/c0d6/manifest.json');assert old['binary_sha256']==sha('build/checkpoints/c0d6/TERMINAL.EXE')
 # Authenticate the old compiled inputs against the committed source, not the
 # edited current tree. Old probe/observer adapters are retained separately.
 for name,value in old['sources'].items():
  data=subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)
  assert hashlib.sha256(data).hexdigest()==value,name
 artifacts=[Path('build/checkpoints/c0d6')/name for name in ('manifest.json','TERMINAL.EXE','terminal.map')]
 samples={}
 for kind,label,identity,map_path in [('before',a.before,old,Path('build/checkpoints/c0d6/terminal.map')),('after',a.after,manifest,Path('build/terminal/terminal.map'))]:
  out=Path('build/menu-parser-probe')/label;report=read(out/'result.json');assert report['reproduced'] and all(report['checks'].values())
  assert report['binary_sha256']==identity['binary_sha256']
  assert report.get('expected_behavior','refused')==('refused' if kind=='before' else 'deferred')
  folder=Path('build/connection-dos')/report['case']['case']
  rows=decode(folder,report,identity);wire=(ROOT/folder/'serial.bin').read_bytes()
  if kind=='before':assert wire.count(b'\x1b[C')==2 and not any('Command Menu' in row['title'] for row in rows)
  else:assert b'\x1b[C' not in wire and any(row['key']&255==27 and row['guards']['_command_menu_active']==1 for row in rows);sources(report)
  assert b'\x1b[2;1R' in wire and b'ready' in wire
  before=(ROOT/folder/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(ROOT/folder/'AFTER.BIN').read_bytes()
  listing=(ROOT/map_path).read_text();symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
  near=identity['memory_layout']['near_relative_segment'];assert report['offsets']=={n:s*16+o-near*16 for n in FIELDS for s,o in [symbols[n]]}
  if kind=='before':
   for name,value in report['sources'].items():
    copied=out/Path(name).name;actual=sha(copied) if (ROOT/copied).is_file() else sha(name)
    assert actual==value,name
  samples[kind]=report
  artifacts.extend(f.relative_to(ROOT) for base in (ROOT/out,ROOT/folder) for f in sorted(base.rglob('*')) if f.is_file())
 linked=read('build/terminal/menu-pending-checks.json');assert linked['passed'] and linked['binary_sha256']==runtime and linked['inputs']==36;sources(linked)
 menu=read('docs/validation/command-menu.json');assert menu['passed'] and menu['binary_sha256']==runtime and len(menu['actual_DOS']['cases'])==4
 assert all(c['passed'] and all(c['checks'].values()) for c in menu['actual_DOS']['cases'])
 artifacts.extend(map(Path,['build/terminal/menu-pending-checks.json','docs/validation/command-menu.json','build/terminal/manifest.json']))
 # The observed stock attempt did not reproduce the earlier refusal. Retain
 # its measured guards and successful harness, without publishing BBS artwork.
 stock=Path('build/bbs-lab/results/synchronet/menu-guard-c0d6-1500-1')
 observed=read(stock/'menu-guard-records.json');stock_result=read(stock/'result.json')
 assert observed['binary_sha256']==old['binary_sha256'] and stock_result['passed']
 altz=next(row for row in observed['records'] if row['key']==0x2c00)
 assert altz['guards']['terminal_parser_active']==0
 assert any(row['key'] in (0x4d00,0x4de0) and row['guards']['_command_menu_active']==1 for row in observed['records'])
 fixture=read(str(stock)+'-logon.json');verification=read(str(stock)+'-logon.verify.json')
 assert fixture['restored'] and fixture['before']==fixture['after']==verification['exemptions']==0
 artifacts.extend(f.relative_to(ROOT) for f in sorted((ROOT/stock).iterdir()) if f.is_file() and f.name!='.lock')
 artifacts.extend(f.relative_to(ROOT) for f in sorted((ROOT/stock.parent).glob(stock.name+'-logon.*')) if f.is_file())
 result=dict(passed=True,binary_sha256=runtime,baseline=dict(source_commit=BASELINE,binary_sha256=old['binary_sha256'],compiled_inputs_verified_from_commit=True),
  controlled_DOS=samples,linked=linked,independent_behavioral_DOS=dict(report='docs/validation/command-menu.json',case=menu['actual_DOS']['cases'][3]),
  instrumented_stock_nonreproduction=dict(binary_sha256=old['binary_sha256'],harness_passed=True,
   observed_AltZ_guards=altz['guards'],following_Right_observed_menu=True,restored_logon_fixture=fixture,independent_readback=verification,
   scope='Original1500ms recipe plus diagnostic observer succeeded. Observer changes load placement/timing. This does not identify the cause of the earlier unobserved refusal.'),
  terminal_regression=menu['terminal_regression'],source_rebuild=menu['source_rebuild'],runtime_sources=manifest['sources'],
  sources={name:sha(name) for name in ['standalone/record_menu_pending.py','standalone/probe_menu_parser_dos.py','standalone/menu_guard_watch.asm','lab/bbs/menu_guard_probe.py']},
  retained_artifacts={str(f):sha(f) for f in artifacts},
  scope='Maintained parser-safe Alt-Z request, existing32-key FIFO, repeated-request coalescing, cancellation and opening revalidation. Controlled actual DOS before/after plus separate state-independent video/peer behavior and full regression/source rebuild. Earlier isolated BBS refusal remains unattributed; original UI parity, physical modem and whole application remain open.')
 (ROOT/'docs/validation/menu-pending.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded parser-safe menu entry',runtime)

if __name__=='__main__':main()
