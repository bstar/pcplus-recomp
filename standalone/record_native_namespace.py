#!/usr/bin/env python3
"""Bind actual DOS namespace, SYSTEM policy and nested allocation evidence."""
import argparse
import json
from pathlib import Path
import re

from build_native_process import ROOT,OUT,sha


def checked_run(label,namespace,assertions):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    folder=OUT/'runs'/label
    report=json.loads((folder/'result.json').read_text())
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert report['passed'] and not report['timed_out']
    assert report['namespace']==namespace and report['checks']==assertions
    assert report['manifest_sha256']==sha(folder/'manifest.json')==sha(OUT/'manifest.json')
    name='NAMES.EXE' if namespace else 'NATIVE.EXE'
    key='namespace_sha256' if namespace else 'executable_sha256'
    assert report['executable']==name
    assert report['executable_sha256']==manifest[key]==sha(folder/name)==sha(OUT/name)
    assert report['checker_sha256']==sha(ROOT/'standalone/test_native_process_dos.py')
    for p,h in report['artifacts'].items():assert sha(folder/p)==h,p
    for p,h in manifest['sources'].items():assert sha(ROOT/p)==sha(folder/'sources'/p)==h,p
    for p,h in manifest['children'].items():assert sha(folder/p)==h,p
    return folder,report,manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True)
    parser.add_argument('--core-label',required=True)
    parser.add_argument('--collision-label',help='optional retained initial CHECK.BAT collision')
    args=parser.parse_args()
    folder,report,manifest=checked_run(args.label,True,2053)
    core,core_report,_=checked_run(args.core_label,False,678)
    text=(folder/'CHECKS.TXT').read_text()
    rows=[]
    pattern=r'^CASE (.*?) status=(\d+) child=(\d+) errno=(\d+) dos=(\d+) vectors=(\d+) route=(\d+)$'
    for m in re.finditer(pattern,text,re.M):
        rows.append(dict(path=m[1],status=int(m[2]),child_status=int(m[3]),
            crt_error=int(m[4]),dos_error=int(m[5]),changed_vectors=int(m[6]),route=int(m[7])))
    assert len(rows)==55 and sum(r['route']==0 for r in rows)==20
    assert [r['child_status'] for r in rows if r['path']=='PRIOR']==[17,37,0]
    assert [r['child_status'] for r in rows if r['path']=='PICK']==[17,21,22]
    assert [r['status'] for r in rows if r['path']=='ENVCHK']==[0,0,4,4,4,4]
    assert [r['child_status'] for r in rows if r['path']=='<query>']==[0,0,1]
    assert 'NAMESPACE maximum live allocations=3 owned after tests=0' in text
    markers={}
    for name,value in [('SYSTEM.OUT',b'SYSPASS'),('FALL.OUT',b'FALLBACK'),
            ('DENIED.OUT',b'DENIED'),('NOCSPEC.OUT',b'NOCOMSPEC'),
            ('RECOVER.OUT',b'RECOVER'),('PRIOR.OUT',b'PRIORITY')]:
        assert (folder/name).read_bytes().rstrip(b'\r\n')==value,name
        markers[name]=sha(folder/name)
    assert not (folder/'NEVER.OUT').exists() and not (folder/'OOM.OUT').exists()
    result=dict(passed=True,component_only=True,runtime_external_commands_enabled=False,
        whole_application_gates_closed=[],original_inputs=[],native_bytes=manifest['native_bytes'],
        added_native_bytes=manifest['native_bytes']-1393,units=manifest['units'],sources=manifest['sources'],
        DOS=dict(cases=len(rows),assertions=report['checks'],rows=rows,marker_sha256=markers,
            maximum_live_allocations=3,remaining_owned_allocations=0,
            evidence={str(p.relative_to(ROOT)):sha(p) for p in (folder/'result.json',folder/'manifest.json',folder/'CHECKS.TXT')}),
        core_regression=dict(assertions=core_report['checks'],
            evidence={str(p.relative_to(ROOT)):sha(p) for p in (core/'result.json',core/'CHECKS.TXT')}),
        recorder_sha256=sha(Path(__file__)),checker_sha256=report['checker_sha256'],
        maintained_adapters=['Linked ownership list for nested native name/PATH/environment allocations.',
            'Explicit native ENOMEM12/DOS8 translation from Watcom allocator failure.',
            'Batch size admission before the native unchecked prefix copy.',
            'NULL access guard for command-processor availability query.',
            'Typed rejection of the unadmitted overlay/load-and-go mode.'],
        limitations=['No production shared-state, display/WAIT/NOCLEAR or UART ownership; no runtime slots published.',
            'Native PATH quirks retained: a leading empty component stops search; no shell quoting is invented.',
            'Invalid executable-format coverage and full ASPECT continuation/lease/handler integration remain open.',
            'Modeled DOSBox-X8086, not physical hardware or RS-232 Wi-Fi modem acceptance.'])
    if args.collision_label:
        assert re.fullmatch(r'[A-Za-z0-9_-]+',args.collision_label)
        old=OUT/'runs'/args.collision_label
        source=old/'sources/standalone/native_namespace_cases.inc'
        old_manifest=json.loads((old/'manifest.json').read_text())
        assert sha(source)==old_manifest['sources']['standalone/native_namespace_cases.inc']
        assert 'namespace_case("CHECK"' in source.read_text()
        assert (old/'CHECK.BAT').is_file() and not (old/'result.json').exists()
        redirects=(old/'dosbox.log').read_text().count('Redirect output to CHECKS.TXT')
        assert redirects>=2
        result['retained_incomplete_attempt']=dict(passed=False,completed_report_present=False,
            outcome='Observed30-second subprocess timeout after CHECK selected the harness CHECK.BAT recursively.',
            evidence={str(p.relative_to(ROOT)):sha(p) for p in (old/'manifest.json',source,old/'CHECK.BAT',old/'dosbox.log')},
            repeated_harness_redirections=redirects,
            correction='Use ENVCHK as target, PCPTEST.BAT as harness, unbuffered assertions and a fresh run.')
    (ROOT/'docs/validation/native-process-namespace.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded55 DOS namespace/core cases /2053 assertions plus separate678-assertion core regression; application gates remain open.')


if __name__=='__main__':main()
