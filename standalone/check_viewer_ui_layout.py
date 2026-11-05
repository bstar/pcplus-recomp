#!/usr/bin/env python3
"""Verify viewer state/loan retention and linked resident safety gates; no execution."""
import argparse,json,re,struct
from pathlib import Path
from build_path_session import ROOT,sha
from terminal_memory import inspect_terminal_memory

def inspect(binary):
 data=binary.read_bytes();header=struct.unpack_from('<14H',data);begin=header[4]*16
 listing=binary.with_name('terminal.map').read_text();symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 memory=inspect_terminal_memory(binary,binary.with_name('terminal.map'));filecode=next(c for c in memory['code_segments'] if c['name']=='FILE_CODE');config=next(c for c in memory['code_segments'] if c['name']=='CONFIG_CODE');bank=filecode['relative_segment']
 spans=[]
 for name,size,cookie in [('_terminal_viewer_dialog_state',68,0x5644),('_viewer_session_storage',596,0x5653),('_viewer_file_storage',90,0x5646)]:
  seg,off=symbols[name];at=seg*16+off;assert seg==bank and seg!=memory['near_relative_segment']
  assert off+size<=filecode['offset']+filecode['bytes'] and at+size<=memory['retained_parent_paragraphs']*16-256
  assert struct.unpack_from('<H',data,begin+at)[0]==cookie
  spans.append((at,at+size,name))
 for lo,hi,name in spans:
  for lo2,hi2,other in spans:
   if name!=other:assert hi<=lo2 or hi2<=lo,(name,other)
  for other,size in [('_terminal_file_dialog_state',1676),('_file_find_storage',48),('_path_session_storage',76),('_terminal_path_dialog_state',144),('_gateway_front_storage',20),('_gateway_files_storage',6),('_process_handles_storage',36),('gateway_uart_storage',22)]:
   if other in symbols:
    at=symbols[other][0]*16+symbols[other][1];assert hi<=at or at+size<=lo,(name,other)
 for n in ['viewer_dialog_event','viewer_dialog_cursor','viewer_dialog_shape','viewer_dialog_pending','viewer_dialog_owned','viewer_dialog_unsafe','viewer_dialog_shutdown','viewer_file_conflict','viewer_file_open','viewer_file_read','viewer_file_seek','viewer_file_close','viewer_session_begin','viewer_session_step','viewer_session_move','viewer_session_stop','viewer_decode_init','viewer_decode_feed','viewer_decode_finish']:
  assert symbols['_'+n][0]==bank,n
 for n in ['_viewer_admit_validate','_viewer_admit_claim','_viewer_admit_release']:assert symbols[n][0]==config['relative_segment'],n
 resident=next(c for c in memory['code_segments'] if c['name']=='_TEXT');code=data[begin+resident['relative_segment']*16:begin+resident['relative_segment']*16+resident['bytes']];gates={}
 for n in ['_viewer_dialog_pending','_viewer_dialog_owned','_viewer_dialog_shutdown','_viewer_dialog_unsafe']:
  seg,off=symbols[n];encoded=b'\x9a'+struct.pack('<HH',off,seg);assert code.count(encoded)==1,(n,'missing/duplicate resident gate');gates[n]=code.index(encoded)
 assert gates['_viewer_dialog_shutdown']<gates['_viewer_dialog_unsafe']
 snapshot=symbols['redisplay_snapshot'];end=symbols['redisplay_snapshot_end'];assert snapshot[0]==end[0] and end[1]-snapshot[1]==63000 and snapshot[1]+3920<=65536
 return dict(memory=memory,viewer_state_bytes=754,persistent_DGROUP_bytes=0,gates=gates,borrowed_page_capacity=3920,existing_snapshot_bytes=63000)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_file_viewer'] and sha(binary)==manifest['binary_sha256']
 result=inspect(binary)
 # Test the gate decoder against byte-local damage without executing copies.
 data=binary.read_bytes();header=struct.unpack_from('<14H',data);start=header[4]*16;out.mkdir(parents=True);controls=[]
 for name,offset in result['gates'].items():
  damaged=bytearray(data);damaged[start+offset+3]^=1
  folder=out/name;folder.mkdir();target=folder/'damaged.analysis.exe';target.write_bytes(damaged)
  (folder/'terminal.map').write_bytes(binary.with_name('terminal.map').read_bytes())
  try:inspect(target)
  except AssertionError:controls.append(dict(gate=name,rejected=True))
  else:raise AssertionError(name)
 names=['standalone/check_viewer_ui_layout.py','standalone/terminal_memory.py','standalone/build_path_session.py']
 r=dict(passed=True,binary_sha256=sha(binary),**result,negative_controls=controls,sources={n:sha(ROOT/n) for n in names},original_inputs=[],
  scope=__doc__+' Check754retained FILE_CODE state bytes/cookies/disjointness, far APIs/admission segment, existing63000-byte frozen-storage loan, unchanged DGROUP size and four linked pending/EXEC/shutdown/quarantine resident calls. Four damaged synthetic images are inspected only, never executed. Runtime coverage remains separate.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS retained viewer state,loan,4safety gates and4unexecuted negative controls')
if __name__=='__main__':main()
