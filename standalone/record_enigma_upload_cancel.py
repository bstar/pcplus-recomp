#!/usr/bin/env python3
"""Bind DOS cancel/NFO/retry to explicit staged BBS ownership and unchanged apps."""
import argparse,json,re,sys
from datetime import date
from pathlib import Path
from build_native_mouse import ROOT,sha


def read(p):return json.loads(p.read_text())
def current(sources):
    for p,h in sources.items():assert not Path(p).is_absolute() and '..' not in Path(p).parts and sha(ROOT/p)==h,p


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label',required=True)
    for n in ('candidate','server-root','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    folder=ROOT/'build/bbs-lab/results/enigma'/a.label;r=read(folder/'upload-checks.json');negative=read(folder/'upload-audit-negative-checks.json')
    assert r['passed'] and r['cancel_first'] and len(r['checks'])==21 and all(r['checks'].values()) and not r['errors']
    assert negative['passed'] and len(negative['cases'])==22 and all(c['rejected'] for c in negative['cases'])
    assert next(c for c in negative['cases'] if c['case']=='valid-CRC-nonzero-invented-time')['reason']=='ZFILE time is not explicitly unknown'
    assert negative['checker_sha256']==r['input_hashes']['time_auditor']==sha(ROOT/'lab/bbs/check_enigma_upload_audit.py')
    assert negative['auditor_sha256']==r['input_hashes']['auditor']==sha(ROOT/'lab/bbs/audit_zmodem.py')
    for n,h in negative['capture_hashes'].items():assert sha(folder/n)==h
    for key,name in [('runner','enigma_upload_dos.py'),('harness','test_dos.py'),('observer','test_transfer_dos.py'),('form_observer','enigma_upload_watch.py'),('cancel_observer','enigma_upload_cancel_watch.py'),('fixture_owner','enigma_key_stream_fixture.py'),('observer_base','zmodem_label_watch.py')]:assert r['input_hashes'][key]==sha(ROOT/'lab/bbs'/name)
    candidate=a.candidate.resolve();assert candidate.is_relative_to(ROOT/'build');fixture=read(candidate/'search-instance.json')
    assert fixture['upload_fixture'] and fixture['upload_temp_experiment']
    for n,h in {**fixture['fixture_inputs'],**fixture['source_modules']}.items():assert sha(candidate/n)==h==r['input_hashes'][n]
    for n,h in fixture['source_inputs'].items():assert sha(a.server_root/n)==h
    experiment=read(candidate/'upload-temp-experiment.json');current(experiment['inputs'])
    assert set(experiment['changed'])=={'core/upload.js','core/file_transfer.js','core/file_transfer_protocol_select.js'}
    for n,h in experiment['staged_core'].items():assert sha(candidate/n)==h
    for n,h in experiment['original_core'].items():assert sha(a.server_root/n)==h==fixture['source_inputs'][n]
    sys.path.insert(0,str(ROOT/'lab/bbs'))
    from enigma_upload_dos import metadata
    from enigma_upload_cancel_watch import events
    from check_enigma_upload_audit import replay,catalog,canceled_prefix,canceled_snapshot
    from audit_zmodem import scan
    expected={n:(folder/'SEND'/n).read_bytes() for n in ('PCUP01.BIN','EMPTY.BIN')}
    assert len(expected['PCUP01.BIN'])==65539 and expected['EMPTY.BIN']==b''
    assert {n:sha(folder/'SEND'/n) for n in expected}=={n:v['sha256'] for n,v in r['expected'].items()}
    sent=(folder/'serial-received.bin').read_bytes();received=(folder/'display.bin').read_bytes();trace=read(folder/'trace.json')
    canceled=canceled_prefix(sent,received,trace,expected);assert canceled==r['canceled_protocol']
    assert next(h for h in scan(sent,canceled['first_offer']['end']) if h['type']==10)['position']==0
    retried=replay(sent,received,trace,expected,True,True)
    snapshots=read(folder/'cancel-upload-snapshots.json');assert snapshots==r['cancel_snapshots'];canceled_snapshot(snapshots)
    assert {row['name'] for row in snapshots[0]['entries']}==set(expected)
    forms=events((folder/'LABELS.BIN').read_bytes());assert forms==read(folder/'upload-form-events.json')
    before_search=sent[retried['end']:].split(b'S\r',1)[0]
    assert bytes(c for c in before_search if c in (9,13))==bytes(13 if e['key']=='Enter' else 9 for e in forms[1:])
    rows=metadata(candidate,list(expected));assert rows==read(folder/'server-upload-metadata.json');catalog(rows,expected,candidate,r['received_date_bounds_ns'])
    original_folder=folder.parent/'owned-upload-cancel-02';original=read(original_folder/'upload-checks.json')
    assert not original['passed'] and not original['checks']['canceled_temporary_data_removed']
    assert all(v for k,v in original['checks'].items() if k!='canceled_temporary_data_removed') and not original['errors']
    assert original['terminal_sha256']==r['terminal_sha256']
    assert read(original_folder/'result.json')['keyboard_input']==read(folder/'result.json')['keyboard_input']
    original_snapshot=read(original_folder/'cancel-upload-snapshots.json');assert original_snapshot[0]['temporary_files']
    bad_folder=folder.parent/'owned-upload-cancel-01';bad=read(bad_folder/'upload-checks.json')
    assert not bad['passed'] and not bad['checks']['DOS_harness'] and bad['checks']['source_files_unchanged']
    unit_root=ROOT/'build/bbs-lab/upload-temp-unit';baseline=read(unit_root/'original-01/checks.json');fixed=read(unit_root/'fixed-01/checks.json')
    assert baseline['passed'] and not baseline['fixed'] and len(baseline['cases'])==1
    assert fixed['passed'] and fixed['fixed'] and len(fixed['cases'])==14 and all(c['passed'] for c in fixed['cases'])
    for unit in (baseline,fixed):assert unit['checker_sha256']==sha(ROOT/'lab/bbs/patches/enigma-upload-temp/check.js')
    assert baseline['core']=={n:h for n,h in experiment['original_core'].items() if n in experiment['changed']}
    assert fixed['core']=={n:h for n,h in experiment['staged_core'].items() if n in experiment['changed']}
    assert baseline['temptmp_sha256']==fixed['temptmp_sha256']==sha(candidate/'node_modules/temptmp/index.js')
    upstream=read(unit_root/'upstream-bootstrapped-01.json');assert upstream['passed'] and upstream['exit_code']==0 and upstream['passing']==141
    assert upstream['bootstrap_sha256']==sha(candidate/'test/setup.js') and upstream['log_sha256']==sha(unit_root/'upstream-bootstrapped-01.log')
    preceding_path=ROOT/'docs/validation/enigma-upload-time.json';preceding=read(preceding_path);assert preceding['passed'];current(preceding['source_hashes'])
    for n,h in preceding['source_products'].items():assert sha(ROOT/'build'/n)==h
    assert len(preceding['source_products'])==31 and preceding['source_products']['terminal/TERMINAL.EXE']==r['terminal_sha256']
    evidence=[folder/n for n in ('upload-checks.json','upload-audit-negative-checks.json','cancel-upload-snapshots.json','LABELS.BIN','upload-form-events.json','server-upload-metadata.json')]
    evidence += [candidate/'search-instance.json',candidate/'upload-temp-experiment.json',original_folder/'upload-checks.json',original_folder/'cancel-upload-snapshots.json',bad_folder/'upload-checks.json',unit_root/'original-01/checks.json',unit_root/'fixed-01/checks.json',unit_root/'upstream-bootstrapped-01.json',unit_root/'upstream-bootstrapped-01.log',unit_root/'upstream-01.log',preceding_path]
    result=dict(date=date.today().isoformat(),passed=True,whole_application_gates_closed=[],checks=r['checks'],form_events=forms,
        first_cancel=dict(first_valid_packet_bytes=canceled['first_data']['length'],peer_ACK_position=canceled['ack']['position'],no_EOF=True),
        canceled_snapshot=dict(installed_files=0,catalog_entries=0,temporary_data_files=0,source_files_unchanged=True),
        installed_files={n:dict(bytes=v['bytes'],sha256=v['sha256']) for n,v in r['expected'].items()},
        corruptions_rejected=len(negative['cases']),baseline_shared_cleanup_reproduced=True,ownership_checks=fixed['cases'],upstream_regressions=141,
        staged_server=experiment,original_core_failure=original['checks'],
        retained_harness_failure=dict(label='owned-upload-cancel-01',reason='Unsupported esc token stopped the later ADDKEY commands; bounded DOS harness timeout. Later runs use escape.'),
        retained_upstream_invocation_failure='The first Mocha command omitted test/setup.js. The standard bootstrapped command passes all 141 checks.',
        application_code_changed=False,unchanged_application_products=31,source_products=preceding['source_products'],original_build_inputs=[],
        evidence=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in evidence],
        sources={n:sha(ROOT/n) for n in ('lab/bbs/enigma_upload_dos.py','lab/bbs/enigma_upload_cancel_watch.py','lab/bbs/check_enigma_upload_audit.py','lab/bbs/enigma_key_stream_fixture.py','lab/bbs/patches/enigma-upload-temp/stage.py','lab/bbs/patches/enigma-upload-temp/check.js','lab/bbs/patches/enigma-upload-temp/upload-temp.patch')},
        recorder_sha256=sha(Path(__file__)),nix_inputs={n:sha(ROOT/n) for n in ('nix/flake.nix','nix/flake.lock')},
        limitations=['Isolated keyboard-decoder candidate plus explicit three-module upload ownership patch; neither is installed on the running board.',
            'Modeled 19200/HARD UART. Physical modem, upload carrier loss and original source-date preservation remain open.',
            'The ownership component uses real module methods/files but does not establish simultaneous BBS connections or cleanup under filesystem/spawn errors.',
            'Unrelated protocol-list temporary tracking and full application requirements remain open.'])
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(a.output)


if __name__=='__main__':main()
