#!/usr/bin/env python3
"""Admit retry synchronization on current normal/mouse products with retained failure evidence."""
import argparse, difflib, json, shutil
from pathlib import Path
import audit_manual_cancel_retained as baseline_audit
from audit_modem_resync_candidate import verify
from audit_aspect_transmit_wait import ROOT, sha, read


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','retained','cleared','source-proof','normal-linked','mouse-linked','reconnect-linked','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    for name,value in vars(a).items():setattr(a,name,value.resolve())
    assert not a.cohort.exists() and not a.output.exists()
    assert a.cohort.resolve().is_relative_to(ROOT/'build') and a.output.resolve().is_relative_to(ROOT/'docs/validation')
    old=baseline_audit.verify(a.baseline.resolve());backend=read(a.baseline/'checks.json')['emulator'];rows=[]
    for folder,policy in [(a.retained,'retained'),(a.cleared,'cleared')]:
        r,cases=verify(folder.resolve(),policy,backend);rows+=cases
        for name,digest in r['inputs'].items():assert sha(ROOT/name)==digest,name
    proof=read(a.source_proof);assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==2
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==digest,name
    products={}
    for name,model in [('terminal',a.normal_linked),('terminal-mouse',a.mouse_linked)]:
        manifest=read(ROOT/'build'/name/'manifest.json');binary=ROOT/'build'/name/'TERMINAL.EXE'
        digest=sha(binary);assert digest==manifest['binary_sha256']==proof['products'][name]
        linked=read(model);assert linked['passed'] and len(linked['cases'])==17 and all(c['passed'] for c in linked['cases'])
        assert linked['parent_sha256']==digest and linked['checker_sha256']==sha(ROOT/'standalone/check_modem_resync.py')
        for source,h in manifest['sources'].items():assert sha(ROOT/source)==h
        products[name]=digest
    assert r['parent_sha256']==products['terminal']!=old['parent_sha256']
    linked=read(a.reconnect_linked);assert linked['passed'] and linked['parent_sha256']==products['terminal'] and len(linked['cases'])==4
    for case in linked['cases']:
        expected=(b'\r' if case['case'].startswith('cancel-init-') else b'')+b'ATZ\rATDLocal.Example:2323\r'
        assert case['passed'] and case['retry_state']==5 and bytes.fromhex(case['retry_wire_hex'])==expected
    patch=''
    for name in ('src/terminal/connection.asm','src/terminal/modem_sender.asm'):
        patch+=''.join(difflib.unified_diff((a.baseline/'inputs'/name).read_text().splitlines(True),(ROOT/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    assert patch==(ROOT/'patches/modem-retry-resync.patch').read_text()
    a.cohort.mkdir(parents=True)
    for path in [a.baseline,a.retained,a.cleared,a.source_proof.parent,a.normal_linked,a.mouse_linked,a.reconnect_linked,Path(__file__),ROOT/'standalone/audit_modem_resync_candidate.py',ROOT/'standalone/audit_manual_cancel_retained.py']:
        path=path.resolve();dest=a.cohort/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
        if path.is_dir():shutil.copytree(path,dest)
        else:shutil.copy2(path,dest)
    files={str(path.relative_to(a.cohort)):sha(path) for path in a.cohort.rglob('*') if path.is_file()}
    (a.cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,retry_synchronization_component_accepted=True,full_application_accepted=False,physical_hardware_accepted=False,baseline_parent_sha256=old['parent_sha256'],products=products,cases=rows,linked_cases=34,manual_reconnect_cases=4,source_products=2,emulator=backend,cohort=str(a.cohort.relative_to(ROOT)),files_manifest_sha256=sha(a.cohort/'files.json'),patch_sha256=sha(ROOT/'patches/modem-retry-resync.patch'),auditor_sha256=sha(Path(__file__)),scope=__doc__+' Four independently audited actual DOS retained/cleared-parser cases on explicit patched DCD lab, current-source/product binding and byte-identical fresh normal/mouse builds. Configured initialization remains unchanged after a separately paced retry terminator. The separately documented stock modem-parser comparison supports that specific software behavior. Other carrier/DTR/init-result policies, full application and physical Boca/SPA2102 validation remain open.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,DOS_cases=len(rows),linked_cases=34,source_products=2)))


if __name__=='__main__':main()
