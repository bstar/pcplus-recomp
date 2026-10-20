#!/usr/bin/env python3
"""Audit same-session CLI retry from raw DOS/MCB/callback/owner evidence."""
import argparse,json,re,struct
from pathlib import Path
from build_aspect_process import ROOT,sha
from record_parent_exit import mouse_evidence

def read(path):return json.loads(path.read_text())
def current(sources):
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
def symbols(path):
    return {n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',path.read_text(),re.M|re.I)}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label',action='append',required=True)
    p.add_argument('--mouse-label',action='append',required=True)
    p.add_argument('--source-label',required=True)
    p.add_argument('--normal-control',required=True);p.add_argument('--exit-control',required=True)
    args=p.parse_args()
    for label in [*args.label,*args.mouse_label,args.source_label,args.normal_control,args.exit_control]:assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    child=ROOT/'build/aspect-exit-retry/ASPECT.EXE'
    manifest=read(child.parent/'manifest.json');current(manifest['sources'])
    assert manifest['exit_probe_attached'] and manifest['exit_probe_retry']
    syms=symbols(child.parent/'ASPECT.map');seg,off=syms['_aspect_exit_foreign']
    names=('seen returned status carry psp child_function child_code nested_calls nested_carry '
        'nested_lease resources_equal final_lease vector_before_off vector_before_seg '
        'vector_after_off vector_after_seg retained_owner retained_paras callback_before '
        'callback_after extra_owner extra_paras extra_word jft_equal owners_equal '
        'exec_error largest_free observer_segment nested_status nested_kernel_flags nested_caller_flags').split()
    assert len(names)==31
    routes=[];seen=set();evidence={}
    for mouse,labels in [(False,args.label),(True,args.mouse_label)]:
        parent=ROOT/('build/terminal-mouse-process/TERMINAL.EXE' if mouse else 'build/terminal-process/TERMINAL.EXE')
        for label in labels:
            folder=ROOT/('build/aspect-parent-exit-mouse-retry' if mouse else 'build/aspect-parent-exit-retry')/label
            run=read(folder/'result.json')
            assert run['passed'] and run['same_session_retry'] and run['exit_probe'] and run['experimental_mouse']==mouse
            assert run['parent_sha256']==sha(parent) and run['child_sha256']==sha(child)
            assert run['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py')
            assert run['observer_sha256']==sha(folder/'RENDER.COM');current(run['source_hashes'])
            for name,digest in run['source_hashes'].items():assert sha(folder/'sources'/name)==digest,name
            for case in run['cases']:
                sub=folder/case['case'];config=case['configuration'];key=(mouse,config['port'],config['flow'])
                assert key not in seen;seen.add(key)
                assert case==read(sub/'result.json') and case['passed'] and all(case['checks'].values())
                assert sha(sub/'TERMINAL.EXE')==sha(parent) and sha(sub/'ASPECT.EXE')==sha(child)
                raw=(sub/'RENDER.BIN').read_bytes();at=len(raw)-26-32*70-case['compared_parent_bytes']
                head=struct.unpack_from('<7H',raw);retained=struct.unpack_from('<15H',raw,at-30)
                assert head[:4]==(0x524e,1,1,1) and head[6]==10
                assert list(retained)==case['retained_words'] and retained[0]==0x31 and retained[10]==0x030a
                assert retained[1]==retained[2]==retained[4] and retained[3]==retained[5]>0
                assert retained[6:8]==(off,retained[1]+16+seg) and retained[8:10]==(0,1)
                assert retained[12:15]==(retained[1],32,0xa55a)
                start=at-30-(4150 if mouse else 0)-1334
                r=dict(zip(names,struct.unpack_from('<31H',raw,start)));assert r==case['retry_probe']
                assert (r['seen'],r['returned'],r['carry'],r['status'])==(1,1,0,0)
                assert r['psp'] not in (0,head[5],retained[1])
                assert (r['child_function'],r['child_code'])==(0x4c,0)
                assert (r['nested_calls'],r['nested_carry'],r['nested_lease'],r['nested_status'])==(1,0,1,37)
                assert r['resources_equal']==1 and r['final_lease']==0 and case['resource_words'][2]==0
                assert (r['vector_before_off'],r['vector_before_seg'])==retained[6:8]
                assert (r['vector_after_off'],r['vector_after_seg'])==retained[6:8]
                assert (r['callback_before'],r['callback_after'])==(1,2)
                assert (r['retained_owner'],r['retained_paras'])==(retained[1],retained[3])
                assert (r['extra_owner'],r['extra_paras'],r['extra_word'])==(retained[1],32,0xa55a)
                assert r['observer_segment']>=0xa000 and r['largest_free']>0 and r['nested_caller_flags']&0x200
                start+=62
                assert raw[start:start+20]==raw[start+20:start+40] and r['jft_equal']==1
                assert raw[start+40:start+456]==raw[start+456:start+872] and r['owners_equal']==1
                assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
                assert (sub/'CHILD.LOG').read_bytes()==b'GT' and (sub/'RETRY.OUT').read_bytes()==b'retry-owned'
                assert struct.unpack('<3H',(sub/'RETRYWIT.BIN').read_bytes())[0]==0
                assert struct.unpack('<10H',(sub/'RETRYDBG.BIN').read_bytes())==(37,0,0,0,0,0,0,0,1,0)
                wire=(sub/'serial.bin').read_bytes();screen=(sub/'SCREEN.BIN').read_bytes()[::2]
                assert wire.count(b'RETRY-OK\r')==1 and b'Synth42\r' not in wire
                assert b'\x1b[2;1R' in wire[wire.find(b'RETRY-OK\r')+9:] and b'ready' in wire
                assert b'RETRY COMPLETE' in screen and b'FAIL' not in screen
                assert b'ASPECT memory retained.' in screen
                route=dict(label=label,mouse=mouse,port=config['port'],flow=config['flow'],checks=len(case['checks']),
                    observer_segment=r['observer_segment'],largest_free_paragraphs=r['largest_free'],
                    retained_PSP=retained[1],retry_PSP=r['psp'],retry_status=r['status'],callback_hits=r['callback_after'],
                    nested_kernel_flags=r['nested_kernel_flags'],nested_caller_flags=r['nested_caller_flags'])
                if mouse:route['mouse']=mouse_evidence(sub,case,parent,True,resource_copies=1)
                routes.append(route)
                files=['RENDER.BIN','EXITWIT.BIN','RETRYWIT.BIN','RETRYDBG.BIN','CHILD.LOG','RETRY.OUT','serial.bin','SCREEN.BIN','result.json','dosbox.conf']
                evidence[str(sub.relative_to(ROOT))]={n:sha(sub/n) for n in files}
    assert seen=={(m,p,f) for m in [False,True] for p in [1,2] for f in 'NSHB'}
    proof=read(ROOT/'build/exit-owner/source-proofs'/args.source_label/'result.json')
    assert proof['passed'] and proof['attached'] and proof['mouse'] and proof['retry'] and len(proof['products'])==34
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_exit_source.py');current(proof['sources'])
    for name,pair in proof['products'].items():assert pair['expected']==pair['actual']==sha(ROOT/'build'/name),name
    baseline=read(ROOT/'docs/validation/parent-exit-mouse.json')
    stock={n:sha(ROOT/'build'/n) for n in baseline['stock_products_unchanged']}
    assert stock==baseline['stock_products_unchanged']
    controls=[]
    for path,expected in [(ROOT/'build/aspect-parent-break-mouse'/args.normal_control/'result.json',{'G','F','full-2-B'}),
                          (ROOT/'build/aspect-parent-exit'/args.exit_control/'result.json',{'Q-1-H'})]:
        control=read(path);assert control['passed'] and not control['same_session_retry'];current(control['source_hashes'])
        assert control['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py')
        assert {c['case'] for c in control['cases']}==expected
        assert all(c['passed'] and all(c['checks'].values()) for c in control['cases'])
        controls.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),cases=sorted(expected)))
    result=dict(passed=True,routes=routes,checks=sum(r['checks'] for r in routes),whole_application_gates_closed=[],
        source_proof=proof,evidence=evidence,controls=controls,stock_products_unchanged=stock,child_sha256=sha(child),checker_sha256=sha(Path(__file__)),
        auditor_dependencies={'standalone/record_parent_exit.py':sha(ROOT/'standalone/record_parent_exit.py')},
        limits=['Controlled first-script INT1B mutation; no physical modem/mouse acceptance',
            'Only the known retained ISR is invoked; no vector/lease repair or retained allocation reclaim',
            'Observer is verified in upper memory to avoid consuming the conventional RAM under test; hardware UMB availability is not established',
            'One exact parent resource snapshot is compared byte-for-byte against live post-EXEC memory; second redundant report copy omitted',
            'Nested DOS child deliberately exits37; WAITFOR is checked through its own native result rather than the previous RUN comparison',
            'One retained failure followed by one successful retry; repeated quarantine exhaustion is not eliminated',
            'Normal publication, remaining native services, stock BBS/hardware acceptance and all full application gates remain open'])
    (ROOT/'docs/validation/parent-retry.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Sixteen same-session retained-child/retry routes and34 source products audited')
if __name__=='__main__':main()
