#!/usr/bin/env python3
"""Bind automatic-reception evidence to the frozen maintained runtime.
No tests, BBS commands or protocol replies are executed by this collector.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNTIME='731418bde8f3264d5f6c987195eb54b20c86a2981259ea1c721ba252e3c9a776'

def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def main():
    artifacts=set()
    def retain(path):
        path=Path(path)
        if (ROOT/path).is_dir():
            artifacts.update(p.relative_to(ROOT) for p in (ROOT/path).rglob('*') if p.is_file() and p.name!='.lock')
        else:
            assert (ROOT/path).is_file(),path
            artifacts.add(path)
    manifest=read('build/terminal/manifest.json');memory=manifest['memory_layout']
    assert manifest['binary_sha256']==sha('build/terminal/TERMINAL.EXE')==RUNTIME
    assert (memory['near_bytes'],memory['resident_code_bytes'],memory['configuration_bridge_pairs_verified'],memory['far_code_bridge_pairs_verified'])==(65296,63630,78,127)
    for path,digest in manifest['sources'].items():assert sha(path)==digest,path
    linked={}
    for key,path in {
        'preferences':'transfer-preferences-live-checks.json',
        'invitations':'autostart-live-checks.json',
        'bridges':'config-far-checks.json',
        'protocol_regression':'terminal-zmodem-live-checks.json',
    }.items():
        location='build/terminal/'+path;data=read(location)
        assert data['passed'] and data['binary_sha256']==RUNTIME
        linked[key]=data;retain(location)
    assert sum(c['inputs'] for c in linked['preferences']['cases'])==60
    assert len(linked['invitations']['cases'])==5
    assert len(linked['bridges']['rejected_mutations'])==384
    assert linked['protocol_regression']['inputs']==78
    regression=read('build/terminal/autostart-final-regression.json')
    commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
    assert len(commands)==80 and regression['complete'] and regression['passed']
    assert regression['binary_sha256']==RUNTIME and all(c['exit_code']==0 for c in regression['commands'])
    assert [c['command'] for c in regression['commands']]==commands
    for path in ('build/terminal/autostart-final-regression.json','build/terminal/autostart-final-regression.log','build/terminal/autostart-final-regression'):
        retain(path)
    source=read('docs/validation/application-components-source-build.json')
    assert source['passed'] and source['output_count']==64
    for path,data in source['outputs'].items():
        assert data['matches_workspace'] and sha('build/'+path)==data['sha256'],path
    assert read('docs/validation/terminal-source-build.json')['manifest']==manifest
    for path in ('docs/validation/application-components-source-build.json','docs/validation/terminal-source-build.json','build/application-source-proof/snapshot.json','build/application-source-proof/result.json','build/application-source-proof/build.log','build/terminal/TERMINAL.EXE','build/terminal/terminal.map','build/terminal/manifest.json'):
        retain(path)
    dos=[]
    for label,count in [('auto-7314-small',1),('auto-7314-large',2)]:
        location=Path('build/terminal-zmodem-dos')/label;report=read(location/'checks.json')
        assert report['passed'] and report['binary_sha256']==RUNTIME and len(report['cases'])==count
        for case in report['cases']:
            assert case['passed'] and all(case['checks'].values())
            assert case['checks']['no_manual_transfer_keys'] and case['checks']['saved_preferences_unchanged']
            assert case['peer_exit']==0
            dos.append(case)
        retain(location)
    failure_path=Path('build/terminal-zmodem-dos/auto-f8df-first')
    failure=read(failure_path/'checks.json');assert not failure['passed']
    assert failure['binary_sha256']=='f8df666aa39b0942a75485184ab8b285997a2f03ab1b48bfc6aa6f116770f889'
    # Keep the original failed outcome; the prototype executable itself was
    # overwritten before retention, so no byte-identical paired replay claim.
    assert failure['cases'][0]['peer_command'] is None
    retain(failure_path)
    bbs=[]
    for server,short in [('synchronet','sync'),('enigma','enigma')]:
        label='zmodem-auto-7314-'+short+'-1';location=Path('build/bbs-lab/results')/server/label
        data=read(location/'result.json')
        assert data['passed'] and data['standard_completion'] and data['binary_sha256']==RUNTIME
        assert all(data['checks'].values()) and data['checks']['automatic_invitation_then_receiver_negotiation']
        assert data['checks']['no_manual_transfer_keys']
        assert read(location/'server-source-metadata.json')['passed']
        bbs.append({k:data[k] for k in ('passed','standard_completion','name','label','mode','binary_sha256','payload_sha256','checks','errors','serial')})
        retain(location);retain('build/bbs-lab/'+label+'-command.json')
    guard=read('build/bbs-lab/results/synchronet/zmodem-auto-7314-sync-1-logon.json')
    assert guard['restored'] and guard['after']==guard['before']==0
    retain('build/bbs-lab/results/synchronet/zmodem-auto-7314-sync-1-logon.json')
    retain('build/bbs-lab/zmodem-logon-readback.json')
    readback=read('build/bbs-lab/zmodem-logon-readback.json')
    assert readback['level']==50 and readback['exemptions']==0
    paired=read('build/terminal/autostart-midnight-paired.json')
    assert paired['passed'] and paired['cases'][1]['binary_sha256']==RUNTIME
    assert paired['cases'][0]['released_after_one_tick']=='2a' and paired['cases'][1]['released_after_one_tick']==''
    storage=read('build/batch-download/result.json')
    assert storage['passed'] and all(storage['checks'].values())
    for path,digest in storage['sources'].items():assert sha(path)==digest,path
    assert len([s for s in storage['normal_cases'] if s.startswith('PASS ')])==21
    assert len([s for s in storage['fault_cases'] if s.startswith('PASS ')])==38
    earlier=read('build/checkpoints/autostart-f0fd/validation.json')
    assert earlier['passed'] and earlier['terminal_regression']['complete']
    drive_failure=read('build/checkpoints/autostart-d23b-paths/result.json')
    assert not drive_failure['passed'] and not drive_failure['checks']['REL/DRIVE.BIN']
    for path in ('build/terminal/autostart-midnight-paired.json','build/terminal/recheck-autostart-midnight.py','build/batch-download/result.json','build/checkpoints/autostart-f0fd','build/checkpoints/autostart-d23b-paths'):
        retain(path)
    sources={path:sha(path) for path in (
        'standalone/check_autostart_live.py','standalone/check_transfer_preferences_live.py',
        'standalone/test_terminal_zmodem_dos.py','lab/bbs/test_zmodem_dos.py',
        'standalone/record_autostart.py','src/config/terminal_preferences.h',
        'src/config/terminal_preferences.c','src/transfer/terminal_autostart.c',
        'src/transfer/batch_download.c','standalone/batch_download_host.c',
        'standalone/check_batch_download.py')}
    result=dict(passed=True,binary_sha256=RUNTIME,memory=memory,linked=linked,
                terminal_regression=regression,source_only_rebuild=dict(outputs=64,byte_identical=True,snapshot_sha256=source['source_snapshot_sha256']),
                actual_DOS=dos,actual_BBS=bbs,storage=storage,midnight_paired=paired,
                earlier_validated_prototype=dict(binary_sha256=earlier['binary_sha256'],regression=earlier['terminal_regression'],actual_DOS=earlier['actual_DOS'],actual_BBS=earlier['actual_BBS'],midnight_counterexample=read('build/checkpoints/autostart-f0fd/midnight-counterexample.json')),
                failed_drive_extension=drive_failure,
                failed_prototype=dict(report=failure,reason='Early recognizer initialization clobbered AX before PROGRAM saved the PSP; fixed by preserving AX. Original failed artifacts retained; prototype executable not retained.'),
                sources=sources,artifacts={str(p):sha(p) for p in sorted(artifacts)},
                scope='Canonical CRC-valid hex ZRQINIT automatic receive with saved enable/directory preferences; modeled linked ownership plus actual DOS/lrzsz and stock Synchronet/ENiGMA downloads without manual transfer keys. Parser continuations remain raw; software flow/non-8-bit/dedicated owners exclude recognition. Other invitation forms, persisted resume, broader line/peer timing, physical modem behavior and all F01-F16 whole-application gates remain open.')
    (ROOT/'docs/validation/zmodem-autostart.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Automatic reception:80 terminal commands;384 damaged ABI images;3 DOS and2 BBS automatic-download workflows;64 matching source-only outputs.')

if __name__=='__main__':main()
