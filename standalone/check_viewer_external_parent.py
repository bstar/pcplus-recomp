#!/usr/bin/env python3
"""Inspect retained external state and actual PROGRAM/COMSPEC/cancel dispatch gates."""
import argparse,json,re,struct
from pathlib import Path
from build_path_session import ROOT,sha
from terminal_memory import inspect_terminal_memory

def inspect(binary):
 data=binary.read_bytes();header=struct.unpack_from('<14H',data);begin=header[4]*16
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
 memory=inspect_terminal_memory(binary,binary.with_name('terminal.map'));banks={b['name']:b for b in memory['code_segments']}
 def linear(name):seg,off=symbols[name];return seg*16+off
 def encoded(name):seg,off=symbols[name];return b'\x9a'+struct.pack('<HH',off,seg)
 state=linear('_terminal_external_viewer_state');bank=banks['FILE_CODE'];assert symbols['_terminal_external_viewer_state'][0]==bank['relative_segment']
 assert state+128<=bank['relative_segment']*16+bank['bytes'] and state+128<=memory['retained_parent_paragraphs']*16-256
 assert data[begin+state:begin+state+128]==b'\x58\x56'+bytes(126),'External bank must initialize inactive'
 for name in ['_viewer_external_build','_viewer_external_select','_viewer_external_event','_viewer_external_owned','_viewer_external_unsafe','_viewer_external_queued','_viewer_external_start','_viewer_external_execute','_viewer_external_cancel']:
  assert symbols[name][0]==bank['relative_segment'],name
 assert symbols['_program_execute_external'][0]==banks['CONFIG_CODE']['relative_segment']
 queue=linear('_external_program_queue');code=data[begin+queue:begin+queue+20];assert code[0]==0xb8 and code[3]==0xe8
 marker=struct.unpack_from('<H',code,1)[0];ds=memory['near_relative_segment'];assert marker+2<=memory['near_bytes']
 assert data[begin+ds*16+marker:begin+ds*16+marker+2]==b'V\0'
 target=(symbols['_external_program_queue'][1]+6+struct.unpack_from('<h',code,4)[0])&0xffff
 assert symbols['terminal_program_start']==(symbols['_external_program_queue'][0],target),'Ordinary PROGRAM admission must run'
 gates={}
 dispatch=linear('terminal_redisplay_key_impl')
 assert data[begin+dispatch:begin+dispatch+3]==b'\x3d\x00\xf3','Viewer must use F300; F600 belongs to redial'
 for name,bank_name in [('_viewer_external_execute','_TEXT'),('_viewer_external_cancel','_TEXT'),('_viewer_external_start','CONFIG_CODE'),('_program_execute_external','FILE_CODE')]:
  b=banks[bank_name];at=b['relative_segment']*16;raw=data[begin+at:begin+at+b['bytes']];sig=encoded(name)
  assert raw.count(sig)==1,(name,'gate missing or duplicated');pos=raw.index(sig);gates[name]=at+pos
  assert at+pos+3 in {s*16+o for o,s in (struct.unpack_from('<HH',data,header[12]+i*4) for i in range(header[3]))},name
 return dict(memory=memory,state_bytes=128,near_marker_bytes=2,near_bytes=memory['near_bytes'],resident_code_bytes=memory['resident_code_bytes'],gates=gates,private_action_site=dispatch,private_action=0xf300,redial_action=0xf600)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_external_viewer'] and sha(binary)==manifest['binary_sha256']
 result=inspect(binary);out.mkdir();data=binary.read_bytes();begin=struct.unpack_from('<H',data,8)[0]*16;controls=[]
 for name,at in result['gates'].items():
  folder=out/name;folder.mkdir();target=folder/'damaged.analysis.exe';damaged=bytearray(data);damaged[begin+at+3]^=1;target.write_bytes(damaged);target.with_name('terminal.map').write_bytes(binary.with_name('terminal.map').read_bytes())
  try:inspect(target)
  except AssertionError:controls.append(dict(gate=name,rejected=True))
  else:raise AssertionError(name)
 folder=out/'redial-collision';folder.mkdir();target=folder/'damaged.analysis.exe';damaged=bytearray(data);at=result['private_action_site'];damaged[begin+at+1:begin+at+3]=struct.pack('<H',0xf600);target.write_bytes(damaged);target.with_name('terminal.map').write_bytes(binary.with_name('terminal.map').read_bytes())
 try:inspect(target)
 except AssertionError:controls.append(dict(gate='redial-action-collision',rejected=True))
 else:raise AssertionError('Redial collision must be rejected')
 names=['standalone/check_viewer_external_parent.py','standalone/terminal_memory.py','standalone/build_path_session.py']
 (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),**result,negative_controls=controls,sources={n:sha(ROOT/n) for n in names},scope=__doc__+' Static linked instruction/relocation/state retention and distinct viewer/redial action checks; five damaged analysis-only copies are rejected without execution. No runtime or physical acceptance.'),indent=2)+'\n');print('PASS retained128-byte state,2-byte marker,4gates,distinct redial action and5unexecuted negative controls')
if __name__=='__main__':main()
