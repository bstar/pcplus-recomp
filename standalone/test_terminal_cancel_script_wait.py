#!/usr/bin/env python3
"""Exercise the serviced script-return wait after a real missing-child EXEC."""
import json,sys,uuid
from pathlib import Path
import test_terminal_cancel_dos as base

def main():
    if '--label' not in sys.argv:sys.argv+=['--label','script-wait-'+uuid.uuid4().hex]
    base.CASES={'script-return':('return','p2000 a-z p300 a p300 m i s s i n g . a s x enter',None)}
    result=base.main()
    # Freeze this explicit scenario adapter alongside the unchanged core
    # harness's own snapshot. No application resource or reply is supplied.
    label=sys.argv[sys.argv.index('--label')+1]
    folder=base.ROOT/'build/terminal-cancel-tests'/label
    target=folder/'sources/standalone/test_terminal_cancel_script_wait.py'
    target.write_bytes(Path(__file__).read_bytes())
    receipt=json.loads((folder/'result.json').read_text())
    receipt['script_wait_adapter_sha256']=base.sha(Path(__file__))
    (folder/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return result

if __name__=='__main__':raise SystemExit(main())
