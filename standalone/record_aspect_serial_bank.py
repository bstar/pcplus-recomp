#!/usr/bin/env python3
"""Bind the serial-bank placement audit to raw DOS/BBS and source evidence."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cohort',type=Path,required=True);a=ap.parse_args()
    out=a.cohort.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    base=ROOT/'build/aspect-serial-bank-parent';m=read(base/'manifest.json');old=ROOT/'build/aspect-help-resource-parent';om=read(old/'manifest.json')
    assert m['experimental_serial_bank'] and not om['experimental_serial_bank']
    assert sha(base/'ASPECT.EXE')==m['binary_sha256'] and sha(old/'ASPECT.EXE')==om['binary_sha256']
    linked_path=ROOT/'build/aspect-serial-bank/linked-01/result.json';linked=read(linked_path)
    assert linked['passed'] and linked['bridge_pairs']==23 and linked['C_instruction_bytes_identical']==3415 and linked['near_code_saved']==3104
    assert linked['binary_sha256']==m['binary_sha256'] and linked['baseline_sha256']==om['binary_sha256']
    assert linked['baseline_object_sha256']==sha(old/'serial.o') and linked['banked_object_sha256']==sha(base/'serial.o')
    scripts=ROOT/'build/aspect-script-serial-dos';s=read(scripts/'checks.json')
    assert s['passed'] and s['original_inputs']==[] and len(s['cases'])==28 and s['runner_sha256']==m['binary_sha256']
    assert s['checker_sha256']==sha(ROOT/'standalone/test_aspect_script_serial_dos.py')
    for r in s['cases']:
        assert r['passed'] and all(r['checks'].values())
        folder=scripts/r['name'];assert sha(folder/'ASPECT.EXE')==m['binary_sha256']
        assert (folder/'RETURN.BIN').read_bytes().hex()==r['returned_hex']
        assert (folder/'LEASE.BIN').read_bytes().hex()==r['descriptor_hex']
        assert 'cputype=8086' in (folder/'dosbox.conf').read_text()
    full=ROOT/'build/aspect-parent-process-mouse-serial-bank/serial-bank-full-high-01';f=read(full/'result.json')
    assert f['passed'] and len(f['cases'])==2 and f['child_sha256']==m['binary_sha256']
    assert f['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py')
    assert sum(len(r['checks']) for r in f['cases'])==112
    for r in f['cases']:
        assert r['passed'] and all(r['checks'].values());folder=full/r['case']
        assert 'LH D:\\RENDER T' in (folder/'dosbox.conf').read_text()
        assert (folder/'CHILD.LOG').read_bytes()==b'GTWRGT'
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        assert b'Synth42\r' in (folder/'serial.bin').read_bytes() and b'ready' in (folder/'serial.bin').read_bytes()
        assert (folder/'NEXT.ASX').exists()
    early=ROOT/'build/aspect-parent-process-mouse-serial-bank/serial-bank-full-01';e=read(early/'result.json')
    assert not e['passed']
    for r in e['cases']:
        assert not r['passed'] and any(x['name']=='C:\\ASPCOMP.EXE' and x['carry']==1 and x['result']==8 for x in r['nested_EXEC'])
        assert 'LH D:\\RENDER T' not in (early/r['case']/'dosbox.conf').read_text()
    bbs=ROOT/'build/aspect-serial-bank/BBS-DOS-01';b=read(bbs/'checks.json')
    assert b['passed'] and b['original_inputs']==[] and len(b['cases'])==2 and b['runner_sha256']==m['binary_sha256']
    assert b['checker_sha256']==sha(ROOT/'standalone/test_aspect_serial_bbs.py')
    assert b['driver_checker_sha256']==sha(ROOT/'standalone/test_aspect_script_serial_dos.py')
    assert b['modem_source_sha256']==sha(ROOT/'lab/bbs/modem.py')
    for r in b['cases']:
        assert r['passed'] and all(r['checks'].values());folder=bbs/r['name']
        assert r['runner_sha256']==m['binary_sha256']
        for n,h in r['files'].items():assert sha(folder/n)==h,n
        assert (folder/'RETURN.BIN').read_bytes().hex()==r['returned_hex'] and (folder/'LEASE.BIN').read_bytes().hex()==r['descriptor_hex']
    proof_path=ROOT/'build/aspect-serial-bank/source-01/result.json';proof=read(proof_path)
    assert proof['passed'] and proof['original_inputs']==[] and proof['source_files']==685 and len(proof['products'])==6
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py')
    for n,h in proof['products'].items():assert sha(ROOT/n)==h,n
    sources={}
    for r in [m,om,linked,proof]:
        for n,h in r['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n,h in f['source_hashes'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n in ['standalone/test_aspect_script_serial_dos.py','standalone/fixtures/aspect_serial_vectors.json','standalone/test_aspect_serial_bbs.py','lab/bbs/modem.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    files=[ROOT/n for n in sources]+[linked_path,proof_path,proof_path.parent/'build.log']
    for folder in [base,old]:files.extend(folder/n for n in ['manifest.json','ASPECT.EXE','ASPECT.map','serial.o'])
    for folder in [scripts,full,early,bbs]:files.extend(p for p in folder.rglob('*') if p.is_file() and not set(p.relative_to(folder).parts)&{'source','sources'})
    files.extend([Path(__file__).resolve(),ROOT/'Makefile',ROOT/'tools/dev',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock'])
    out.mkdir(parents=True);custody={}
    for p in sorted(set(files)):
        target=out/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        assert sha(target)==sha(p);custody[str(target.relative_to(ROOT))]=sha(target)
    report=dict(passed=True,bridge_pairs=23,unchanged_serial_instruction_bytes=3415,near_code_saved=3104,
        DOS_script_cases=28,attached_DOS_checks=112,attached_DOS_cases=[r['configuration'] for r in f['cases']],BBS_greetings=[r['name'] for r in b['cases']],
        source_files=685,products=proof['products'],custody_sha256=custody,register_handback_accepted=False,terminal_HOOK_accepted=False,full_application_accepted=False,
        scope='Serial controller placement/ABI only. Unchanged C instructions,23 bridge pairs,28 actual8086 serial script cases,two attached COM1/2 workflows with observer high,read-only owned local BBS greetings,six source-only products. Low-observer DOS8 attempts retained. ASIO still v1..v6; no register handback/full compatibility/hardware acceptance.')
    (ROOT/'docs/validation/aspect-serial-bank.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS23 bridges,28 DOS cases,112 attached checks,two BBS greetings,685 sources/six products')
if __name__=='__main__':main()
