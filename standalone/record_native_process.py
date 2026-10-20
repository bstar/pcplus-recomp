#!/usr/bin/env python3
"""Bind real DOS process results, exact native bytes and retained failed attempts."""
import argparse
import json
from pathlib import Path
import re

from build_native_process import ROOT,OUT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True)
    parser.add_argument('--retain-initial-failures',action='store_true',
                        help='bind the three locally retained initial process attempts')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    run=OUT/'runs'/args.label
    manifest=json.loads((OUT/'manifest.json').read_text())
    report=json.loads((run/'result.json').read_text())
    assert report['passed'] and report['checks']==678
    assert report['manifest_sha256']==sha(OUT/'manifest.json')==sha(run/'manifest.json')
    assert report['executable_sha256']==manifest['executable_sha256']==sha(OUT/'NATIVE.EXE')==sha(run/'NATIVE.EXE')
    assert report['checker_sha256']==sha(ROOT/'standalone/test_native_process_dos.py')
    for p,h in report['artifacts'].items():assert sha(run/p)==h,p
    for p,h in manifest['sources'].items():
        assert sha(ROOT/p)==sha(run/'sources'/p)==h,p
    for name,h in manifest['children'].items():assert sha(run/name)==h,name
    cases=[]
    for m in re.finditer(r'CASE (\S+) status=(\d+) child=(\d+) errno=(\d+) dos=(\d+) vectors=(\d+)',(run/'CHECKS.TXT').read_text()):
        cases.append(dict(path=m[1],status=int(m[2]),child_status=int(m[3]),crt_error=int(m[4]),dos_error=int(m[5]),changed_vectors=int(m[6])))
    assert len(cases)==20
    assert any(c['child_status']==0x307 for c in cases)
    assert any(c['path']=='CHILD.EXE' and c['child_status']==37 for c in cases)
    assert sum(c['path']=='EMPTY.COM' and c['child_status']==37 for c in cases)==2
    failed=[]
    for label in (('native-process-01','native-process-02','native-process-03') if args.retain_initial_failures else ()):
        folder=OUT/'runs'/label;path=folder/'result.json'
        old=json.loads(path.read_text());assert not old['passed']
        old_manifest=json.loads((folder/'manifest.json').read_text())
        assert old['manifest_sha256']==sha(folder/'manifest.json')
        for p,h in old_manifest['sources'].items():assert sha(folder/'sources'/p)==h,p
        failed.append(dict(label=label,passed=False,evidence={str(p.relative_to(ROOT)):sha(p) for p in (path,folder/'manifest.json',folder/'CHECKS.TXT')}))
    result=dict(passed=True,component_only=True,runtime_external_commands_enabled=False,
        whole_application_gates_closed=[],original_inputs=[],native_bytes=manifest['native_bytes'],
        units=manifest['units'],sources=manifest['sources'],
        actual_DOS=dict(assertions=report['checks'],cases=cases,
            evidence={str(p.relative_to(ROOT)):sha(p) for p in (run/'result.json',run/'manifest.json',run/'CHECKS.TXT',run/'CHILD.OUT',run/'EXE.OUT',run/'BATCH.OUT')}),
        retained_failed_attempts=failed,recorder_sha256=sha(Path(__file__)),
        checker_sha256=report['checker_sha256'],
        limitations=[
            'This core run exercises direct COM/EXE and native batch/COMSPEC; namespace coverage is recorded separately.',
            'No application display, WAIT/NOCLEAR or UART release/restore owner; no ASPECT runtime slots enabled.',
            'Six ordinary held CRT streams, live heap guards and patterned arena; not full ASPECT stream/lease/continuation acceptance.',
            'Native CRT platform state is separately owned in this component; production shared-state binding remains required.',
            'Source-owned heap padding, pointer admission and trap bracket are maintained adapters, not recovered native bytes.',
            'DOSBox-X8086 only; physical hardware and RS-232 Wi-Fi modem acceptance remain open.'])
    (ROOT/'docs/validation/native-process.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded 20 actual DOS process cases /678 assertions;',len(failed),'retained failed attempts; runtime slots remain unpublished.')


if __name__=='__main__':main()
