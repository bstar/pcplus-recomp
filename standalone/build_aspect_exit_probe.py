#!/usr/bin/env python3
"""Build the actual ASPECT CLI with a controlled foreground-ownership probe."""
import argparse,json
from pathlib import Path
import build_aspect_process as process
ROOT=process.ROOT;OUT=ROOT/'build/aspect-exit-break';sha=process.sha
def main(attached=False):
    global OUT
    OUT=ROOT/('build/aspect-exit-parent' if attached else 'build/aspect-exit-break')
    process.main(ROOT/'standalone/aspect_exit_driver.c',output=OUT,parent_render=attached,break_owner=True)
    manifest=json.loads((OUT/'manifest.json').read_text())
    manifest['sources'][str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    manifest['exit_probe_attached']=attached
    manifest['scope']='Actual banked ASPECT CLI and exit guard; controlled timer mutates INT1B during real RUN WAIT. '+('Attached terminal observes retained MCBs, invokes the known test callback and resumes serial I/O.' if attached else 'Callback/code retention tested by independent recovered EXEC parent after process exit.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--attached',action='store_true')
    main(parser.parse_args().attached)
