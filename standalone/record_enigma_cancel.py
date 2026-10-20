#!/usr/bin/env python3
"""Publish sanitized cancellation, retry, cleanup and source rebuild evidence."""
import argparse,json,re
from datetime import date
from pathlib import Path
from build_native_mouse import ROOT,sha


def read(path):return json.loads(path.read_text())
def current(sources):
    for p,h in sources.items():
        assert not Path(p).is_absolute() and '..' not in Path(p).parts and sha(ROOT/p)==h,p


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('label','repeat-label','source-label','timeout-label','repeat-audit-label','package-label'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    for value in (args.label,args.repeat_label,args.source_label,args.timeout_label,args.repeat_audit_label,args.package_label):assert re.fullmatch(r'[A-Za-z0-9_-]+',value)
    normal=ROOT/'build/terminal/TERMINAL.EXE';digest=sha(normal);evidence=[]
    reports={}
    for leaf in ('terminal-zmodem-live-checks.json','terminal-transfer-live-checks.json','terminal-ymodem-live-checks.json','zmodem-owners-live-checks.json','zmodem-cancel-checks.json'):
        path=normal.parent/leaf;r=read(path)
        assert r['passed'] and r['binary_sha256']==digest and all(c['passed'] for c in r['cases'])
        reports[leaf]=dict(inputs=r.get('inputs',len(r['cases'])),cases=r['cases']);evidence.append(path)
    assert reports['terminal-zmodem-live-checks.json']['inputs']==78
    cancel=read(normal.parent/'zmodem-cancel-checks.json')
    assert cancel['checker_sha256']==sha(ROOT/'standalone/check_terminal_zmodem_cancel.py')
    assert {r['case'] for r in cancel['cases']}=={'quiet','late','continuous','quiet-upload','clock-jump'}
    assert next(c for c in cancel['cases'] if c['case']=='late')['late_bursts']==2
    assert next(c for c in cancel['cases'] if c['case']=='continuous')['elapsed_modeled_ticks']>=180
    assert next(c for c in cancel['cases'] if c['case']=='clock-jump')['elapsed_modeled_ticks']>=65536
    clock_path=normal.parent/'cancel-clock-counterexample.json';clock_counter=read(clock_path)
    assert clock_counter['reproduced'] and clock_counter['quit']==0 and clock_counter['exit_code']==0
    old_proof_dir=ROOT/'build/aspect-unwind-mouse/source-proofs/enigma-cancel-source-02'
    assert clock_counter['binary_sha256']==sha(old_proof_dir/'source/build/terminal/TERMINAL.EXE')
    evidence += [clock_path,old_proof_dir/'result.json']
    folder=ROOT/'build/bbs-lab/results/enigma'/args.label
    bbs=read(folder/'cancel-checks.json');negative=read(folder/'cancel-audit-negative-checks.json')
    assert bbs['passed'] and all(bbs['checks'].values()) and not bbs['errors'] and bbs['terminal_sha256']==digest
    assert bbs['server_exit_codes'][0]!=0 and bbs['server_exit_codes'][1]==0
    assert bbs['snapshots'] and bbs['snapshots'][0]['files']=={}
    assert bbs['input_hashes']['runner']==sha(ROOT/'lab/bbs/enigma_cancel_download_dos.py')
    assert bbs['input_hashes']['harness']==sha(ROOT/'lab/bbs/test_dos.py')
    assert bbs['input_hashes']['auditor']==negative['auditor_sha256']==sha(ROOT/'lab/bbs/audit_zmodem.py')
    candidate=args.candidate.resolve();assert candidate.is_relative_to(ROOT/'build')
    fixture=read(candidate/'search-instance.json');assert fixture['transfer_bytes']==32768
    for p,h in {**fixture['fixture_inputs'],**fixture['source_modules']}.items():
        assert sha(candidate/p)==h==bbs['input_hashes'][p]
    assert negative['passed'] and len(negative['cases'])>=11 and all(c['rejected'] for c in negative['cases'])
    assert negative['checker_sha256']==sha(ROOT/'lab/bbs/check_enigma_cancel_audit.py')
    for p,h in negative['capture_hashes'].items():assert sha(folder/p)==h
    evidence += [folder/'cancel-checks.json',folder/'cancel-audit-negative-checks.json']
    repeat_dir=folder.parent/args.repeat_label;repeat=read(repeat_dir/'cancel-checks.json')
    assert repeat['passed'] and all(repeat['checks'].values()) and not repeat['errors']
    assert repeat['terminal_sha256']==digest and repeat['input_hashes']==bbs['input_hashes']
    assert repeat['server_exit_codes'][0]!=0 and repeat['server_exit_codes'][1]==0
    evidence.append(repeat_dir/'cancel-checks.json')
    regression_path=folder.parent/args.repeat_audit_label/'audit-negative-checks.json';regression=read(regression_path)
    assert regression['passed'] and len(regression['cases'])==7 and all(c['rejected'] for c in regression['cases'])
    assert regression['checker_sha256']==sha(ROOT/'lab/bbs/check_enigma_repeat_audit.py')
    for p,h in regression['capture_hashes'].items():assert sha(regression_path.parent/p)==h
    evidence.append(regression_path)
    timeout_path=ROOT/'build/bbs-lab/results/harness'/args.timeout_label/'timeout-checks.json';timeout=read(timeout_path)
    assert timeout['passed'] and all(timeout['checks'].values())
    assert timeout['harness_sha256']==sha(ROOT/'lab/bbs/test_dos.py')
    assert timeout['checker_sha256']==sha(ROOT/'lab/bbs/check_dos_harness_timeout.py')
    evidence.append(timeout_path)
    proof_dir=ROOT/'build/aspect-unwind-mouse/source-proofs'/args.source_label;proof=read(proof_dir/'result.json')
    assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==31
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_aspect_unwind_source.py')
    assert proof['log_sha256']==sha(proof_dir/'build.log');current(proof['sources'])
    for p,h in proof['sources'].items():assert sha(proof_dir/'source'/p)==h
    for p,r in proof['products'].items():assert r['actual']==r['expected']==sha(ROOT/'build'/p)==sha(proof_dir/'source/build'/p)
    preceding=read(ROOT/'docs/validation/mouse-settings.json')['products']
    changed={p for p,r in proof['products'].items() if r['actual']!=preceding[p]}
    assert changed=={p+'/TERMINAL.EXE' for p in ('terminal','terminal-process','terminal-mouse','terminal-mouse-process')}
    layouts={}
    for p in sorted(changed):
        manifest_path=(ROOT/'build'/p).parent/'manifest.json';manifest=read(manifest_path)
        assert manifest['binary_sha256']==proof['products'][p]['actual'];current(manifest['sources'])
        memory=manifest['memory_layout'];assert memory['resident_code_bytes']<65536 and memory['near_bytes']<65536
        layouts[p]={k:memory[k] for k in ('resident_code_bytes','resident_code_spare_bytes','near_bytes','near_spare_bytes')}
        evidence.append(manifest_path)
    evidence += [proof_dir/'result.json',proof_dir/'build.log']
    packages={}
    for name,terminal in [('dos-package','terminal'),('dos-package-mouse','terminal-mouse')]:
        package_dir=ROOT/'build'/name;manifest=read(package_dir/'manifest.json')
        assert manifest['original_inputs']==[] and len(manifest['files'])==10
        current(manifest['sources'])
        assert all(sha(package_dir/p)==h for p,h in manifest['files'].items())
        assert manifest['files']['TERMINAL.EXE']==proof['products'][terminal+'/TERMINAL.EXE']['actual']
        packages[name]=manifest['files'];evidence.append(package_dir/'manifest.json')
    package_test_path=ROOT/'build/package-mouse-tests'/args.package_label/'result.json';package_test=read(package_test_path)
    assert package_test['passed'] and all(package_test['checks'].values())
    assert package_test['checker_sha256']==sha(ROOT/'standalone/test_package_mouse.py')
    assert package_test['package_manifest_sha256']==sha(ROOT/'build/dos-package-mouse/manifest.json')
    evidence.append(package_test_path)
    failed=[]
    for label in ('owned-cancel-02','owned-cancel-03','owned-cancel-04','owned-cancel-05'):
        path=folder.parent/label/'cancel-checks.json';r=read(path);assert not r['passed']
        failed.append(dict(label=label,checks=r['checks'],errors=r['errors'],terminal_sha256=r['terminal_sha256']))
        evidence.append(path)
    interrupted=folder.parent/'owned-cancel-01/interrupted-run.json';failed.append(dict(label='owned-cancel-01',**read(interrupted)));evidence.append(interrupted)
    report=dict(date=date.today().isoformat(),passed=True,whole_application_gates_closed=[],
        isolated_ENIGMA=dict(checks=bbs['checks'],repeat_checks=repeat['checks'],sessions=2,archive_bytes=bbs['archive_bytes'],wire_name=bbs['wire_name'],local_name=bbs['local_name'],server_exit_codes=bbs['server_exit_codes']),
        linked_regressions=reports,capture_corruptions_rejected=len(negative['cases']),preceding_repeat_audit_corruptions_rejected=7,
        harness_timeout=dict(checks=timeout['checks'],seconds=timeout['seconds']),
        source_products={p:r['actual'] for p,r in proof['products'].items()},unchanged_products=27,
        changed_terminal_products=sorted(changed),layouts=layouts,source_hashes=proof['sources'],original_build_inputs=[],packages=packages,
        retained_failed_runs=failed,retained_clock_counterexample=clock_counter,
        evidence=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in evidence],
        recorder_sha256=sha(Path(__file__)),nix_inputs={p:sha(ROOT/p) for p in ('nix/flake.nix','nix/flake.lock')},
        test_sources={p:sha(ROOT/p) for p in ('lab/bbs/enigma_cancel_download_dos.py','lab/bbs/zmodem_cancel_watch.py','lab/bbs/zmodem_label_watch.py','lab/bbs/test_dos.py','lab/bbs/test_transfer_dos.py','lab/bbs/modem.py','lab/bbs/audit_zmodem.py','lab/bbs/check_enigma_cancel_audit.py','lab/bbs/check_dos_harness_timeout.py','lab/bbs/enigma_search_fixture.py')},
        limitations=['Isolated staged ENiGMA decoder and generated archive; live server is unchanged.',
            'Modem/UART timing is modeled at19200/HARD; physical Wi-Fi modem acceptance remains open.',
            'A continuous binary stream beyond180 BIOS ticks exits with status14; it does not return to the ANSI parser.',
            'The 31-product source proof is not full application acceptance. Earlier mouse/UI and ASPECT workflow receipts identify their own binaries.'])
    with args.output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(args.output)


if __name__=='__main__':main()
