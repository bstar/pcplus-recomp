#!/usr/bin/env python3
"""Bind live helper returns to actual script-login and unsaved BBS editor evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from modem import Telnet
from product_inputs import select_product

# Independent raw layout from the captured public DOS structs and native import
# ABI, rather than the helper probe's pass booleans or interpretation routine.
SPANS=[('owner',1734),('baseline',1272),('config',44),('modem',368),('transfer',66),
       ('keymap',948),('xlt',256),('sound',2),('status',2),('xltmode',2),
       ('xlton',2),('mask',2),('profile',2),('irqoff',2),('irqseg',2)]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def word(raw,at=0):return struct.unpack_from('<H',raw,at)[0]
def fields(path):
    raw=path.read_bytes();assert len(raw)==sum(size for _,size in SPANS)
    answer={};offset=0
    for name,size in SPANS:answer[name]=raw[offset:offset+size];offset+=size
    return answer


def verify_case(server,label,mode,delay,terminal,runner,immediate=False):
    assert server in ('synchronet','enigma') and mode in ('accept','reject')
    assert label and all(c.isalnum() or c in '-_' for c in label)
    stage=ROOT/'build/bbs-lab/script-login'/label
    output=ROOT/'build/bbs-lab/results'/server/label
    report=json.loads((stage/'checks.json').read_text())
    prediction=json.loads((stage/'predictions.json').read_text())
    run=json.loads((output/'result.json').read_text())
    audit=json.loads((output/'semantic-audit.json').read_text())
    assert report['predictions_sha256']==sha(stage/'predictions.json')
    assert report['terminal_sha256']==run['binary_sha256']==audit['binary_sha256']==sha(terminal)
    assert report['runner_sha256']==sha(runner)
    assert sha(stage/'TERMINAL.EXE')==sha(terminal) and sha(stage/'ASPECT.EXE')==sha(runner)
    for source,digest in report['sources'].items():assert sha(ROOT/source)==digest,source
    for leaf,digest in prediction['staged'].items():assert sha(stage/leaf)==digest,leaf
    if prediction['compile_in_DOS']:
        compiler,_=select_product(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE','ASPCOMP.EXE')
        assert sha(stage/'ASPCOMP.EXE')==sha(compiler)
    if server=='enigma':
        server_root=ROOT/'build/bbs-lab/enigma/source'
        for source,digest in report['server_sources'].items():assert sha(server_root/source)==digest
        assert report['checks']['stock_server_unchanged']
    assert run['passed'] and all(run['checks'].values())
    assert run['cpu']=='8086' and 'cputype=8086' in (output/'dosbox.conf').read_text()
    assert run['modem_packet_delay_ms']==audit['modem_packet_delay_ms']==delay
    assert run['serial']['com']==2 and run['serial']['baud']==19200 and run['serial']['flow']=='HARD'
    assert run['server_endpoint']==dict(address='127.0.0.1',port=23231 if server=='synchronet' else 23233)
    assert report['checks']['helper_session']
    passed=report['passed'];assert passed is audit['passed']
    assert all(v for k,v in report['checks'].items() if k!='resumed_parent_editor')
    assert report['checks']['resumed_parent_editor'] is passed
    assert all(audit['observed_key_wire'].values())
    assert audit['checks']['draft_aborted' if server=='synchronet' else 'no_post_saved']
    if not immediate:assert passed and all(audit['checks'].values())
    else:
        assert server=='enigma' and delay==0
        assert all(v for k,v in audit['checks'].items() if k not in ('home_moves_before_marker','insert_toggled_overtype'))
    wire,_=Telnet().feed((output/'bbs-sent.bin').read_bytes())
    credentials=b'LABUSER\rLABPASS42\r' if server=='synchronet' else b'loclab\rLoC-Lab-2026!\r'
    assert wire.count(credentials)==1
    assert word((stage/'MODE.BIN').read_bytes())==(0 if mode=='accept' else 1)
    assert (stage/'COUNT.BIN').read_bytes()==struct.pack('<H',3)
    assert word((stage/'ACTIONS.KEY').read_bytes())==2
    snapshots=[fields(stage/f'S{i}.BIN')for i in range(3)]
    before=[(stage/f'B{i}.BIN').read_bytes()for i in range(3)]
    after=[(stage/f'A{i}.BIN').read_bytes()for i in range(3)]
    assert all(len(p)==2094 for p in before+after)
    accepted=mode=='accept'
    assert word(snapshots[0]['owner'],4)==1
    assert before[1]==(after[0] if accepted else before[0])
    assert before[2]==after[1]==before[1]
    assert before[0]!=after[0],'The first helper must actually propose a mutation'
    for index in (1,2):
        s=snapshots[index];assert word(s['owner'])==0 and s['owner'][904:]==before[index][:830]
        assert word(s['owner'],4)==1+index-(not accepted)
        assert word(s['status'])==(107 if index==1 and not accepted else 0)
        if index==1 and not accepted:
            assert all(s[name]==snapshots[0][name] for name,_ in SPANS if name not in ('owner','status'))
        else:
            assert word(s['baseline'],4)==3 and s['baseline'][8:]==before[index][830:]
        if accepted:
            assert word(s['config'],18)==30 and word(s['config'],38)==31 and word(s['config'],42)==32
            assert word(s['sound'])==0 and word(s['transfer'])==1 and word(s['modem'],366)==123
        else:assert s['config']==snapshots[0]['config']
    for i,s in enumerate(snapshots):
        h=struct.unpack('<13H',(stage/f'H{i}.BIN').read_bytes())
        assert h[4]==6 and h[5]==3 and h[7]==0 and not h[6]&2 and h[8]&8
        assert h[11:13]==(word(s['irqoff']),word(s['irqseg']))
    return dict(server=server,label=label,mode=mode,packet_delay_ms=delay,editor_passed=passed,
        source_compilation=prediction['compile_in_DOS'],helper_calls=3,
        server_revision=report.get('server_commit'),server_sources=report.get('server_sources',{}),
        first_return_status=word(snapshots[1]['status']),second_return_status=word(snapshots[2]['status']),
        register_epochs=[word(s['owner'],4)for s in snapshots],no_post_saved=True,
        checks=report['checks'],editor_checks=audit['checks'],
        sources=report['sources'],artifacts={str(p.relative_to(ROOT)):sha(p)
            for folder in (stage,output)for p in folder.iterdir()if p.is_file()})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True);p.add_argument('--runner',type=Path,required=True)
    p.add_argument('--case',action='append',required=True,help='server:label:accept|reject:delay_ms')
    p.add_argument('--immediate-label',action='append',default=[])
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    terminal,_=select_product(args.terminal,'TERMINAL.EXE');runner,_=select_product(args.runner,'ASPECT.EXE')
    assert json.loads((terminal.parent/'manifest.json').read_text())['experimental_hook_apply']
    cases=[verify_case(server,label,mode,int(delay),terminal,runner)
        for server,label,mode,delay in (spec.split(':')for spec in args.case)]
    assert {(c['server'],c['mode'])for c in cases}=={(server,mode)for server in ('synchronet','enigma')for mode in ('accept','reject')}
    for label in args.immediate_label:cases.append(verify_case('enigma',label,'accept',0,terminal,runner,True))
    assert len({c['label']for c in cases})==len(cases)
    result=dict(passed=True,terminal_sha256=sha(terminal),runner_sha256=sha(runner),cases=cases,
        recorder_sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
            'src/config/terminal_import.h':sha(ROOT/'src/config/terminal_import.h')},
        scope='Actual directory ASPECT login followed by three KEY kind2 helpers and stock unsaved BBS editor. '
        'First helper acceptance/rejection, second acceptance, raw register/baseline/configuration and quiet UART '
        'snapshots are independently checked. Third helper exits23; following editor exercises recovery, but no '
        'post-third accepted-bank snapshot is claimed. ENiGMA immediate observations remain separate from30ms '
        'buffered acceptance. No physical modem, full application, transfer or general TCP-partition claim.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS live helper receipt:',len(cases),'cases; editor outcomes',[c['editor_passed']for c in cases])
if __name__=='__main__':main()
