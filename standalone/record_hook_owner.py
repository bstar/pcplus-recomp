#!/usr/bin/env python3
"""Audit raw HOOK allocation/EXEC reports and preserve both DOS backend variants."""
import argparse,hashlib,json,re,shutil,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cohort',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    cohort=ROOT/a.cohort;assert cohort.is_relative_to(ROOT/'build');cohort.mkdir(parents=True,exist_ok=False)
    custody={};sources={};accepted=[]
    def keep(path):
        target=cohort/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        assert sha(path)==sha(target);custody[str(target.relative_to(ROOT))]=sha(target)
    sys.path.insert(0,str(ROOT/'standalone'));from omf_imports import records,externals
    for label,count,generation,production in [('DOS-final-02',239,25,False),('production-final-02',236,26,True)]:
        folder=ROOT/'build/hook-owner'/label;d=read(folder/'result.json')
        assert d['passed'] and all(d['checks'].values()) and d['self_checks']==count and d['generations']==generation and d['production_backend']==production and d['original_inputs']==[]
        assert (folder/'OUTPUT.TXT').read_bytes()==('HOOKOWNER checks=%u failures=0 generation=%u\r\n'%(count,generation)).encode()
        assert sha(folder/'HOWNER.EXE')==sha(folder/'rebuild/HOWNER.EXE')==d['binary_sha256']
        assert sha(folder/'HOOKCH.EXE')==sha(folder/'rebuild/HOOKCH.EXE')==d['helper_sha256']
        report=(folder/'HOWNER.RPT').read_bytes();assert len(report)==538
        w=struct.unpack_from('<12H',report);assert w[:4]==(0x484f,count,0,generation)
        psp,keep_paras,stacktop,heap_end,free_before,free_after,printed,file_size=w[4:]
        assert free_before==free_after and printed>0 and file_size==14
        assert report[24:44]==report[44:64] and report[64:320]==bytes(256)
        assert report[320:320+file_size]==report[384:384+file_size]
        listing=(folder/'HOWNER.map').read_text();group=re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I);assert group
        ds=psp+16+int(group[1],16);assert (ds-psp)*16+max(stacktop,heap_end)<=keep_paras*16
        state=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[ *+]+_hook_diagnostic_state\s*$',listing,re.M|re.I);assert state
        assert (16+int(state[1],16))*16+int(state[2],16)+84<=keep_paras*16
        cases=list(struct.iter_unpack('<9H',report[448:]));assert [x[0] for x in cases]==[3,4,5,6,7]
        for context,status,phase,process,child,segment,owner,guard,gen in cases:
            assert status==(2 if context in (5,6) else 0) and phase==4 and process==0 and child==(23 if context==7 else 0)
            assert segment>psp and segment+133<=65536 and owner==(psp^1 if context==6 else psp)
            expected=(0xa5^gen^psp^context)&255;assert guard==(expected^1 if context==5 else expected)
        frame=(folder/'HCHILD.BIN').read_bytes();assert len(frame)==2094
        expected_a=bytes(((128+i*17)&255)^0x3c for i in range(20));expected_b=bytearray(128+i%127 for i in range(810))
        for i in range(10):expected_b[i*81+i]=0
        expected_b[0]=1;expected_b[80]=0
        for i in range(10):expected_b[i*81:i*81+3]=bytes([72,48+i,0])
        expected_p=bytes(((i*37)&255)^0x5a for i in range(1264));assert frame==expected_a+expected_b+expected_p
        imports={n.decode() for kind,body,_ in records((folder/'hook_owner.obj').read_bytes()) if kind==0x8c for n,_ in externals(body)}
        assert imports=={'_small_code_','_hook_exchange_pack','_hook_exchange_unpack','_hook_key_format','_hook_key_spans','_hook_platform_allocate','_hook_platform_busy','_hook_platform_execute','_hook_platform_prepare','_hook_platform_psp','_hook_platform_release'}
        if production:assert b'_hook_test_' not in (folder/'hook_owner_dos.obj').read_bytes() and '_hook_test_' not in listing
        for n,h in d['sources'].items():
            assert n not in sources or sources[n]==h,n
            assert sha(ROOT/n)==sha(folder/'source'/n)==h,n;sources[n]=h
        for path in sorted(folder.rglob('*')):
            if path.is_file():keep(path)
        accepted.append(dict(path=str(folder.relative_to(ROOT)),checks=count,generations=generation,production_backend=production,raw_cases=[list(c) for c in cases]))
    for name in ['DOS-01','DOS-02','DOS-05','DOS-08']:
        folder=ROOT/'build/hook-owner'/name
        for leaf in ['result.json','OUTPUT.TXT','HOWNER.RPT','dosbox.log','hook_owner_diagnostic.err','source/standalone/hook_owner_diagnostic.c','source/standalone/hook_owner_support.asm']:
            path=folder/leaf
            if path.is_file():keep(path)
    for path in [Path(__file__),ROOT/'standalone/omf_imports.py',ROOT/'Makefile',ROOT/'tools/dev',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock']:keep(path)
    result=dict(passed=True,standalone_HOOK_owner_accepted=True,terminal_HOOK_accepted=False,full_application_accepted=False,
        diagnostic_checks=239,production_backend_checks=236,allocation_generations=[25,26],sources=sources,accepted=accepted,custody_sha256=custody,
        early_attempts=['Warnings-as-errors caught far qualifiers applying only to the first fixture declarator.','The diagnostic first used the address of Watcom STACKTOP instead of its value, releasing live memory; corrected and added active-stack admission.','Static stack bounds alone omitted a live CRT heap buffer; retaining curbrk preserves heap canary and stdout.','Fault-control variables also required separate far declarations; wrong-segment fixture writes were corrected.','The first duplicate-link recipe shadowed parsed options with expected-frame bytes; corrected before accepted source-bound runs.'],
        scope='Two actual8086 DOS standalone owner variants with real source helper EXEC, memory/MCB/guard/PSP checks, repeat/free restoration, exact returned bytes, JFT/FILE/heap/foreign-block preservation and context rejection. Both binaries reproduce from fresh objects; normal backend contains no fault controls. Caller supplies complete resident/heap limit and suspended external owners. No terminal kind2 routing, UART/UI handoff, live PRM commit, general asynchronous recovery/unload, other DOS kernels or physical hardware acceptance.')
    output=ROOT/a.output;output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(custody),'preserved files')
if __name__=='__main__':main()
