#!/usr/bin/env python3
"""Preserve current terminal TX provenance and compatibility evidence."""
import argparse
import ast
import json
import shutil
from pathlib import Path
from record_recording_file import ROOT, read, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort', type=Path, required=True)
    parser.add_argument('--terminal-dos', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cohort, dos, output = (p.resolve() for p in (args.cohort, args.terminal_dos, args.output))
    assert cohort.is_relative_to(ROOT/'build') and dos.is_relative_to(ROOT/'build')
    assert not cohort.exists() and output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    selected = {Path(__file__).resolve(), ROOT/'standalone/record_recording_file.py', ROOT/'Makefile'}
    variants = {}
    for name, data_spare, code_spare in (('terminal',112,440),('terminal-mouse',64,290)):
        directory = ROOT/'build'/name
        manifest_path = directory/'manifest.json'
        manifest = read(manifest_path)
        assert manifest['kind']=='source-only-interactive-dos-terminal'
        assert sha(directory/'TERMINAL.EXE')==manifest['binary_sha256']
        selected.update((manifest_path,directory/'TERMINAL.EXE',directory/'terminal.map'))
        for source,digest in manifest['sources'].items():
            assert not source.startswith(('analysis/','build/')) and sha(ROOT/source)==digest,source
            selected.add(ROOT/source)
        memory=manifest['memory_layout']
        assert memory['near_spare_bytes']==data_spare and memory['resident_code_spare_bytes']==code_spare
        assert memory['recording_terminal_state_bytes']==392 and memory['recording_tx_origin_bytes']==128
        assert memory['configuration_bridge_pairs_verified']==94
        assert memory['far_code_bridge_pairs_verified']==(160 if name=='terminal-mouse' else 150)
        if name=='terminal-mouse':assert memory['mouse_bridge_pairs_verified']==10
        assert len(memory['recording_tx_far_call_sites'])==4 and memory['recording_tx_callback_site']>0
        variants[name]=dict(binary_sha256=manifest['binary_sha256'],memory_layout=memory,
                            runtime_regressions_accepted=name=='terminal')
    binary_sha256=variants['terminal']['binary_sha256']
    regressions={}
    recipes=(('wire','recording-tx-checks.json',10),('owner','recording-foreground-checks.json',6),
             ('transport','transport-results.json',6),('TEXT','meta-actions-live-checks.json',343),
             ('clipboard','clipboard-live-checks.json',46),('ZMODEM','terminal-zmodem-live-checks.json',78),
             ('ABI','config-far-checks.json',574))
    for name,filename,count in recipes:
        path=ROOT/'build/terminal'/filename;proof=read(path)
        assert proof['passed'] and proof['binary_sha256']==binary_sha256
        if name=='ABI':
            assert len(proof['rejected_mutations'])==count and proof['memory']==variants['terminal']['memory_layout']
        elif name in ('TEXT','clipboard','ZMODEM'):
            assert proof['inputs']==count
            assert all(c['passed'] for c in proof.get('cases',proof.get('groups',[])))
        else:
            assert len(proof['cases'])==count and all(c['passed'] for c in proof['cases'])
        if name=='wire':
            assert proof['source_sha256']==sha(ROOT/'standalone/check_recording_tx_live.py')
        if name=='ZMODEM':
            assert proof['test_sha256']==sha(ROOT/'standalone/check_terminal_zmodem_live.py')
        selected.add(path)
        regressions[name]=dict(result=str(path.relative_to(ROOT)),sha256=sha(path),cases_or_inputs=count)
    keys_path=ROOT/'build/terminal-key-output/checks.json';keys=read(keys_path)
    assert keys['passed'] and keys['cases']==837 and keys['binary_sha256']==binary_sha256
    assert not keys['original_inputs'] and keys['checker_sha256']==sha(ROOT/'standalone/check_terminal_key_output.py')
    selected.add(keys_path)
    regressions['keys']=dict(result=str(keys_path.relative_to(ROOT)),sha256=sha(keys_path),cases=837)
    proof=read(dos)
    assert proof['passed'] and proof['binary_sha256']==binary_sha256 and len(proof['cases'])==11
    assert all(c['passed'] and all(c['checks'].values()) for c in proof['cases'])
    selected.update(p for p in dos.parent.rglob('*') if p.is_file())
    visited=set()
    def keep_imports(path):
        if path in visited:return
        visited.add(path);selected.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[n.name for n in node.names] if isinstance(node,ast.Import) else (
                [node.module] if isinstance(node,ast.ImportFrom) and node.module else [])
            for module in modules:
                imported=path.parent/(module.split('.')[0]+'.py')
                if imported.is_file():keep_imports(imported)
    for name in ('check_recording_tx_live.py','check_recording_foreground_live.py','check_transport.py',
                 'check_meta_actions_live.py','check_clipboard_live.py','check_terminal_zmodem_live.py',
                 'check_config_far_live.py','check_terminal_key_output.py','test_terminal_capture_dos.py'):
        keep_imports(ROOT/'standalone'/name)
    previous=ROOT/'docs/validation/recording-owner.json'
    assert read(previous)['recording_owner_component_accepted']
    selected.add(previous)
    for name in ('tags-wire-02.stdout','tags-wire-02.stderr'):
        selected.add(ROOT/'build/recording-file'/name)
    cohort.mkdir();custody=cohort/'accepted';custody.mkdir();kept={}
    for path in sorted(selected):
        copy=custody/path.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,copy);assert sha(copy)==sha(path)
        kept[str(copy.relative_to(ROOT))]=sha(copy)
    result=dict(passed=True,recording_TX_component_accepted=True,terminal_recording_accepted=False,
        variants=variants,regressions=regressions,
        actual_DOS_capture=dict(result=str(dos.relative_to(ROOT)),sha256=sha(dos),cases=11),
        owner_prerequisite=dict(result=str(previous.relative_to(ROOT)),sha256=sha(previous)),
        custody_sha256=kept,
        scope='Three register/flag-preserving far helpers classify1024 ring slots with128 initialized '
              'loaded bank bytes. Both successful queue-drain paths and direct TEXT output feed the '
              'recorder after actual UART acceptance. Replies/dedicated producers use zero tags; '
              'normal keys, expanded bindings and clipboard use user tags. Ten linked campaigns '
              'cover all octets, full-capacity dirty/wrapped tags, busy UART/CTS, reset/cancellation, '
              'FF-to-NUL/pause behavior, actual transfer-drain instructions and write-error continuity. '
              'Kernel/hardware boundaries are models;11 DOS capture cases exercise the current terminal '
              'with recording idle. No Record UI, RX taps, complete owner exclusions, current BBS/audio, '
              'physical modem or full F01-F16 application acceptance.')
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,custody_files=len(kept))))


if __name__=='__main__':main()
