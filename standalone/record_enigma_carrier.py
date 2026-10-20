#!/usr/bin/env python3
"""Record current DOS carrier recovery, bounded receive credit and strict finish."""
import argparse,json,re,shutil
from datetime import date
from pathlib import Path
from build_native_mouse import ROOT,sha


def read(path):return json.loads(path.read_text())
def current(sources):
    for p,h in sources.items():
        assert not Path(p).is_absolute() and '..' not in Path(p).parts and sha(ROOT/p)==h,p


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('carrier-label','cancel-label','source-label','relay-label','package-label','repeat-audit-label'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--server-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    for name,value in vars(args).items():
        if name.endswith('_label'):assert re.fullmatch(r'[A-Za-z0-9_-]+',value)
    binary=ROOT/'build/terminal/TERMINAL.EXE';digest=sha(binary);evidence=[];reports={}
    for name,count in [('terminal-zmodem-live-checks.json',78),('zmodem-cancel-checks.json',5),('zmodem-name-ui-checks.json',17)]:
        path=binary.parent/name;r=read(path);assert r['passed'] and r['binary_sha256']==digest and len(r['cases'])==count
        if name=='zmodem-name-ui-checks.json':assert all(c['passed'] if 'passed' in c else c['visible'] and c['restored'] for c in r['cases'])
        else:assert all(c['passed'] for c in r['cases'])
        reports[name]=dict(cases=count);evidence.append(path)
    for name,field,count in [('zmodem-session','scripted_checks',92),('zmodem-dos','DOS_cases',68),('zmodem-window','inputs',79),('zmodem-names','cases',446)]:
        path=ROOT/'build'/name/'checks.json';r=read(path);assert r['passed'] and r[field]==count;current(r['sources'])
        if name=='zmodem-dos':assert r['isolated_source_build_byte_identical'] and r['binary_sha256']==sha(path.parent/'SESSION.EXE')
        reports[name]=dict(cases=count);evidence.append(path)
    root=ROOT/'build/bbs-lab/results/enigma';folder=root/args.carrier_label
    result=read(folder/'carrier-checks.json');negative=read(folder/'carrier-audit-negative-checks.json')
    assert result['passed'] and all(result['checks'].values()) and not result['errors'] and result['terminal_sha256']==digest
    assert result['checks']['confirmed_finish_notice'] and not any('unconfirmed' in n for n in result['notices'])
    assert result['snapshots'][0]['bytes']>=1024 and result['snapshots'][1]['files']==[]
    assert negative['passed'] and len(negative['cases'])>=12 and all(c['rejected'] for c in negative['cases'])
    assert negative['checker_sha256']==sha(ROOT/'lab/bbs/check_enigma_carrier_audit.py')
    assert negative['auditor_sha256']==sha(ROOT/'lab/bbs/audit_zmodem.py')
    for p,h in negative['capture_hashes'].items():assert sha(folder/p)==h
    for key,p in [('runner','enigma_carrier_dos.py'),('relay','carrier_relay.py'),('observer','carrier_notice_watch.py')]:assert result['input_hashes'][key]==sha(ROOT/'lab/bbs'/p)
    candidate=args.candidate.resolve();assert candidate.is_relative_to(ROOT/'build');fixture=read(candidate/'search-instance.json')
    for p,h in {**fixture['fixture_inputs'],**fixture['source_modules']}.items():assert sha(candidate/p)==h==result['input_hashes'][p]
    for p,h in fixture['source_inputs'].items():assert sha(args.server_root/p)==h
    from sys import path as module_path
    module_path.insert(0,str(ROOT/'lab/bbs'))
    from audit_zmodem import scan
    credits=[]
    for i in (1,2):
        session=read(folder/f'connection-{i}/session.json');assert session['done'] and session['interrupted']==(i==1)
        init=[h['position'] for h in scan((folder/f'connection-{i}/serial-received.bin').read_bytes()) if h['type']==1]
        assert init and all(v==0x23002000 for v in init);credits.append(init)
        evidence.append(folder/f'connection-{i}/session.json')
    evidence += [folder/'carrier-checks.json',folder/'carrier-audit-negative-checks.json',folder/'LABELS.BIN']
    canceled=root/args.cancel_label;cancel=read(canceled/'cancel-checks.json');cn=read(canceled/'cancel-audit-negative-checks.json')
    assert cancel['passed'] and all(cancel['checks'].values()) and cancel['terminal_sha256']==digest and not cancel['errors']
    assert cn['auditor_sha256']==sha(ROOT/'lab/bbs/audit_zmodem.py')
    assert cn['checker_sha256']==sha(ROOT/'lab/bbs/check_enigma_cancel_audit.py')
    assert cn['passed'] and len(cn['cases'])>=12 and all(c['rejected'] for c in cn['cases'])
    for p,h in cn['capture_hashes'].items():assert sha(canceled/p)==h
    evidence += [canceled/'cancel-checks.json',canceled/'cancel-audit-negative-checks.json']
    relay_path=ROOT/'build/bbs-lab/carrier-relay'/args.relay_label/'checks.json';relay=read(relay_path)
    assert relay['passed'] and all(relay['checks'].values());current(relay['sources']);evidence.append(relay_path)
    regression_path=root/args.repeat_audit_label/'audit-negative-checks.json';regression=read(regression_path)
    assert regression['passed'] and len(regression['cases'])==7 and all(c['rejected'] for c in regression['cases'])
    assert regression['shared_auditor_sha256']==sha(ROOT/'lab/bbs/audit_zmodem.py')
    for p,h in regression['capture_hashes'].items():assert sha(regression_path.parent/p)==h
    evidence.append(regression_path)
    empty_path=ROOT/'build/bbs-lab/empty-zmodem-audit/empty-credit-02/checks.json';empty=read(empty_path)
    assert empty['passed'] and all(c['passed'] for c in empty['cases'])
    assert empty['checker_sha256']==sha(ROOT/'lab/bbs/check_empty_zmodem_audit.py') and empty['auditor_sha256']==sha(ROOT/'lab/bbs/audit_zmodem.py')
    evidence.append(empty_path)
    proof_dir=ROOT/'build/aspect-unwind-mouse/source-proofs'/args.source_label;proof=read(proof_dir/'result.json')
    assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==31;current(proof['sources'])
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_aspect_unwind_source.py') and proof['log_sha256']==sha(proof_dir/'build.log')
    for p,h in proof['sources'].items():assert sha(proof_dir/'source'/p)==h
    for p,r in proof['products'].items():assert r['expected']==r['actual']==sha(ROOT/'build'/p)==sha(proof_dir/'source/build'/p)
    old=read(ROOT/'docs/validation/enigma-cancel-download.json')['source_products']
    changed={p for p,v in proof['products'].items() if v['actual']!=old[p]}
    assert changed=={p+'/TERMINAL.EXE' for p in ('terminal','terminal-process','terminal-mouse','terminal-mouse-process')}
    evidence += [proof_dir/'result.json',proof_dir/'build.log']
    packages={}
    for name,terminal in [('dos-package','terminal'),('dos-package-mouse','terminal-mouse')]:
        path=ROOT/'build'/name/'manifest.json';m=read(path);assert m['original_inputs']==[];current(m['sources'])
        assert all(sha(path.parent/p)==h for p,h in m['files'].items()) and m['files']['TERMINAL.EXE']==proof['products'][terminal+'/TERMINAL.EXE']['actual']
        packages[name]=m['files'];evidence.append(path)
    package_path=ROOT/'build/package-mouse-tests'/args.package_label/'result.json';package=read(package_path)
    assert package['passed'] and all(package['checks'].values()) and package['package_manifest_sha256']==sha(ROOT/'build/dos-package-mouse/manifest.json')
    evidence.append(package_path)
    failed=[root/n/'carrier-checks.json' for n in ('owned-carrier-02','owned-carrier-03')]
    for path in failed:assert not read(path)['passed']
    counter_path=root/'owned-carrier-02/finish-counterexample.json';counter=read(counter_path)
    assert counter['reproduced'] and counter['source_bytes_exact'] and counter['observed_EOF_to_receiver_ZRINIT_seconds']>10
    evidence += failed+[counter_path]
    output=dict(date=date.today().isoformat(),passed=True,whole_application_gates_closed=[],
        carrier_workflow=dict(checks=result['checks'],notices=result['notices'],snapshots=result['snapshots'],receive_credit=credits),
        cancellation_regression=cancel['checks'],capture_corruptions_rejected=len(negative['cases']),cancel_corruptions_rejected=len(cn['cases']),
        repeat_audit_corruptions_rejected=7,component_regressions=reports,relay_unit_checks=relay['checks'],empty_file_audit=empty['cases'],
        source_products={p:v['actual'] for p,v in proof['products'].items()},unchanged_products=27,changed_terminal_products=sorted(changed),
        original_build_inputs=[],source_hashes=proof['sources'],packages=packages,retained_counterexample=counter,
        evidence=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in evidence],
        recorder_sha256=sha(Path(__file__)),nix_inputs={p:sha(ROOT/p) for p in ('nix/flake.nix','nix/flake.lock')},
        capture_producer_auditors=dict(carrier=result['input_hashes']['auditor'],cancel=cancel['input_hashes']['auditor']),
        current_replay_auditor_sha256=sha(ROOT/'lab/bbs/audit_zmodem.py'),
        dosbox_executable_sha256=sha(Path(shutil.which('dosbox-x'))),
        limitations=['Built-in DOSBox-X modem, isolated staged ENiGMA decoder and generated catalog; no live deployment or physical Wi-Fi firmware acceptance.',
            'Bridge timestamps record forwarding, not the remote process actual send calls.',
            'One carrier workflow uses two TCP connections in one DOS process; later cancellation regression uses the separate Python Hayes/nullmodem model.',
            'Earlier receipts retain their own auditor versions; final reply ordering is stricter here.',
            'Captured workflows were re-audited after an empty-packet classification fix; producer and replay auditor hashes are recorded separately.',
            'No whole-application gate closes.'])
    with args.output.open('x') as f:f.write(json.dumps(output,indent=2)+'\n')
    print(args.output)


if __name__=='__main__':main()
