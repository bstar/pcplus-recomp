#!/usr/bin/env python3
"""Real terminal login child owns files through success, native error and Escape."""
import json
from pathlib import Path
import test_aspect_renderer_dos as renderer
ROOT=renderer.ROOT;OUT=ROOT/'build/aspect-script-files-parent-dos'
def definitions():
 header=renderer.ESC+b'[2J'+renderer.ESC+b'[HFIRST BYTE SAFE'+renderer.QUERY+renderer.DA+b'LOGIN:'
 common='proc main\nwaitfor "LOGIN:" 5\nif waitfor\nfopen 0 "{file}" "wb"\nif failure\nexit\nendif\nfputs 0 "{text}"\n'
 success=common.format(file='PARENT.BIN',text='parent')+'transmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'
 error='integer result,zero\n'+common.format(file='ERROR.BIN',text='error')+'result=1/zero\nendif\nendproc\n'
 cancel=common.format(file='CANCEL.BIN',text='cancelled')+'waitfor "NEVER" 12\nendif\nendproc\n'
 return [dict(name='file-login',source=success,banner=header,success=True,post=renderer.QUERY,post_reply=renderer.ESC+b'[1;22R',screen=[(0,0,'FIRST BYTE SAFE')]),dict(name='file-error',source=error,banner=header,success=False,screen=[]),dict(name='file-cancel',source=cancel,banner=header,success=False,cancel=True,screen=[])]
def main():
 renderer.OUT=OUT;renderer.definitions=definitions;result=renderer.main();folder=renderer.OUT;report=json.loads((folder/'checks.json').read_text())
 expected={'file-login':('PARENT.BIN',b'parent'),'file-error':('ERROR.BIN',b'error'),'file-cancel':('CANCEL.BIN',b'cancelled')}
 for case in report['cases']:
  name,data=expected[case['case']];path=folder/case['case']/name
  case['checks']['owned_file_flushed_before_parent_return']=path.is_file() and path.read_bytes()==data
  case['passed']=all(case['checks'].values());(folder/case['case']/'result.json').write_text(json.dumps(case,indent=2)+'\n')
 report.update(passed=result==0 and all(c['passed'] for c in report['cases']),checker_sha256=renderer.sha(Path(__file__)),reused_renderer_checker_sha256=renderer.sha(Path(renderer.__file__)),files={k:dict(name=v[0],bytes=len(v[1]),sha256=renderer.sha(folder/k/v[0])) for k,v in expected.items()},scope='Actual terminal and production ASPECT login child with file left open on normal return, divide error and BIOS Escape during WAITFOR. Exact flushed files, later parent keyboard, JFT/sink/history/device/interrupt restoration through passive observer. Owned mapped test files and controlled modem; no physical hardware claim.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('ASPECT file parent:',len(report['cases']),'cases',report['passed']);return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
