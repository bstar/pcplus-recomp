#!/usr/bin/env python3
"""Bind actual DOS owned-reset outcomes, source reproduction and retained failures."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('dos','proof','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();dos=args.dos.resolve();proof=args.proof.resolve();base=ROOT/'build/terminal-reset-shadow'
    m=read(base/'manifest.json');d=read(dos/'result.json');s=read(proof/'result.json')
    assert m['shadow_owner']and m['viewport_bound']and m['data_stack_bytes']<=65536
    assert d['passed']and not d['timed_out']and d['cpu']=='8086'
    assert d['binary_sha256']==s['binary_sha256']==m['binary_sha256']==sha(base/'RESET.EXE')==sha(dos/'RESET.EXE')
    assert s['passed']and s['original_inputs']==[]and s['normal_owner_compiled']and s['source_files']==66
    assert s['sources']==m['sources']and s['checker_sha256']==sha(ROOT/'standalone/prove_shadow_reset_source.py')
    assert sha(proof/'source/build/terminal-reset-shadow/RESET.EXE')==m['binary_sha256']
    assert sha(base/'shadow-owner-normal.obj')==m['normal_owner_object_sha256']
    assert s['build_log_sha256']==sha(proof/'build.log')
    sources={}
    for report in [m,d,s]:
        for name,digest in report['sources'].items():assert sha(ROOT/name)==digest;sources[name]=digest
    for name,digest in m['sources'].items():assert sha(dos/'inputs'/name)==sha(proof/'source'/name)==digest
    assert(dos/'PASS.TXT').is_file()and not(dos/'FAIL.TXT').exists()
    match=re.fullmatch(r'PASS (\d+) checks allocations=(\d+) releases=(\d+) entry_flags=([0-9a-f]+)\s*',d['report'])
    assert match and tuple(map(int,match.group(1,2,3)))==(77,43,43)
    boot=struct.unpack('<4H',(dos/'BOOT.BIN').read_bytes())
    assert list(boot)==d['boot']and boot[0]==boot[1]and(boot[3]&0x600)==0x200
    assert m['data_stack_bytes']-4096<boot[2]<=m['data_stack_bytes']
    trace=(dos/'TRACE.TXT').read_text().splitlines();assert len(trace)==77
    for marker in ['actual DOS snapshot allocation failure','actual DOS native shadow allocation failure',
                   'real native exhaustion rolls back all state','reused shadow bytes restore exactly',
                   'old allocation and all state survive rollback','foreign release leaves state unchanged',
                   'nested request rejected before allocation','IF-disabled admission refused','DF-set admission refused',
                   'closed wide view rejects reuse before reinitialization','DOS largest free block restored exactly']:
        assert marker in trace,marker
    old=ROOT/'build/shadow-reset-dos-07';failure=read(old/'result.json')
    assert not failure['passed']and failure['timed_out']and sha(old/'RESET.EXE')==failure['binary_sha256']
    for name,digest in failure['sources'].items():
        if name!='standalone/test_shadow_reset_dos.py':assert sha(old/'inputs'/name)==digest,name
    assert(old/'TRACE.TXT').read_text().splitlines()[-1]=='retained release retries'
    assert 'closed wide view rejects reuse'not in(old/'inputs/standalone/shadow_reset_driver.c').read_text()
    assert 'shadow_viewport_enabled'not in(old/'inputs/src/ui/shadow_owner.c').read_text()
    prior=read(ROOT/'docs/validation/viewport-panes.json');controls={}
    for name,expected in [('terminal-reset','8bdd8c62707ef4c1761c734a9481cad18be991aeed3cadd6194c527f14408e32'),
                          ('terminal-reset-viewport',prior['products']['build/terminal-reset-viewport/RESET.EXE'])]:
        assert sha(ROOT/'build'/name/'RESET.EXE')==expected;controls[name]=expected
    regression=read(ROOT/'build/terminal-reset/checks-original.json')
    assert regression['passed']and regression['genuine_original_comparisons']==47
    joined=read(ROOT/'build/terminal-reset-viewport/viewport-checks.json');assert joined['passed']and len(joined['cases'])==10
    evidence=[]
    for index in (0,1):
        path=ROOT/f'analysis/shadow-allocator-{index}-20261024.rea.json';e=read(path)
        assert e['authority']=='shipped-artifact'
        evidence.append(dict(evidence_id=e['evidence_id'],inline_evidence_sha256=sha(path)))
    artifacts={}
    for folder in [dos,proof,old,ROOT/'build/shadow-reset-timeout-02',ROOT/'build/shadow-reset-trace-timeout-03']:
        for path in folder.rglob('*'):
            if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    for number in (3,4,5,6):
        folder=ROOT/f'build/shadow-reset-dos-{number:02d}'
        assert not read(folder/'result.json')['passed']
        for leaf in ['result.json','dosbox.log','TRACE.TXT','BOOT.BIN']:
            path=folder/leaf
            if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    for name in ['Makefile','standalone/record_shadow_reset.py','nix/flake.nix','nix/flake.lock']:
        sources[name]=sha(ROOT/name)
    result=dict(passed=True,application_integrated=False,binary_sha256=m['binary_sha256'],data_stack_bytes=m['data_stack_bytes'],
                dos_checks=77,owned_allocations=43,owned_releases=43,largest_free_block_restored=True,
                source_files=66,original_inputs=[],sources=sources,artifacts=artifacts,evidence=evidence,
                unchanged_controls=controls,prior_reset_comparisons=47,prior_cursor_reset_cases=10,
                retained_failure=dict(label=old.name,accepted=False,reason='Reset attempted after freeing a wide viewport; committed trace ends after release retry. Current admission refuses that inconsistent state until reinitialization.'),
                scope='Actual DOS8086 native width/reset/geometry plus authored DOS-memory transaction, full native image/video/shadow byte comparisons, BIOS cursor restoration, real DOS allocation exhaustion and requested typed faults. Frame/old storage retained until commit; guard/release errors retain ownership. Mode3/page0/80 physical by24 logical rows only. No arbitrary async recovery, live application/BBS/UI binding, physical video, package/card or full-application claim.')
    args.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS owned shadow-reset evidence, DOS pressure, exact rollback and source proof')


if __name__=='__main__':main()
