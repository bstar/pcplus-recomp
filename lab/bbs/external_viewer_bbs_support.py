"""Owned external child and post-child exact stock-editor restoration audit."""
import json,struct,subprocess
from pathlib import Path
from product_inputs import ROOT,sha

SOURCES=['lab/bbs/external_viewer_bbs_support.py','standalone/file_directory_bbs_watch.asm','standalone/viewer_external_child.asm']

def prepare(folder,admission_binary=None):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
 observer=folder/'EXWATCH.COM'
 observer_source=ROOT/SOURCES[1]
 if admission_binary:
  from program_admission_support import instrument
  observer_source=folder/'observer.asm';observer_source.write_text(instrument((ROOT/SOURCES[1]).read_text(),admission_binary))
 subprocess.run(['nasm','-fbin','-DEXTERNAL_VIEWER_ROUNDTRIP',str(observer_source),'-o',str(observer)],check=True)
 source=(ROOT/SOURCES[2]).read_text()
 # The owned child deliberately leaves graphics mode, then marks its completion
 # to the passive observer. A pre-EXEC screen cannot satisfy the return gate.
 source=source.replace(' mov ax,4c00h',' mov ax,13h\n int 10h\n mov ax,0d744h\n mov bx,5658h\n int 2fh\n mov ax,4c00h',1)
 (folder/'child.asm').write_text(source);child=folder/'VTEST.COM'
 subprocess.run(['nasm','-fbin',str(folder/'child.asm'),'-o',str(child)],check=True)
 return child,observer

def audit(output,tool='viewer'):
 assert tool in ('viewer','editor')
 output=Path(output);raw=(output/'VFVIEW.BIN').read_bytes();words=struct.unpack_from('<12H',raw) if len(raw)==12024 else None
 wire=(output/'serial-received.bin').read_bytes();path=output/'VCHILD.BIN';child=path.read_bytes() if path.exists() else b''
 prompt=raw[8024:12024];settings=(output/'TEST.PRM').read_bytes()
 checks=dict(observer_complete=words is not None and words[:4]==(0x5657,1,1,1),
  exact_post_child_editor_frame=words is not None and raw[24:4024]==raw[4024:8024],
  cursor_shape_preserved=words is not None and words[6]==words[7] and words[8]==words[9],
  mode_rows_preserved=words is not None and words[4:6]==(25,25) and words[10:12]==(0x5003,0x5003),
  parameter_prompt=prompt[(12*80+7)*2:(12*80+24)*2:2]==b'Enter parameters:',
  configured_title=b'VTEST.COM Parameters' in prompt[::2],
  actual_child=len(child)==202 and struct.unpack_from('<2H',child)==(0x5645,1),
  exact_child_tail=len(child)==202 and child[8:19]==b'\x09 PAGE.DAT\r',
  original_drive_CWD=len(child)==202 and struct.unpack_from('<H',child,136)[0]==2 and child[138]==0,
  synthetic_configuration=settings[(0x39e if tool=='editor' else 0x35d):(0x3df if tool=='editor' else 0x39e)]==b'D:\\VTEST.COM'.ljust(65,b'\0'),
  parameters_consumed_locally=b'PAGE.DAT' not in wire,
  subsequent_editor_keys=b'ABCDE' in wire and b'UNSAVED' in wire)
 if tool=='editor':checks['independent_viewer_setting']=settings[0x35d:0x39e]==b'NO-VIEW.COM'.ljust(65,b'\0')
 r=dict(passed=all(checks.values()),external_command_tool=tool,checks=checks,observer_words=words,capture_sha256=sha(output/'VFVIEW.BIN'),child_sha256=sha(path) if child else None,
  sources={n:sha(ROOT/n) for n in SOURCES},scope='Actual Alt-V parameter dialog and external COMSPEC /c owned child inside the stock unsaved editor. Child records PSP/CWD, enters mode13h, then sends a private observer-only completion marker. Return capture is gated on that marker and text-mode editor visibility; no pre-EXEC frame can pass. Full4000-byte editor/cursor/shape preservation and subsequent ordinary editing. No product-memory writes, terminal replies, physical/SIP/audio acceptance or broad external-program claim.')
 r['scope']=r['scope'].replace('Alt-V', 'Alt-A' if tool=='editor' else 'Alt-V')
 (output/('external-'+tool+'-audit.json')).write_text(json.dumps(r,indent=2)+'\n');return r
