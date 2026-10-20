#!/usr/bin/env python3
"""Actual modal/transfer cancellation from an independently checked timer ISR."""
import argparse,binascii,json,re,shutil,struct,subprocess,types,uuid
from pathlib import Path
import test_aspect_renderer_dos as render
from modem_fixtures import fixture
from directory_fixtures import directory
ROOT=render.ROOT;sha=render.sha
CASES={
 'browser':('DIRECTORY','',None),
 'editor':('RECORD','p500 e',None),
 'capture':('[PCPLUS.LOG]','p2000 a-f1',None),
 'download':('Download:','p2000 a-r',None),
 'receive':('Receiving','p2000 a-r p300 R E C V . B I N enter',None),
 'receive-partial':('Receiving+','p2000 a-r p300 R E C V . B I N enter',None),
 'upload':('Upload:','p2000 a-s',None),
 'send':('Sending','p2000 a-s p300 S E N D . B I N enter',None),
 'program':('return','p2000 a-1',None),
 'reload':('Reload','p2000 a-f9',None),
 'serial':('current-port','p2000 a-f10',[(2,8)]),
 'profile':('switches;','p2000 a-f10',[(0x194,4)]),
 'translation':('translation','p2000 a-f10',[(0x1e0,2)]),
 'port':('Both','p2000 a-f10',[(0,1),(0x176,0x2f8),(0x186,3)]),
}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mouse',action='store_true')
 p.add_argument('--label',default='cancel-'+uuid.uuid4().hex);p.add_argument('--case',action='append',choices=CASES)
 args=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
 out=ROOT/'build/terminal-cancel-tests'/args.label;out.mkdir(parents=True,exist_ok=False)
 binary=ROOT/'build'/('terminal-traps-mouse' if args.mouse else 'terminal-traps')/'TERMINAL.EXE'
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['terminal_traps']
 assert manifest['binary_sha256']==sha(binary)
 names=['test_terminal_cancel_dos.py','terminal_cancel_parent.c','cancel_settings_child.c','test_connection_dos.py',
  'test_terminal.py','test_aspect_renderer_dos.py','modem_fixtures.py','terminal_config_fixtures.py','directory_fixtures.py','directory_test_support.py']
 sources={**manifest['sources'],**{'standalone/'+n:sha(ROOT/'standalone'/n) for n in names}}
 for n,h in sources.items():
  assert sha(ROOT/n)==h,n
  target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
 syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(binary.parent/'terminal.map').read_text(),re.M|re.I)}
 data=manifest['memory_layout']['near_relative_segment'];trap_seg,trap_off=syms['terminal_trap_break']
 fields=dict(PHASE_OFF='terminal_trap_phase',PENDING_OFF='terminal_trap_pending',HARDWARE_OFF='hardware_active',
  PROGRAM_OFF='terminal_program_active',TRANSFER_OFF='terminal_transfer_active',BLOCKS_OFF='session_blocks_accepted')
 defines=dict(TRAP_SEG=trap_seg,TRAP_OFF=trap_off,DATA_SEG=data,**{n:syms[s][1] for n,s in fields.items()})
 build=out/'parent';build.mkdir()
 for src,name,flags in [('terminal_cancel_parent.c','CANCEL.EXE',['-d'+n+'='+str(v) for n,v in defines.items()]),('cancel_settings_child.c','PRMEDIT.EXE',[])]:
  subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',*flags,'-fe='+name,str(out/'sources/standalone'/src)],cwd=build,check=True)
 source=(ROOT/'standalone/test_connection_dos.py').read_text().replace('cputype=386','cputype=8086')
 changes={"out=ROOT/'build/connection-dos'/name":'out=CANCEL_OUT/name',
  "checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'":"checks['actual_screen_snapshot']=len(screen)==4000",
  r'C:\\TERMINAL {arguments}':r'D:\\CANCEL {CANCEL_TARGET} {arguments}'}
 for old,new in changes.items():assert source.count(old)==1;source=source.replace(old,new)
 old='if online:\n       line.append(byte)'
 assert source.count(old)==1
 source=source.replace(old,old+'''\n       if CANCEL_PARTIAL and byte==ord('C') and not checks.get('partial_frame_sent'):
        conn.sendall(PARTIAL_FRAME);checks['partial_frame_sent']=True''')
 harness=types.ModuleType('cancel_connection');harness.__file__=str(ROOT/'standalone/test_connection_dos.py');harness.CANCEL_OUT=out
 exec(compile(source,harness.__file__,'exec'),harness.__dict__);results=[]
 for name in args.case or CASES:
  marker,keys,updates=CASES[name];folder=out/name;folder.mkdir();shutil.copyfile(binary,folder/'TERMINAL.EXE')
  harness.BINARY=folder/'TERMINAL.EXE';harness.CANCEL_TARGET=marker
  harness.CANCEL_PARTIAL=name=='receive-partial'
  payload=bytes(range(128));harness.PARTIAL_FRAME=b'\x01\x01\xfe'+payload+binascii.crc_hqx(payload,0).to_bytes(2,'big')
  settings=bytearray(fixture(timeout=5));struct.pack_into('<HH',settings,0x4e4,8,4)
  if name=='reload':
   struct.pack_into('<H',settings,0x1e0,1);files_table=bytes(range(256))
  files={'CANCEL.EXE':(build/'CANCEL.EXE').read_bytes()};expected=bytearray(settings)
  if name=='reload':files['PCPLUS.XLT']=files_table
  offline=name in ['browser','editor'];directory_data=directory() if offline else None
  arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR' if offline else '@D:\\TEST.PRM /D:CaseTest:23'
  if updates:
   # Live setup deliberately accepts a current-directory 8.3 leaf only.
   arguments='@TEST.PRM /D:CaseTest:23'
   for offset,value in updates:struct.pack_into('<H',expected,offset,value)
   files.update({'PREP.PRM':bytes(expected),'PRMEDIT.EXE':(build/'PRMEDIT.EXE').read_bytes()})
  if name=='program':
   key=bytearray(540)
   for i in range(10):struct.pack_into('<H',key,i*54,3)
   struct.pack_into('<H',key,0,1);key[2:2+len(b'D:\\CHILD.COM')]=b'D:\\CHILD.COM'
   files.update({'TEST.KEY':bytes(key),'CHILD.COM':b'\xb8\x00\x4c\xcd\x21'})
   arguments+=' /T:D:\\TEST.KEY'
  if name=='send':files['SEND.BIN']=bytes(range(128))
  proof=harness.run(name,'cancel' if offline else 'success',keys,prm=bytes(settings),prm_expected=bytes(expected),
   arguments=arguments,directory=directory_data,accounting_delta=0,working_drive='d',files=files)
  raw=(folder/'CANCEL.BIN').read_bytes() if (folder/'CANCEL.BIN').exists() else b''
  witness=struct.unpack('<16H',raw) if len(raw)==32 else None
  view=(folder/'CANCEL.VID').read_bytes() if (folder/'CANCEL.VID').exists() else b''
  checks=proof['checks'];checks.update(independent_timer_fired=witness is not None and witness[0]==0xca16 and witness[3]==1,
   owned_trap_delivered=witness is not None and witness[6:9]==(1,0,1),
   no_rescue_key_required=witness is not None and witness[4]==0,
   prompt_exit_latency=witness is not None and witness[5]<18,
   actual_DOS_exit16=witness is not None and witness[1]==16,
   trap_vectors_and_flag_restored=witness is not None and witness[12]==1,
   actual_modal_screen=marker.rstrip('+').encode() in view)
  if name=='receive-partial':
   checks.update(actual_block_accepted=witness is not None and witness[15]==1 and b'\x06' in (folder/'serial.bin').read_bytes(),
    no_partial_target_installed=not (folder/'RECV.BIN').exists(),
    no_download_stage_left=not (folder/'PCRX.$$$').exists())
  if name in ['capture','download','upload']:checks['no_unaccepted_file_created']=not (folder/('PCPLUS.LOG' if name=='capture' else 'RECV.BIN')).exists()
  proof.update(passed=all(checks.values()),witness=witness,mouse=args.mouse,marker=marker)
  (folder/'result.json').write_text(json.dumps(proof,indent=2)+'\n');results.append(proof)
  print(name,'CANCEL PASS' if proof['passed'] else 'CANCEL FAIL',flush=True)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 report=dict(passed=all(c['passed'] for c in results),cases=results,sources=sources,
  parent_sha256=sha(build/'CANCEL.EXE'),binary_sha256=sha(binary),checker_sha256=sha(Path(__file__)),
  scope='Actual8086 DOS modal waits and synthetic timer INT1B to the exact linked owned handler. Independent kernel exit/vector/flag and UART restoration; rescue BIOS Escape exposes blocked cancellation. No DOS call in timer, no product field patch, no physical Ctrl-Break/modem claim.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
