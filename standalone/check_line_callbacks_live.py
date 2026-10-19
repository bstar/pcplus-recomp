#!/usr/bin/env python3
"""Current-source-only line callback checks; no historical executable required."""
import json
from pathlib import Path
from check_line_controller_far import check_callbacks,sha,ROOT

def main():
 count=check_callbacks();assert count==24
 report=dict(passed=True,binary_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),cases=count,
  checker_sha256=sha(Path(__file__)),mechanics_sha256=sha(ROOT/'standalone/check_line_controller_far.py'),original_inputs=[],
  scope='Current linked image only. Six declared register-only callbacks, two FLAGS inputs and empty/nonempty receive. Actual native return observation requires exact general-register/FLAGS propagation through each far callback; direct near calls independently verify state/BIOS effects and declared scalar/callee results. No previous executable, original or install data read.')
 (ROOT/'build/terminal/line-callback-live-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Line callbacks:',count,'current-source-only native return/FLAGS cases PASS')
if __name__=='__main__':main()
