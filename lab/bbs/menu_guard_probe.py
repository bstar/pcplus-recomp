#!/usr/bin/env python3
"""Run the unchanged stock transfer harness with a diagnostic INT16 observer.

All arguments belong to test_transfer_dos.py. Only its DOSBox process boundary
is wrapped: install/collect a map-bound test TSR in its fresh owned fixture.
No product function, key source, peer response or protocol validator is replaced.
The observer changes memory/timing and reads product state; this is diagnostic
evidence, not an uninstrumented compatibility or original-equivalence claim.
"""
import asyncio,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
import test_transfer_dos as harness
ROOT=harness.ROOT
FIELDS=['terminal_parser_active','terminal_transfer_pending','terminal_transfer_active',
 'terminal_program_pending','terminal_program_active','terminal_macro_active',
 'terminal_monitor_active','terminal_controller_active','terminal_ansi_wait_active',
 'terminal_snapshot_active','uart_break_hold','screen_viewport_enabled',
 'text_cga_status_port','text_video_segment','screen_attribute_row_bytes',
 'screen_video_row_bytes','connection_state','_redisplay_active',
 '_command_menu_active','keyboard_debug_gate','terminal_history_start',
 'terminal_history_end','terminal_history_pointer','terminal_history_wrapped']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 manifest=json.loads((ROOT/'build/terminal/manifest.json').read_text())
 digest=sha(harness.BINARY);assert digest==manifest['binary_sha256']
 for name,value in manifest['sources'].items():assert sha(ROOT/name)==value,name
 listing=(ROOT/'build/terminal/terminal.map').read_text()
 symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 near=manifest['memory_layout']['near_relative_segment']
 offsets={name:seg*16+off-near*16 for name in FIELDS for seg,off in [symbols[name]]}
 assert all(0<=off<manifest['data_stack_bytes']-1 for off in offsets.values())
 original=asyncio.create_subprocess_exec;folders=[]
 async def observed_exec(*argv,**kwargs):
  assert argv[0]=='dosbox-x' and argv.count('-conf')==1,argv
  config=Path(argv[argv.index('-conf')+1]).resolve();folder=config.parent
  folder.relative_to(ROOT/'build/bbs-lab/results')
  assert not (folder/'MGWATCH.COM').exists() and not folders
  include='%define GUARD_COUNT '+str(len(FIELDS))+'\n%define GUARD_OFFSETS dw '+','.join(str(offsets[n]) for n in FIELDS)+'\n'
  (folder/'menu-guards.inc').write_text(include)
  source=ROOT/'standalone/menu_guard_watch.asm'
  subprocess.run(['nasm','-fbin','-I',str(folder)+'/',str(source),'-o',str(folder/'MGWATCH.COM')],check=True)
  text=config.read_text();needle='D:\\SNAP B\n';assert text.count(needle)==1
  text=text.replace(needle,needle+'D:\\MGWATCH T\n')
  needle='D:\\SNAP S\n';assert text.count(needle)==1
  collect='D:\\MGWATCH\nif errorlevel 1 goto menu_guard_failed\ngoto menu_guard_done\n:menu_guard_failed\necho FAIL>D:\\FAIL.TXT\n:menu_guard_done\n'
  text=text.replace(needle,needle+collect);config.write_text(text)
  inputs=dict(binary_sha256=digest,fields=FIELDS,offsets=offsets,
   sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),source,ROOT/'lab/bbs/test_transfer_dos.py']},
   map_sha256=sha(ROOT/'build/terminal/terminal.map'),observer_sha256=sha(folder/'MGWATCH.COM'),
   scope=__doc__)
  (folder/'menu-guard-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');folders.append(folder)
  return await original(*argv,**kwargs)
 asyncio.create_subprocess_exec=observed_exec
 try:code=harness.main()
 finally:asyncio.create_subprocess_exec=original
 assert sha(harness.BINARY)==digest and len(folders)==1
 folder=folders[0];raw=(folder/'MGUARD.BIN').read_bytes()
 magic,version,size,n,count,overflow=struct.unpack_from('<6H',raw)
 assert magic==0x474d and version==1 and n==len(FIELDS) and size==16+n*2+8+240
 assert len(raw)==12+32*size and count<=32 and overflow==0
 records=[]
 for index in range(count):
  at=12+index*size;key,low,high,ip,cs,ds,ss,bp=struct.unpack_from('<8H',raw,at)
  values=struct.unpack_from('<'+str(n)+'H',raw,at+16)
  mode,cols,page,rows=struct.unpack_from('<4H',raw,at+16+n*2);chars=at+16+n*2+8
  records.append(dict(key=key,ticks=high*65536+low,caller=dict(IP=ip,CS=cs,DS=ds,SS=ss,BP=bp),
   guards=dict(zip(FIELDS,values)),BDA=dict(mode=mode,columns=cols,page=page,last_row=rows),
   title=raw[chars:chars+80].decode('cp437'),header=raw[chars+80:chars+160].decode('cp437'),footer=raw[chars+160:chars+240].decode('cp437')))
  assert ds==ss and cs+near==ds,'Observed caller does not match this small-model executable'
 result=dict(binary_sha256=digest,original_harness_exit=code,records=records,
  scope='Observation after actual BIOS key return, before application dispatch. Map-bound application reads and BDA/video only; no keys or product state written. Observer memory/timing can change refusal reproduction.')
 (folder/'menu-guard-records.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));return code

if __name__=='__main__':raise SystemExit(main())
