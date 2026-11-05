"""Owned Gateway child and passive stock-editor frame evidence."""
import json,struct,subprocess
from pathlib import Path
from product_inputs import ROOT,sha
SOURCES=['lab/bbs/gateway_bbs_support.py','standalone/gateway_bbs_child.asm','standalone/gateway_bbs_watch.asm']
def prepare(folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 child=folder/'GWSHELL.COM';observer=folder/'GWWATCH.COM'
 for source,target in [('standalone/gateway_bbs_child.asm',child),('standalone/gateway_bbs_watch.asm',observer)]:
  assert not target.exists();subprocess.run(['nasm','-fbin',str(ROOT/source),'-o',str(target)],check=True)
 return child,observer

def audit(output):
 output=Path(output);report=output/'GWVIEW.BIN';raw=report.read_bytes() if report.exists() else b''
 words=struct.unpack_from('<12H',raw) if len(raw) in (8024,16024) else None
 child=(output/'GWCHILD.BIN').read_bytes() if (output/'GWCHILD.BIN').exists() else b''
 stride=(len(raw)-24)//2 if words else 0
 wire=(output/'serial-received.bin').read_bytes()
 checks=dict(actual_empty_tail_child=child==b'\0\r',observer_complete=words is not None and words[:4]==(0x474f,1,1,1),
  exact_editor_frame=words is not None and raw[24:4024]==raw[24+stride:4024+stride],
  cursor_and_shape=words is not None and words[6:7]==words[7:8] and words[8:9]==words[9:10],
  mode_and_rows=words is not None and words[4:6]==(25,25) and words[10:12]==(0x5003,0x5003),
  post_return_edit_keys=b'ABCDE' in wire and b'UNSAVED' in wire)
 result=dict(passed=all(checks.values()),checks=checks,observer_words=words,
  capture_sha256=sha(report) if report.exists() else None,child_report_hex=child.hex(),
  sources={s:sha(ROOT/s) for s in SOURCES},
  scope='Actual keyboard Gateway and graphics-mode DOS child inside an owned stock BBS editor; passive BIOS/VGA frame and cursor comparison, empty-tail file and subsequent edit-key wire. No product state or terminal reply injection. One quiet-editor return, not sustained traffic, physical/audio or all workflows.')
 (output/'gateway-audit.json').write_text(json.dumps(result,indent=2)+'\n');return result
