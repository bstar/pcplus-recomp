#!/usr/bin/env python3
"""Explicit analyst comparison/provenance refresh; ordinary builds never run this."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
EVIDENCE='ev_569fc63c4a44ed77abaf3a0282ecdf4f47fc71a15851e3c4e72dcaa2db68f520'
def main():
 raw=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
 source=ROOT/'reconstruction/substitute_control/substitute.asm';blob=raw[0x2448:0x247d];assert len(blob)==53
 with tempfile.TemporaryDirectory()as work:
  target=Path(work)/'substitute.bin';subprocess.run(['nasm','-fbin',str(source),'-o',str(target)],check=True);assert target.read_bytes()==blob
 manifest=dict(source_sha256=EXPECTED,units=[dict(file=str(source.relative_to(ROOT)),start=0x1248,end=0x127d,source_file_offset=0x2448,bytes=53,instructions=21,sha256=hashlib.sha256(blob).hexdigest(),matched_original=True)],
  rea_evidence=EVIDENCE,analysis_artifact_sha256='89b73614735f46dabb0554fece9afde77e4101cc3676227eb9894311c7eadbf8',
  state={'1d18':'csi_terminal_id','9056':'render_direct_output','9026':'terminal_control_mode_9026','9020':'terminal_newline_mode_9020'},
  services={'bb77':'terminal_substitute_profile_ge20','ba4b':'terminal_formfeed_profile_6_7','1efc':'screen_cursor_up','1e0c':'screen_cursor_down'},
  limitations=['REA used a static-only copy with its header entry set to1248; original code bytes were unchanged and the copy is never executed.','Ghidra reports51 body bytes in a53-byte span, omitting two padding NOPs. Assembly is authoritative for the near/caller-cleaned ABI; pseudocode is not original source.','Profile>=20 calls an unresolved overlay provider with argument59. Supported application profiles4/6 use the recovered return/clear/up/down branches. Signed native profile comparison is preserved.'])
 (source.parent/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Matched53 original SUB bytes')
if __name__=='__main__':main()
