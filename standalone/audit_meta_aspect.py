#!/usr/bin/env python3
"""Check raw KEY action inputs, DOS/wire samples and source/product custody."""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('selection','cohort','output'):ap.add_argument('--'+name,required=True)
    a=ap.parse_args();selection=read(ROOT/a.selection);cohort=ROOT/a.cohort
    assert cohort.is_relative_to(ROOT/'build');cohort.mkdir(parents=True,exist_ok=False)
    custody={};sources={};accepted=[];coverage=set()
    def source_check(d):
        for n,h in d.get('sources',{}).items():
            assert n not in sources or sources[n]==h,n
            assert sha(ROOT/n)==h,n;sources[n]=h
    def keep(p):
        target=cohort/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,target);assert sha(p)==sha(target);custody[str(target.relative_to(ROOT))]=sha(target)
    terminal=ROOT/'build/terminal-aspect-keys/TERMINAL.EXE'
    child=ROOT/'build/aspect-help-resource-parent/ASPECT.EXE'
    manifest=read(terminal.parent/'manifest.json');assert manifest['experimental_aspect_keys'] and not manifest.get('original_inputs',[])
    assert sha(terminal)==manifest['binary_sha256'];source_check(manifest)
    for name in selection['DOS']:
        run=ROOT/name;d=read(run/'result.json');assert d['passed'] and all(d['checks'].values());source_check(d)
        case=d['case'];port=d['port'];coverage.add((case,port))
        folder=ROOT/'build/connection-dos'/('aspect-key-'+run.name)
        before=(folder/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(folder/'AFTER.BIN').read_bytes()
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
        assert sha(run/'package/TERMINAL.EXE')==sha(terminal)==d['binary_sha256']
        key=(folder/'TEST.KEY').read_bytes();assert len(key)==540
        index=9 if port==2 else 0
        for i in range(10):assert struct.unpack_from('<H',key,i*54)[0]==(0 if i==index else 3)
        filename=key[54*index+2:54*(index+1)].split(b'\0',1)[0]
        assert filename==(b'' if case=='empty' else b'TEST' if case=='serial' else b'TEST.ASP' if case=='source' else b'TEST.ASX')
        if case=='missing':assert not (run/'package/ASPECT.EXE').exists()
        else:assert sha(run/'package/ASPECT.EXE')==sha(child)==d['child_sha256']
        wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()[::2]
        count=2 if case=='repeat' else 0 if case in ('missing','empty','bad-script') else 1
        assert wire.count(b'KEYSTART\r')==wire.count(b'KEYDONE\r')==count
        assert b'ready' in wire and b'ATZ\rATDCaseTest:23\r' in wire
        if case=='serial':assert screen[9*80:9*80+13]==b'KEY REMAINDER'
        if case=='source':
            from sys import path
            path.insert(0,str(ROOT/'src/aspect'));from compiler import compile_source
            assert (folder/'TEST.ASX').read_bytes()==compile_source((folder/'TEST.ASP').read_text())
            assert sha(run/'package/ASPCOMP.EXE')==sha(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE')
        config=(folder/'dosbox.conf').read_text();assert ('a-0' if index else 'a-1') in config and '/T:D:' in config
        for directory in (run,folder):
            for p in sorted(directory.rglob('*')):
                if p.is_file():keep(p)
        accepted.append(dict(case=case,port=port,path=name))
    assert coverage=={('serial',1),('serial',2),('missing',1),('empty',2),('repeat',1),('source',2),('bad-script',1)}
    linked=read(ROOT/selection['linked']/'result.json');source_check(linked)
    assert linked['passed'] and linked['inputs']==40 and sha(terminal)==linked['binary_sha256']
    proof=read(ROOT/selection['proof']/'result.json');source_check(proof)
    assert proof['passed'] and proof['original_inputs']==[] and proof['source_files']==660 and len(proof['products'])==4
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_meta_aspect_source.py')
    for n,h in proof['products'].items():assert sha(ROOT/n)==h,n
    baseline=read(ROOT/selection['baseline']/'result.json')
    for item in baseline:assert item['unchanged'] and sha(ROOT/item['product'])==item['sha256']
    bbs=read(ROOT/selection['bbs']);assert bbs['passed'] and bbs['aspect_keys']
    for n,h in bbs['custody_sha256'].items():assert sha(ROOT/n)==h;custody[n]=h
    for name in ('linked','proof','baseline'):
        for p in sorted((ROOT/selection[name]).rglob('*')):
            if p.is_file():keep(p)
    for label in selection.get('earlier_failures',[]):
        failed=ROOT/'build/aspect-keys'/label
        d=read(failed/'result.json');assert not d['passed'];keep(failed/'result.json')
        folder=ROOT/'build/connection-dos'/('aspect-key-'+label)
        for leaf in ['result.json','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','serial.bin','dosbox.conf']:
            p=folder/leaf
            if p.is_file():keep(p)
        for leaf in ['standalone/test_aspect_keys_dos.py','standalone/test_meta_aspect_dos.py']:
            p=failed/'source'/leaf
            if p.is_file():keep(p)
    for n,h in sources.items():
        assert sha(ROOT/n)==h
        target=cohort/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
        custody[str(target.relative_to(ROOT))]=h
    for p in [Path(__file__),ROOT/a.selection,ROOT/selection['bbs'],ROOT/'Makefile',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock']:keep(p)
    result=dict(passed=True,selected_global_KEY_ASPECT_accepted=True,HOOK_accepted=False,full_F05_accepted=False,full_application_accepted=False,
        DOS_sessions=7,linked_inputs=40,BBS_sessions=4,source_files=660,products=proof['products'],accepted=accepted,selection=selection,custody_sha256=custody,
        early_attempts=['Initial DOS fixture lacked required mouse scale words; terminal rejected startup.','Second fixture placed ASPECT outside required executable sibling directory; Script owner rejected launch and resumed. Corrected packaging passes.'],
        scope='Optional global /T kind0 ASPECT entry into existing foreground Script owner. Raw hardware/wire/file checks, linked model, source-only reproduction and current Alt-1 ENiGMA/Synchronet replay. BBS wrapper exercises failed and successful DOS children. Physical UART/modem, other DOS kernels, arbitrary combined faults, directory KEY/META, HOOK and full application remain open.')
    output=ROOT/a.output;output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',len(custody),'preserved files')
if __name__=='__main__':main()
