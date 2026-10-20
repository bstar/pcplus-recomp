#!/usr/bin/env python3
"""Build the actual ASPECT CLI with a controlled foreground-ownership probe."""
import json
from pathlib import Path
import build_aspect_process as process
ROOT=process.ROOT;OUT=ROOT/'build/aspect-exit-break';sha=process.sha
def main():
    process.main(ROOT/'standalone/aspect_exit_driver.c',output=OUT,break_owner=True)
    manifest=json.loads((OUT/'manifest.json').read_text())
    manifest['sources'][str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    manifest['scope']='Actual banked ASPECT CLI and exit guard; controlled timer mutates INT1B during real RUN WAIT. Callback/code retention tested by independent recovered EXEC parent after process exit.'
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
