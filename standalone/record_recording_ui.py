#!/usr/bin/env python3
"""Preserve selected foreground Record UI, DOS compiler/replay and guard evidence."""
import argparse,ast,json,shutil
from pathlib import Path
from record_recording_file import ROOT,read,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('cohort','dos-new','dos-replace','dos-cancel','capture','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    cohort=args.cohort.resolve();output=args.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    selected={Path(__file__).resolve(),ROOT/'standalone/record_recording_file.py',ROOT/'Makefile'}
    variants={}
    for name,data_spare,code_spare in (('terminal',96,356),('terminal-mouse',48,206)):
        directory=ROOT/'build'/name;manifest=read(directory/'manifest.json')
        assert manifest['kind']=='source-only-interactive-dos-terminal'
        assert sha(directory/'TERMINAL.EXE')==manifest['binary_sha256']
        selected.update((directory/'manifest.json',directory/'TERMINAL.EXE',directory/'terminal.map'))
        for source,digest in manifest['sources'].items():
            assert not source.startswith(('analysis/','build/')) and sha(ROOT/source)==digest,source
            selected.add(ROOT/source)
        memory=manifest['memory_layout']
        assert memory['near_spare_bytes']==data_spare and memory['resident_code_spare_bytes']==code_spare
        assert memory['recording_terminal_state_bytes']==396
        assert len(memory['recording_actor_guard_sites'])==9
        assert len(memory['recording_UI_boundary_sites'])==3 and len(memory['recording_UI_optimized_sites'])==2
        variants[name]=dict(binary_sha256=manifest['binary_sha256'],memory_layout=memory,
                           runtime_workflows_accepted=name=='terminal')
    binary_sha256=variants['terminal']['binary_sha256']
    regressions={}
    for name,filename,count,kind in (
        ('Record UI','recording-ui-checks.json',10,'cases'),('Menu','command-menu-checks.json',153,'inputs'),
        ('TX','recording-tx-checks.json',10,'cases'),('RX','recording-rx-checks.json',10,'cases'),
        ('PROGRAM','program-actions-live-checks.json',60,'inputs'),('Autostart','autostart-live-checks.json',5,'cases'),
        ('ZMODEM','terminal-zmodem-live-checks.json',78,'inputs'),('ABI','config-far-checks.json',629,'mutations')):
        path=ROOT/'build/terminal'/filename;proof=read(path)
        assert proof['passed'] and proof['binary_sha256']==binary_sha256
        if kind=='mutations':
            assert len(proof['rejected_mutations'])==count and proof['memory']==variants['terminal']['memory_layout']
        else:
            assert (len(proof['cases']) if kind=='cases' else proof['inputs'])==count
            assert all(c['passed'] for c in proof['cases'])
        selected.add(path);regressions[name]=dict(result=str(path.relative_to(ROOT)),sha256=sha(path),count=count)
    dos_proofs={}
    for mode,path in (('new',args.dos_new.resolve()),('replace',args.dos_replace.resolve()),('cancel',args.dos_cancel.resolve())):
        assert path.is_relative_to(ROOT/'build');proof=read(path)
        assert proof['passed'] and all(proof['checks'].values()) and proof['mode']==mode
        assert proof['binary_sha256']==binary_sha256 and not proof['errors']
        for name,digest in proof['inputs'].items():
            source=ROOT/name;frozen=path.parent/'frozen-source'/name
            assert sha(source)==sha(frozen)==digest,name
            selected.update((source,frozen))
        for name,digest in proof['captures_sha256'].items():
            artifact=path.parent/name
            assert artifact.resolve().is_relative_to(path.parent) and sha(artifact)==digest
            selected.add(artifact)
        assert sha(path.parent/'TERMINAL.EXE')==binary_sha256
        if mode=='cancel':
            assert (path.parent/'PCPLUS.ASP').read_bytes()==b'ORIGINAL\x1aKEEP\r\n'
            assert not (path.parent/'RECORD.ASX').exists()
        else:
            assert proof['recorded_payload_hex']==proof['manual_hex']==proof['replay_hex']
            assert bytes.fromhex(proof['manual_hex']) in (b'm1bstar\r',b'm1bstar\r\n')
            assert (path.parent/'PCPLUS.ASP').read_bytes().endswith(b'endproc\r\n')
        assert (path.parent/'BEFORE.BIN').read_bytes()==(path.parent/'AFTER.BIN').read_bytes()
        selected.add(path);dos_proofs[mode]=dict(result=str(path.relative_to(ROOT)),sha256=sha(path))
    capture=args.capture.resolve();proof=read(capture)
    assert capture.is_relative_to(ROOT/'build') and proof['passed'] and proof['binary_sha256']==binary_sha256
    assert len(proof['cases'])==11 and all(c['passed'] and all(c['checks'].values()) for c in proof['cases'])
    selected.update(p for p in capture.parent.rglob('*') if p.is_file())
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
    for name in ('check_recording_ui_live.py','test_recording_ui_dos.py','check_command_menu_live.py',
                 'check_recording_tx_live.py','check_recording_rx_live.py','check_program_actions_live.py',
                 'check_autostart_live.py','check_terminal_zmodem_live.py','check_config_far_live.py','test_terminal_capture_dos.py'):
        keep_imports(ROOT/'standalone'/name)
    for name in ('ui-menu.stdout','ui-menu.stderr','ui-final-ABI.stderr'):
        selected.add(ROOT/'build/recording-file'/name)
    cohort.mkdir();custody=cohort/'accepted';custody.mkdir();kept={}
    for path in sorted(selected):
        copy=custody/path.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,copy);assert sha(copy)==sha(path)
        kept[str(copy.relative_to(ROOT))]=sha(copy)
    result=dict(passed=True,foreground_recording_workflows_accepted=True,full_F13_accepted=False,
        variants=variants,regressions=regressions,actual_DOS_Record=dos_proofs,
        actual_DOS_capture=dict(result=str(capture.relative_to(ROOT)),sha256=sha(capture),cases=11),
        custody_sha256=kept,
        scope='Selected80x25 keyboard File/C start/save, File/D cancel and File/F recovery workflows. '
              'Actual DOS new/replacement recordings compile and exactly replay accepted user bytes; '
              'query replies are excluded and cancellation preserves original bytes. Explicit asserted-DTR '
              'baseline is retained for the standalone ASPECT lease. All sampled hardware restores. '
              'Nine compiled actor guards and both checked same-CS far-return UI call frames are bound. '
              'Linked faults are kernel/hardware models, distinct from actual DOS operations. '
              'No full original UI, complete ASPECT language, runtime mouse, current BBS/audio, physical '
              'modem or full F01-F16 application acceptance.')
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,custody_files=len(kept))))


if __name__=='__main__':main()
