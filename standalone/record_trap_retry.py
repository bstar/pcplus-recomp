#!/usr/bin/env python3
"""Audit real retained-ASPECT retries under application trap ownership."""
import argparse,json,re,struct
from pathlib import Path
from build_aspect_process import ROOT,sha
from record_parent_exit import mouse_evidence

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyboard-label',required=True);p.add_argument('--mouse-label',required=True)
    p.add_argument('--keyboard-control',required=True);p.add_argument('--mouse-control',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();routes=[];evidence={}
    names=('seen returned status carry psp child_function child_code nested_calls nested_carry '
        'nested_lease resources_equal final_lease vector_before_off vector_before_seg '
        'vector_after_off vector_after_seg retained_owner retained_paras callback_before '
        'callback_after extra_owner extra_paras extra_word jft_equal owners_equal exec_error '
        'largest_free observer_segment nested_status nested_kernel_flags nested_caller_flags').split()
    child=ROOT/'build/aspect-exit-retry/ASPECT.EXE'
    syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(child.parent/'ASPECT.map').read_text(),re.M|re.I)}
    code_seg,code_off=syms['_aspect_exit_foreign']
    for mouse,label in [(False,a.keyboard_label),(True,a.mouse_label)]:
        assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
        base='aspect-parent-exit'+('-mouse' if mouse else '')+'-retry-guarded-banked-traps'
        folder=ROOT/'build'/base/label;report=json.loads((folder/'result.json').read_text())
        parent=ROOT/'build'/('terminal-traps-mouse' if mouse else 'terminal-traps')/'TERMINAL.EXE'
        assert report['passed'] and report['same_session_retry'] and report['experimental_mouse']==mouse
        assert report['parent_sha256']==sha(parent) and report['child_sha256']==sha(child)
        assert report['observer_sha256']==sha(folder/'RENDER.COM')
        assert report['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py')
        for n,h in report['source_hashes'].items():
            assert sha(ROOT/n)==sha(folder/'sources'/n)==h,n
        assert {c['case'] for c in report['cases']}=={f'Q-{port}-{flow}' for port in [1,2] for flow in 'NSHB'}
        for case in report['cases']:
            run=folder/case['case'];assert case==json.loads((run/'result.json').read_text())
            assert case['passed'] and all(case['checks'].values())
            assert sha(run/'TERMINAL.EXE')==sha(parent) and sha(run/'ASPECT.EXE')==sha(child)
            raw=(run/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw)
            assert header[:4]==(0x524e,1,1,1) and header[6]==10
            assert raw.count(b'TRAPOBS1')==1
            traps=struct.unpack_from('<16H',raw,raw.index(b'TRAPOBS1')+8)
            assert list(traps)==case['trap_snapshot']
            assert traps[0]==2 and traps[15]==1 and traps[1:7]==traps[8:14]
            assert traps[7]==traps[14] and traps[7] in [0,1]
            at=len(raw)-26-32*70-case['compared_parent_bytes']
            retained=struct.unpack_from('<15H',raw,at-30)
            assert list(retained)==case['retained_words']
            assert retained[0]==0x31 and retained[10]==0x030a
            assert retained[1]==retained[2]==retained[4] and retained[3]==retained[5]>0
            assert retained[6:8]==(code_off,retained[1]+16+code_seg)
            assert retained[8:10]==(0,1) and retained[12:15]==(retained[1],32,0xa55a)
            start=at-30-(4150 if mouse else 0)-1334
            r=dict(zip(names,struct.unpack_from('<31H',raw,start)))
            assert r==case['retry_probe']
            assert (r['seen'],r['returned'],r['status'],r['carry'])==(1,1,0,0)
            assert r['psp'] not in [0,header[5],retained[1]]
            assert (r['child_function'],r['child_code'])==(0x4c,0)
            assert (r['nested_calls'],r['nested_carry'],r['nested_lease'],r['nested_status'])==(1,0,1,37)
            assert r['resources_equal']==1 and r['final_lease']==0
            assert (r['vector_before_off'],r['vector_before_seg'])==traps[1:3]
            assert (r['vector_after_off'],r['vector_after_seg'])==traps[1:3]
            assert (r['callback_before'],r['callback_after'])==(1,2)
            assert (r['retained_owner'],r['retained_paras'])==(retained[1],retained[3])
            assert (r['extra_owner'],r['extra_paras'],r['extra_word'])==(retained[1],32,0xa55a)
            assert r['jft_equal']==r['owners_equal']==1 and r['observer_segment']>=0xa000
            assert r['nested_caller_flags']&0x200
            start+=62
            assert raw[start:start+20]==raw[start+20:start+40]
            assert raw[start+40:start+456]==raw[start+456:start+872]
            assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
            assert (run/'CHILD.LOG').read_bytes()==b'GT'
            assert (run/'RETRY.OUT').read_bytes()==b'retry-owned'
            assert struct.unpack('<3H',(run/'RETRYWIT.BIN').read_bytes())[0]==0
            assert struct.unpack('<10H',(run/'RETRYDBG.BIN').read_bytes())==(37,0,0,0,0,0,0,0,1,0)
            wire=(run/'serial.bin').read_bytes();screen=(run/'SCREEN.BIN').read_bytes()[::2]
            assert wire.count(b'RETRY-OK\r')==1 and b'Synth42\r' not in wire and b'ready' in wire
            assert b'\x1b[2;1R' in wire[wire.find(b'RETRY-OK\r')+9:]
            assert b'RETRY COMPLETE' in screen and b'FAIL' not in screen and b'ASPECT memory retained.' in screen
            route=dict(mouse=mouse,case=case['case'],checks=len(case['checks']),
                retained_PSP=retained[1],retry_PSP=r['psp'],callback_hits=r['callback_after'],
                caller_INT1B=list(traps[1:3]),retained_ISR=list(retained[6:8]),parent_sha256=sha(parent))
            if mouse:route['mouse_evidence']=mouse_evidence(run,case,parent,True,resource_copies=1)
            routes.append(route)
            evidence[str(run.relative_to(ROOT))]={n:sha(run/n) for n in ['RENDER.BIN','result.json','RETRYWIT.BIN','RETRYDBG.BIN','RETRY.OUT','serial.bin','SCREEN.BIN']}
    assert len(routes)==16
    controls=[]
    for mouse,label,expected in [(False,a.keyboard_control,'Q-1-H'),(True,a.mouse_control,'Q-2-B')]:
        assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
        base='aspect-parent-exit'+('-mouse' if mouse else '')+'-retry-guarded-banked'
        folder=ROOT/'build'/base/label
        report=json.loads((folder/'result.json').read_text())
        assert report['passed'] and len(report['cases'])==1 and report['cases'][0]['case']==expected
        assert report['cases'][0]['trap_snapshot'] is None
        case=report['cases'][0];r=case['retry_probe'];retained=case['retained_words']
        assert all(case['checks'].values())
        assert (r['vector_before_off'],r['vector_before_seg'])==tuple(retained[6:8])
        assert (r['vector_after_off'],r['vector_after_seg'])==tuple(retained[6:8])
        assert (r['callback_before'],r['callback_after'])==(1,2)
        for n,h in report['source_hashes'].items():assert sha(ROOT/n)==h,n
        controls.append(dict(receipt=str((folder/'result.json').relative_to(ROOT)),
            sha256=sha(folder/'result.json'),checks=len(case['checks'])))
    receipt=dict(passed=True,routes=routes,checks=sum(r['checks'] for r in routes),evidence=evidence,
        untrapped_controls=controls,
        auditor_sha256=sha(Path(__file__)),mouse_auditor_sha256=sha(ROOT/'standalone/record_parent_exit.py'),
        scope='Actual DOS31 retention followed by real DOS4C retry and nested PROGRAM, caller trap handoff, exact retained ISR invocation and mouse restoration. No vector repair, unloading, memory-pressure overwrite or physical hardware claim.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('Trap-aware retained retry audit PASS:',len(routes),'routes',receipt['checks'],'checks')

if __name__=='__main__':main()
