"""Owned read-only viewer file and passive exact stock-editor return evidence."""
import json,struct,subprocess
from pathlib import Path
from product_inputs import ROOT,sha
SOURCES=['lab/bbs/file_viewer_bbs_support.py','standalone/file_directory_bbs_watch.asm']
PAYLOAD=b'VIEWER CHECK\r\nREAD ONLY / CP437: \xdb\xb1\xc4\r\nEditor stays active.\r\n'
FOOTER=b' Home: Top of file      PgUp: Previous page      PgDn: Next page      ESC: Exit '

def expected_page():
 rows=[b'VIEWER CHECK',b'READ ONLY / CP437: \xdb\xb1\xc4',b'Editor stays active.']+[b'']*21+[FOOTER]
 return b''.join(bytes((c,0x71 if i==24 else 7)) for i,row in enumerate(rows) for c in row.ljust(80,b' '))

def prepare(folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);observer=folder/'VFWATCH.COM'
 subprocess.run(['nasm','-fbin','-DFILE_VIEWER_ROUNDTRIP',str(ROOT/SOURCES[1]),'-o',str(observer)],check=True)
 return observer

def audit(output,require_high=False):
 output=Path(output);path=output/'VFVIEW.BIN';raw=path.read_bytes() if path.exists() else b''
 words=struct.unpack_from('<12H',raw) if len(raw)==12024 else None
 wire=(output/'serial-received.bin').read_bytes();view=(output/'VIEW.DAT').read_bytes() if (output/'VIEW.DAT').exists() else None
 segment_path=output/'VFSEG.BIN';segment_raw=segment_path.read_bytes() if segment_path.exists() else b''
 segment=struct.unpack('<H',segment_raw)[0] if len(segment_raw)==2 else None
 checks=dict(observer_segment_recorded=segment is not None,
  observer_high_if_required=not require_high or segment is not None and segment>=0xa000,
  observer_complete=words is not None and words[:4]==(0x5657,1,1,1),
  exact_editor_frame=words is not None and raw[24:4024]==raw[4024:8024],
  cursor_shape_preserved=words is not None and words[6]==words[7] and words[8]==words[9],
  mode_rows_preserved=words is not None and words[4:6]==(25,25) and words[10:12]==(0x5003,0x5003),
  exact_2000_viewer_cells=raw[8024:12024]==expected_page(),owned_input_unchanged=view==PAYLOAD,
  filename_consumed_locally=b'VIEW.DAT' not in wire,
  subsequent_edit_keys=b'ABCDE' in wire and b'UNSAVED' in wire)
 result=dict(passed=all(checks.values()),checks=checks,observer_words=words,observer_resident_segment=segment,observer_high_required=require_high,capture_sha256=sha(path) if path.exists() else None,
  file_sha256=sha(output/'VIEW.DAT') if view is not None else None,sources={n:sha(ROOT/n) for n in SOURCES},
  scope='Actual Alt-V, owned D:\\VIEW.DAT read-only page and Escape inside a stock unsaved editor. Passive full4000-byte editor return/cursor/shape plus4000-byte local viewer image, subsequent ordinary editing and unchanged generated file. Observer install creates only its owned DOS fixture, never product memory. No terminal reply injection, SIP/DSP, analog or physical acceptance.')
 (output/'file-viewer-audit.json').write_text(json.dumps(result,indent=2)+'\n');return result
