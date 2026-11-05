"""Passive File Directory roundtrip inside an owned stock BBS editor."""
import json,struct,subprocess
from pathlib import Path
from product_inputs import ROOT,sha
SOURCES=['lab/bbs/file_directory_bbs_support.py','standalone/file_directory_bbs_watch.asm']

def prepare(folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
 observer=folder/'FDWATCH.COM'
 subprocess.run(['nasm','-fbin',str(ROOT/SOURCES[1]),'-o',str(observer)],check=True)
 return observer

def audit(output):
 output=Path(output);path=output/'FDVIEW.BIN';raw=path.read_bytes() if path.exists() else b''
 words=struct.unpack_from('<12H',raw) if len(raw)==8344 else None
 wire=(output/'serial-received.bin').read_bytes()
 header=raw[8024:8184:2];entry=raw[8184:8344:2]
 checks=dict(observer_complete=words is not None and words[:4]==(0x464f,1,1,1),
  exact_editor_frame=words is not None and raw[24:4024]==raw[4024:8024],
  cursor_shape_preserved=words is not None and words[6]==words[7] and words[8]==words[9],
  mode_rows_preserved=words is not None and words[4:6]==(25,25) and words[10:12]==(0x5003,0x5003),
  real_listing_heading=b'FILE NAME       SIZE    DATE    TIME' in header,
  real_listing_entry=entry[22:30]==b'TEST.PRM' and entry[36:42]==b'  1264',
  file_spec_consumed_locally=b'TEST.PRM' not in wire,
  subsequent_edit_keys=b'ABCDE' in wire and b'UNSAVED' in wire)
 result=dict(passed=all(checks.values()),checks=checks,observer_words=words,capture_sha256=sha(path) if path.exists() else None,
  sources={n:sha(ROOT/n) for n in SOURCES},scope='Actual Alt-F, TEST.PRM search and Escape inside an owned stock editor. Passive BIOS/VGA before/after full4000-byte frame, cursor/shape, heading and real1264-byte file entry; continued normal editing and local filename consumption. No product memory writes, injected terminal replies, SIP/DSP/analog or physical acceptance.')
 (output/'file-directory-audit.json').write_text(json.dumps(result,indent=2)+'\n');return result
