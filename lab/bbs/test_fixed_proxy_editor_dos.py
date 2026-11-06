#!/usr/bin/env python3
"""Reuse the actual Enigma editor harness with explicit PRM geometry and no size probe."""
import hashlib,json,sys
from pathlib import Path

def main():
 root=Path(__file__).resolve().parents[2];source=root/'lab/bbs/test_synthmodem_proxy_dos.py'
 # The maintained flag supplies valid explicit imported display preferences;
 # this adapter independently disables only the bridge's pre-session query.
 assert '--size-probe' in sys.argv and '--label' in sys.argv
 label=sys.argv[sys.argv.index('--label')+1]
 before=hashlib.sha256(source.read_bytes()).hexdigest();own=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 text=source.read_text()
 replacements={"(['--probe-terminal-size'] if args.size_probe else [])":"[]", "size_probe_requested=not args.size_probe or ready['terminalSizeProbe']":"fixed_bridge_no_size_probe=not ready.get('terminalSizeProbe',False)"}
 for old,new in replacements.items():assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new,1)
 namespace={'__file__':str(source),'__name__':'fixed_geometry_editor_harness'}
 exec(compile(text,str(source),'exec'),namespace);status=namespace['main']();assert status==0
 assert hashlib.sha256(source.read_bytes()).hexdigest()==before and hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==own
 out=root/'build/bbs-lab/results/enigma'/label;r=json.loads((out/'proxy-integration.json').read_text())
 assert r['passed'] and r['checks']['fixed_bridge_no_size_probe'] and not r['bridge']['terminalSizeProbe']
 result=dict(passed=True,binary_sha256=r['binary_sha256'],sources={'lab/bbs/test_fixed_proxy_editor_dos.py':own,'lab/bbs/test_synthmodem_proxy_dos.py':before},scope=__doc__+' Only the size-probe command switch and its corresponding expectation are adapted. Actual DOS fields, stock authentication/editor/child, UART, protocol and frame audits execute the maintained implementation. No fabricated reports, private config, live service or physical acceptance.')
 (out/'fixed-geometry-adapter.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
