#!/usr/bin/env python3
"""Independently inspect selected directory bytes, imported files and DOS wire data."""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('selection','cohort','output'):ap.add_argument('--'+name,required=True)
    a=ap.parse_args();selection=read(ROOT/a.selection);cohort=ROOT/a.cohort
    assert cohort.is_relative_to(ROOT/'build');cohort.mkdir(parents=True,exist_ok=False)
    sources={};custody={};accepted=[];coverage=set()
    def source_check(d):
        for n,h in d.get('sources',{}).items():
            assert n not in sources or sources[n]==h,n
            assert sha(ROOT/n)==h,n;sources[n]=h
    def keep(p):
        dest=cohort/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        assert sha(p)==sha(dest);custody[str(dest.relative_to(ROOT))]=sha(dest)
    parent=ROOT/'build/terminal-directory-keys/TERMINAL.EXE';manifest=read(parent.parent/'manifest.json')
    assert manifest['experimental_directory_keys'] and manifest['data_stack_bytes']==65520;source_check(manifest)
    expected={'selected':b'DIRKEY\rDIRKBDready','script':b'DIRSCRIPT\rDIRKBDready','environment':b'ENVKEY\rENVKBDready','cwd-first':b'DIRKEY\rDIRKBDready','cli':b'CLIKEY\rCLIKBDready','fallback':b'DIRKEY\rFALLBACKready','missing':b'\x1bOPready','blank':b'\x1bOPready'}
    for name in selection['DOS']:
        run=ROOT/name;d=read(run/'result.json');assert d['passed'] and all(d['checks'].values());source_check(d)
        case=d['case'];coverage.add(case);folder=ROOT/'build/connection-dos'/('dirkeys-'+run.name)
        assert sha(run/'package/TERMINAL.EXE')==sha(parent)==d['binary_sha256']
        before=(folder/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(folder/'AFTER.BIN').read_bytes()
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
        raw=(folder/'TEST.DIR').read_bytes();assert len(raw)==23050
        if case=='bad-name':assert raw[250+0x56:250+0x56+9]==b'CON'+bytes(6)
        elif case=='blank':assert raw[250+0x56:250+0x56+9]==b' \0ignore!'
        else:
            assert raw[250+0x56:250+0x56+9]==b'actions'+bytes(2)
            assert raw[250+0x5f:250+0x5f+9]==b'board'+bytes(4)
        wire=(folder/'serial.bin').read_bytes();config=(folder/'dosbox.conf').read_text()
        if case.startswith('bad-'):assert wire==b'' and d['commands']==[] and d['expected_exit']==7
        else:
            assert expected[case] in wire and bytes.fromhex(d['expected_wire_hex'])==expected[case]
            assert d['commands'][:2]==['ATZ','ATDCaseTest:23'] and d['expected_exit']==0
            assert d['checks']['directory_expected_updates_only']
        assert (' /T:' in d['command'])==(case=='cli')
        assert (' /K:' in d['command'])==(case=='cli')
        assert 'a-1' in config and 'f1' in config
        if case=='bad-key':assert (folder/'ACTIONS.KEY').stat().st_size==539
        if case=='bad-kbd':assert (folder/'BOARD.KBD').stat().st_size==947
        if case in ('missing','blank'):
            assert not any((folder/n).exists() for n in ['ACTIONS.KEY','BOARD.KBD','PCPLUS.KBD'])
        if case=='environment':assert not (folder/'ACTIONS.KEY').exists() and (folder/'ENV/ACTIONS.KEY').stat().st_size==540
        if case=='fallback':assert not (folder/'BOARD.KBD').exists() and (folder/'PCPLUS.KBD').stat().st_size==948*7
        if case=='script':assert struct.unpack_from('<H',(folder/'ACTIONS.KEY').read_bytes())[0]==0
        for directory in (run,folder):
            for p in sorted(directory.rglob('*')):
                if p.is_file():keep(p)
        accepted.append(dict(case=case,port=d['port'],path=name))
    assert coverage==set(expected)|{'bad-key','bad-kbd','bad-name'}
    model=read(ROOT/selection['linked']/'result.json');assert model['passed'] and model['inputs']==292;source_check(model)
    proof=read(ROOT/selection['proof']/'result.json');source_check(proof)
    assert proof['passed'] and proof['source_files']==662 and proof['original_inputs']==[] and len(proof['products'])==4
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py')
    for n,h in proof['products'].items():assert sha(ROOT/n)==h,n
    baseline=read(ROOT/selection['baseline']/'result.json');assert len(baseline)==3
    for item in baseline:assert item['unchanged'] and sha(ROOT/item['product'])==item['sha256']
    bbs=read(ROOT/selection['bbs']);assert bbs['passed'] and bbs['directory_keys']
    for n,h in bbs['custody_sha256'].items():assert sha(ROOT/n)==h;custody[n]=h
    for name in ('linked','proof','baseline'):
        for p in sorted((ROOT/selection[name]).rglob('*')):
            if p.is_file():keep(p)
    for n,h in sources.items():
        target=cohort/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target);custody[str(target.relative_to(ROOT))]=h
    for p in [Path(__file__),ROOT/a.selection,ROOT/selection['bbs'],ROOT/'Makefile',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock']:keep(p)
    for label in ['build/directory-keys-build-01.log','build/directory-keys-build-02.log']:
        p=ROOT/label
        if p.exists():keep(p)
    result=dict(passed=True,selected_directory_KEY_KBD_accepted=True,full_F05_accepted=False,full_F07_accepted=False,full_application_accepted=False,
        DOS_sessions=11,linked_inputs=292,BBS_sessions=4,source_files=662,products=proof['products'],selection=selection,accepted=accepted,custody_sha256=custody,
        early_attempts=['First compile used the wrong retained-context member spelling; corrected to selection.record.','First link reached64KiB DGROUP because of new suffix strings; stack-built names restore the preceding65520-byte footprint.','First BBS harness preparation lacked a Python re import; it failed before launching DOS.'],
        scope='Optional selected-directory KEY action and META KBD imports at startup, explicit CLI precedence, readonly current/PCPLUS lookup and missing fallback. Raw directory/wire/hardware and current BBS Alt-1 replay without /T accepted. Maintained basename validation and pre-UART admission differ from native post-connect mutation; no KEY auto-creation, factory defaults, general directory switching, arbitrary faults, other DOS kernels, physical modem or full application acceptance.')
    output=ROOT/a.output;output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(custody),'preserved files')
if __name__=='__main__':main()
