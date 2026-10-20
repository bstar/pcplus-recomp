#!/usr/bin/env python3
"""Publish unknown-time compatibility, DOS upload and fresh source evidence."""
import argparse,json,re,sys,shutil
from datetime import date
from pathlib import Path
from build_native_mouse import ROOT,sha


def read(path):return json.loads(path.read_text())
def current(sources):
    for p,h in sources.items():assert not Path(p).is_absolute() and '..' not in Path(p).parts and sha(ROOT/p)==h,p


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('peer-label','upload-label','source-label','package-label'):p.add_argument('--'+name,required=True)
    for name in ('candidate','server-root','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    for name,v in vars(a).items():
        if name.endswith('_label'):assert re.fullmatch(r'[A-Za-z0-9_-]+',v)
    evidence=[];binary=ROOT/'build/terminal/TERMINAL.EXE';digest=sha(binary)
    peer_path=ROOT/'build/zmodem-timestamp'/a.peer_label/'checks.json';peer=read(peer_path)
    assert peer['passed'] and peer['absent_time_bad_date_reproduced'] and len(peer['cases'])==6;current(peer['sources'])
    assert {c['case'] for c in peer['cases']}=={m+'-empty-'+o for m in ('absent','unknown','engine') for o in ('first','last')}
    assert all(c['bytes_exact'] and c['receiver_exit']==0 for c in peer['cases'])
    assert all(all(c['current_creation_dates'].values()) for c in peer['cases'] if c['explicit_unknown_time'])
    evidence.append(peer_path)
    folder=ROOT/'build/bbs-lab/results/enigma'/a.upload_label;r=read(folder/'upload-checks.json');negative=read(folder/'upload-audit-negative-checks.json')
    assert r['passed'] and all(r['checks'].values()) and not r['errors'] and r['terminal_sha256']==digest
    assert r['checks']['received_creation_dates_current'] and r['checks']['explicit_unknown_time_on_wire']
    assert r['expected']['PCUP01.BIN']['bytes']==65539 and r['expected']['EMPTY.BIN']['bytes']==0
    assert negative['passed'] and len(negative['cases'])==14 and all(c['rejected'] for c in negative['cases'])
    assert next(c for c in negative['cases'] if c['case']=='valid-CRC-nonzero-invented-time')['reason']=='ZFILE time is not explicitly unknown'
    assert negative['checker_sha256']==r['input_hashes']['time_auditor']==sha(ROOT/'lab/bbs/check_enigma_upload_audit.py')
    assert negative['auditor_sha256']==r['input_hashes']['auditor']==sha(ROOT/'lab/bbs/audit_zmodem.py')
    for name,h in negative['capture_hashes'].items():assert sha(folder/name)==h
    for key,name in [('runner','enigma_upload_dos.py'),('harness','test_dos.py'),('observer','test_transfer_dos.py'),('form_observer','enigma_upload_watch.py'),('observer_base','zmodem_label_watch.py')]:assert r['input_hashes'][key]==sha(ROOT/'lab/bbs'/name)
    candidate=a.candidate.resolve();assert candidate.is_relative_to(ROOT/'build');fixture=read(candidate/'search-instance.json')
    assert fixture['upload_fixture'] and peer['peer_sha256']==fixture['fixture_inputs']['helpers/sexyz']
    for name,h in {**fixture['fixture_inputs'],**fixture['source_modules']}.items():assert sha(candidate/name)==h==r['input_hashes'][name]
    for name,h in fixture['source_inputs'].items():assert sha(a.server_root/name)==h
    sys.path.insert(0,str(ROOT/'lab/bbs'))
    from enigma_upload_dos import metadata
    from check_enigma_upload_audit import replay,catalog
    from enigma_upload_watch import events as form_events
    expected={p.name:p.read_bytes() for p in (folder/'SEND').iterdir()}
    assert {name:sha(folder/'SEND'/name) for name in expected}=={name:v['sha256'] for name,v in r['expected'].items()}
    rows=metadata(candidate,list(expected));assert rows==read(folder/'server-upload-metadata.json')
    catalog(rows,expected,candidate,r['received_date_bounds_ns'])
    forms=form_events((folder/'LABELS.BIN').read_bytes());assert forms==read(folder/'upload-form-events.json')
    sent=(folder/'serial-received.bin').read_bytes()
    audited=replay(sent,(folder/'display.bin').read_bytes(),read(folder/'trace.json'),expected,True)
    before_search=sent[audited['end']:].split(b'S\r',1)[0]
    assert bytes(c for c in before_search if c in (9,13))==bytes(13 if e['key']=='Enter' else 9 for e in forms)
    files={row['name']:dict(bytes=row['entries'][0]['meta']['byte_size'],sha256=row['entries'][0]['fileSha256'],description=row['entries'][0]['desc'],
        uploader=row['entries'][0]['meta']['upload_by_username'],mtime_ns=str(Path(row['entries'][0]['filePath']).stat().st_mtime_ns)) for row in rows}
    evidence += [folder/'upload-checks.json',folder/'upload-audit-negative-checks.json',folder/'server-upload-metadata.json',folder/'LABELS.BIN',folder/'upload-form-events.json',candidate/'search-instance.json']
    reports={}
    for name,count in [('terminal-zmodem-live-checks.json',78),('zmodem-cancel-checks.json',5),('zmodem-name-ui-checks.json',17),('terminal-transfer-live-checks.json',44),('terminal-ymodem-live-checks.json',23)]:
        path=binary.parent/name;m=read(path)
        assert m['passed'] and m['binary_sha256']==digest
        if name in ('terminal-transfer-live-checks.json','terminal-ymodem-live-checks.json'):assert m['inputs']==count
        else:assert len(m['cases'])==count
        assert all(c['passed'] if 'passed' in c else c['visible'] and c['restored'] for c in m['cases'])
        reports[name]=dict(groups=len(m['cases']),inputs=m.get('inputs',count));evidence.append(path)
    for name,field,count in [('zmodem-session','scripted_checks',92),('zmodem-window','inputs',79),('zmodem-dos','DOS_cases',68)]:
        path=ROOT/'build'/name/'checks.json';m=read(path);assert m['passed'] and m[field]==count;current(m['sources'])
        if name=='zmodem-session':assert len(m['independent_peers'])==24 and all(c['passed'] and c['peer_exit']==0 for c in m['independent_peers'])
        if name=='zmodem-dos':assert m['isolated_source_build_byte_identical'] and m['binary_sha256']==sha(path.parent/'SESSION.EXE')
        reports[name]=count;evidence.append(path)
    proof_dir=ROOT/'build/aspect-unwind-mouse/source-proofs'/a.source_label;proof=read(proof_dir/'result.json')
    assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==31;current(proof['sources'])
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_aspect_unwind_source.py') and proof['log_sha256']==sha(proof_dir/'build.log')
    for name,h in proof['sources'].items():assert sha(proof_dir/'source'/name)==h
    for name,v in proof['products'].items():assert v['expected']==v['actual']==sha(ROOT/'build'/name)==sha(proof_dir/'source/build'/name)
    old_path=ROOT/'docs/validation/enigma-upload.json';old=read(old_path)
    changed={name for name,v in proof['products'].items() if v['actual']!=old['unchanged_source_products'][name]}
    assert changed=={name+'/TERMINAL.EXE' for name in ('terminal','terminal-process','terminal-mouse','terminal-mouse-process')}
    failures=[]
    for label,reason in [('owned-upload-time-01','Explicit unknown time reached the wire; fixed Tab navigation did not submit both forms.'),
                         ('owned-upload-time-02','Files and current dates persisted; observer matched only the focused button spelling and did not complete the NFO workflow.'),
                         ('owned-upload-time-03','Files and current dates persisted, but the scan pause was acknowledged by late recipe keys; the forms/NFO workflow failed.')]:
        failed_path=ROOT/'build/bbs-lab/results/enigma'/label/'upload-checks.json';failed=read(failed_path)
        assert not failed['passed'] and failed['checks']['explicit_unknown_time_on_wire'] and not failed['checks']['actual_upload_and_return_route']
        if not label.endswith('01'):assert failed['checks']['all_server_files_and_metadata'] and failed['checks']['received_creation_dates_current']
        failures.append(dict(label=label,checks=failed['checks'],reason=reason));evidence.append(failed_path)
    before=read(ROOT/'docs/validation/enigma-carrier.json')['source_hashes']
    for name in ('src/transfer/batch_header.c','src/transfer/batch_header.h'):assert sha(ROOT/name)==before[name]
    evidence += [proof_dir/'result.json',proof_dir/'build.log',old_path]
    packages={}
    for name,terminal in [('dos-package','terminal'),('dos-package-mouse','terminal-mouse')]:
        path=ROOT/'build'/name/'manifest.json';m=read(path);assert m['original_inputs']==[];current(m['sources'])
        assert all(sha(path.parent/f)==h for f,h in m['files'].items()) and m['files']['TERMINAL.EXE']==proof['products'][terminal+'/TERMINAL.EXE']['actual']
        packages[name]=m['files'];evidence.append(path)
    package_path=ROOT/'build/package-mouse-tests'/a.package_label/'result.json';package=read(package_path)
    assert package['passed'] and all(package['checks'].values()) and package['package_manifest_sha256']==sha(ROOT/'build/dos-package-mouse/manifest.json')
    evidence.append(package_path)
    tool_hashes={}
    for name in ('wcl','dosbox-x','nasm'):
        path=Path(shutil.which(name)).resolve();assert str(path).startswith('/nix/store/')
        tool_hashes[name]=sha(path)
    result=dict(date=date.today().isoformat(),passed=True,whole_application_gates_closed=[],
        retained_failures=failures,
        form_events=forms,peer_cases=peer['cases'],peer_sha256=peer['peer_sha256'],upload_checks=r['checks'],installed_files=files,
        received_date_bounds_ns=[str(v) for v in r['received_date_bounds_ns']],menus=r['menus'],corruptions_rejected=len(negative['cases']),
        component_regressions=reports,source_products={name:v['actual'] for name,v in proof['products'].items()},source_hashes=proof['sources'],
        unchanged_products=27,changed_products=sorted(changed),original_build_inputs=[],packages=packages,
        evidence=[dict(path=str(path.relative_to(ROOT)),sha256=sha(path)) for path in evidence],recorder_sha256=sha(Path(__file__)),tool_sha256=tool_hashes,
        nix_inputs={name:sha(ROOT/name) for name in ('nix/flake.nix','nix/flake.lock')},
        sources={name:sha(ROOT/name) for name in ('src/transfer/zmodem.c','lab/bbs/enigma_search_fixture.py','lab/bbs/enigma_upload_dos.py','lab/bbs/check_enigma_upload_audit.py','lab/bbs/enigma_upload_watch.py','standalone/check_zmodem_timestamp.py','standalone/check_zmodem_progress_live.py')},
        limitations=['Explicit unknown time avoids invented dates; original source timestamp preservation is not implemented by the current source ABI.',
            'Actual isolated ENiGMA upload plus host stdio peer tests; no live deployment or physical Wi-Fi modem acceptance.',
            'Upload interruption and full application requirements remain open. Earlier captures retain their invalid dates and original producer identities.'])
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(a.output)


if __name__=='__main__':main()
