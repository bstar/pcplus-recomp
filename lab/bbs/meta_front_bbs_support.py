"""Passive Meta/editor round trip; no product-memory writes or terminal injection."""
import json,struct,subprocess
from pathlib import Path
from product_inputs import ROOT,sha
SOURCES=['lab/bbs/meta_front_bbs_support.py','standalone/file_directory_bbs_watch.asm']
# Accepted memory-only edit. No Save and no Alt-1 emission into the BBS draft.
KEYS='a-m p2200 r enter Z Z Z enter p1000 escape p1500 '
def prepare(folder,binary):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_meta_editor']
 assert not binary.with_name('PCPLUS.KEY').exists(),'Use an owned build with no preexisting KEY selector'
 observer=folder/'METAW.COM'
 subprocess.run(['nasm','-fbin','-DMETA_KEYS_ROUNDTRIP',str(ROOT/SOURCES[1]),'-o',str(observer)],check=True)
 return observer

def audit(output,binary):
 output=Path(output);path=output/'METAVIEW.BIN';raw=path.read_bytes()if path.exists()else b''
 words=struct.unpack_from('<12H',raw)if len(raw)==12024 else None
 before,after,dialog=raw[24:4024],raw[4024:8024],raw[8024:12024]
 wire=(output/'serial-received.bin').read_bytes()
 checks=dict(observer_complete=words is not None and words[:4]==(0x5657,1,1,1),
  exact_editor_frame=words is not None and before==after,
  editor_cursor_shape=words is not None and words[6]==words[7] and words[8]==words[9],
  actual25_rows=words is not None and words[4:6]==(25,25),mode_preserved=words is not None and words[10:12]==(0x5003,0x5003),
  actual_Meta_heading=dialog[520:542:2]==b' META KEYS ',
  accepted_local_definition=dialog[1010:1016:2]==b'ZZZ',
  local_edit_never_reached_BBS=b'ZZZ'not in wire,
  subsequent_editor_keys=b'ABCDE'in wire and b'UNSAVED'in wire,
  no_implicit_disk_save=not binary.with_name('PCPLUS.KEY').exists() and not(output/'PCPLUS.KEY').exists())
 result=dict(passed=all(checks.values()),checks=checks,observer_words=words,binary_sha256=sha(binary),capture_sha256=sha(path)if path.exists()else None,
  sources={n:sha(ROOT/n)for n in SOURCES},scope='Actual Alt-M, accepted local definition and Escape within a stock unsaved BBS editor. Passive full4000-byte frame/cursor/shape return and resumed ordinary editing. Memory-only edit, no Save or adopted-key emission into the BBS draft. No physical UART/CTS, SIP/audio or native pixel-equivalence claim.')
 (output/'meta-front-audit.json').write_text(json.dumps(result,indent=2)+'\n');return result
