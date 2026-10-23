#!/usr/bin/env python3
"""Audit the combined directory/ASPECT terminal's shared banked EXEC boundary."""
import argparse,hashlib,json,shutil
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cohort',type=Path,required=True)
    a=ap.parse_args();out=a.cohort.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    base=ROOT/'build/terminal-directory-keys-process-bank'
    m=read(base/'manifest.json');assert m['banked_process'] and m['experimental_directory_keys']
    assert not m['terminal_exit_guard'] and not m['terminal_traps']
    assert m['binary_sha256']==sha(base/'TERMINAL.EXE')
    layout=inspect_terminal_memory(base/'TERMINAL.EXE',base/'terminal.map')
    assert layout==m['memory_layout']
    assert layout['process_bridge_pairs_verified']==1 and layout['process_near_entry_bytes']==22
    assert layout['process_bank_bytes']==635 and layout['resident_code_bytes']==64876
    assert layout['resident_code_spare_bytes']==660 and layout['near_bytes']==65520
    proof_path=ROOT/'build/directory-keys/banked-source-01/result.json'
    proof=read(proof_path);assert proof['passed'] and proof['original_inputs']==[]
    assert len(proof['products'])==4
    for p,h in proof['products'].items():assert sha(ROOT/p)==h,p
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py')
    linked_path=ROOT/'build/directory-keys/banked-linked-01/result.json'
    linked=read(linked_path)
    assert linked['passed'] and linked['inputs']==292 and linked['binary_sha256']==m['binary_sha256']
    sources={};files=[base/'manifest.json',base/'TERMINAL.EXE',base/'terminal.map',proof_path,linked_path]
    runs=[]
    for case,port in [('selected',1),('script',2),('bad-key',1)]:
        p=ROOT/('build/directory-keys/banked-'+case+'-01/result.json');r=read(p)
        assert r['passed'] and all(r['checks'].values()) and r['banked_process']
        assert r['case']==case and r['port']==port and r['binary_sha256']==m['binary_sha256']
        folder=ROOT/('build/connection-dos/dirkeys-banked-'+case+'-01')
        wire=(folder/'serial.bin').read_bytes()
        if case!='bad-key':assert bytes.fromhex(r['expected_wire_hex']) in wire
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        files.append(p)
        files.extend(folder/n for n in ['result.json','serial.bin','BEFORE.BIN','AFTER.BIN','PASS.TXT','dosbox.conf','dosbox.log','SCREEN.BIN'])
        runs.append(dict(case=case,port=port,checks=r['checks'],wire_sha256=sha(folder/'serial.bin')))
        for n,h in r['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for receipt in [m,proof,linked]:
        for n,h in receipt['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    files.extend(ROOT/n for n in sources)
    files.extend([Path(__file__).resolve(),ROOT/'nix/flake.nix',ROOT/'nix/flake.lock',ROOT/'tools/dev'])
    out.mkdir(parents=True);custody={}
    for p in sorted(set(files)):
        dst=out/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dst);assert sha(dst)==sha(p)
        custody[str(dst.relative_to(ROOT))]=sha(dst)
    report=dict(passed=True,binary_sha256=m['binary_sha256'],memory_layout=layout,
        linked_inputs=292,DOS_runs=runs,source_files=proof['source_files'],products=proof['products'],
        custody_sha256=custody,terminal_HOOK_accepted=False,full_application_accepted=False,
        scope='Combined selected-directory KEY/ASPECT terminal with shared near/far banked EXEC. Linked bindings, three actual DOS serial sessions and four empty-tree rebuilt products only. No HOOK route or live PRM commit, combined exit guard/traps, BBS acceptance or physical hardware validation.')
    (ROOT/'docs/validation/directory-process-bank.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS shared process bank,292 linked inputs,three DOS runs,four source products')
if __name__=='__main__':main()
