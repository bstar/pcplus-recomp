#!/usr/bin/env python3
"""Actual terminal child: roundtrip file attributes before gated login/resume."""
import json
from pathlib import Path
import test_aspect_renderer_dos as renderer
ROOT=renderer.ROOT;OUT=ROOT/'build/aspect-file-attributes-parent-dos'
def definitions():
 header=renderer.ESC+b'[2J'+renderer.ESC+b'[HFIRST BYTE SAFE'+renderer.QUERY+renderer.DA+b'LOGIN:'
 source='''string attrs
long size
proc main
waitfor "LOGIN:" 5
if waitfor
fopen 0 "ORIGNAME.BIN" "wb"
fputs 0 "parent"
fclose 0
getfsize "ORIGNAME.BIN" size
if failure
exit
endif
if size != 6L
exit
endif
rename "ORIGNAME.BIN" "NAMED.BIN"
if failure
exit
endif
isfile "NAMED.BIN"
if failure
exit
endif
findfirst "NAMED.BIN"
if found
strcmp $FILENAME "NAMED.BIN"
if failure
exit
endif
if $FSIZE != 6L
exit
endif
else
exit
endif
findnext
if found
exit
endif
setfattr "NAMED.BIN" "RHS"
getfattr "NAMED.BIN" attrs
if failure
exit
endif
strcmp attrs "RHS"
if failure
exit
endif
setfattr "NAMED.BIN" ""
getfattr "NAMED.BIN" attrs
strcmp attrs $NULL
if failure
exit
endif
transmit $D_PWORD
transmit "^M"
pause 1
endif
endproc
'''
 return [dict(name='attribute-login',source=source,banner=header,success=True,post=renderer.QUERY,post_reply=renderer.ESC+b'[1;22R',screen=[(0,0,'FIRST BYTE SAFE')])]
def main():
 renderer.OUT=OUT;renderer.definitions=definitions;status=renderer.main();folder=renderer.OUT
 report=json.loads((folder/'checks.json').read_text());case=report['cases'][0]
 # BEFORE/AFTER.BIN are also used by the passive observer. Use the script's
 # unique file names below so its product results cannot collide with probes.
 final=folder/case['case']/'NAMED.BIN';old=folder/case['case']/'ORIGNAME.BIN'
 case['checks']['queried_renamed_file']=final.is_file() and final.read_bytes()==b'parent' and not old.exists()
 report.update(passed=status==0 and all(case['checks'].values()),checker_sha256=renderer.sha(Path(__file__)),reused_renderer_sha256=renderer.sha(Path(renderer.__file__)),scope='Actual production terminal/ASPECT, native attributes/global writeback/enumeration/query/rename and parent callback/UART/keyboard restoration. Password sent only after size/existence/rename success. Owned files and modeled modem, no physical claim.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('File-attributes parent',report['passed']);return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
