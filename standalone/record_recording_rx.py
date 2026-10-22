#!/usr/bin/env python3
"""Preserve normal/parser RX recording and current terminal regressions."""
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
    for name, data_spare, code_spare in (('terminal',96,414),('terminal-mouse',48,264)):
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
        assert memory['recording_terminal_state_bytes']==396 and memory['recording_tx_origin_bytes']==128
        assert memory['configuration_bridge_pairs_verified']==94
        assert memory['far_code_bridge_pairs_verified']==(160 if name=='terminal-mouse' else 150)
        if name=='terminal-mouse':assert memory['mouse_bridge_pairs_verified']==10
        assert len(memory['recording_tx_far_call_sites'])==4 and memory['recording_tx_callback_site']>0
        assert len(memory['recording_rx_far_call_sites'])==4 and memory['recording_rx_callback_site']>0
        variants[name]=dict(binary_sha256=manifest['binary_sha256'],memory_layout=memory,
                            runtime_regressions_accepted=name=='terminal')
    binary_sha256=variants['terminal']['binary_sha256']
    regressions={}
    recipes=(('RX','recording-rx-checks.json',10),('TX','recording-tx-checks.json',10),
             ('owner','recording-foreground-checks.json',6),('autostart','autostart-live-checks.json',5),
             ('translation','translation-live-checks.json',783),('ZMODEM','terminal-zmodem-live-checks.json',78),
             ('ABI','config-far-checks.json',594))
    for name,filename,count in recipes:
        path=ROOT/'build/terminal'/filename;proof=read(path)
        assert proof['passed'] and proof['binary_sha256']==binary_sha256
        if name=='ABI':
            assert len(proof['rejected_mutations'])==count and proof['memory']==variants['terminal']['memory_layout']
        elif name in ('translation','ZMODEM'):
            assert proof['inputs']==count
            assert all(c['passed'] for c in proof.get('cases',proof.get('groups',[])))
        else:
            assert len(proof['cases'])==count and all(c['passed'] for c in proof['cases'])
        if name in ('RX','TX'):
            assert proof['source_sha256']==sha(ROOT/'standalone'/('check_recording_'+name.lower()+'_live.py'))
        if name=='ZMODEM':
            assert proof['test_sha256']==sha(ROOT/'standalone/check_terminal_zmodem_live.py')
        selected.add(path)
        regressions[name]=dict(result=str(path.relative_to(ROOT)),sha256=sha(path),cases_or_inputs=count)
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
    for name in ('check_recording_rx_live.py','check_recording_tx_live.py','check_recording_foreground_live.py',
                 'check_autostart_live.py','check_translation_live.py','check_terminal_zmodem_live.py',
                 'check_config_far_live.py','test_terminal_capture_dos.py'):
        keep_imports(ROOT/'standalone'/name)
    previous=ROOT/'docs/validation/recording-tx.json'
    assert read(previous)['recording_TX_component_accepted']
    selected.add(previous)
    for name in ('rx-wire.stdout','rx-wire.stderr'):
        selected.add(ROOT/'build/recording-file'/name)
    cohort.mkdir();custody=cohort/'accepted';custody.mkdir();kept={}
    for path in sorted(selected):
        copy=custody/path.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,copy);assert sha(copy)==sha(path)
        kept[str(copy.relative_to(ROOT))]=sha(copy)
    result=dict(passed=True,recording_RX_component_accepted=True,terminal_recording_accepted=False,
        variants=variants,regressions=regressions,
        actual_DOS_capture=dict(result=str(dos.relative_to(ROOT)),sha256=sha(dos),cases=11),
        TX_prerequisite=dict(result=str(previous.relative_to(ROOT)),sha256=sha(previous)),
        custody_sha256=kept,
        scope='Ordinary input before XLT and native parser continuation reads feed received prompts '
              'after configured UART masking. A lifecycle-reset replay flag/cursor suppresses only a '
              'parser unreceive reread, including ring wrap. Active/recovery recorder ownership denies '
              'automatic transfer admission. Ten RX and ten TX linked campaigns include an actual native '
              'query/reply/user-output sequence with replies excluded. Six owner, five autostart groups, '
              '783 translation inputs,78 ZMODEM workflows and594 ABI negatives pass against the current '
              'terminal.11 DOS capture cases have recording idle. Kernel/hardware are modeled in linked '
              'campaigns. No Record UI, complete transition exclusions, actual DOS foreground recording, '
              'current BBS/audio, physical modem or full F01-F16 acceptance.')
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,custody_files=len(kept))))


if __name__=='__main__':main()
