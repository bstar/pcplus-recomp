#!/usr/bin/env python3
"""Actual product WHEN/renderer tests. No query parser or reply substitute.

Use --prepare to freeze authored cases without executing or rebuilding products.
Execution requires explicit frozen terminal and runner hashes and a new label.
"""
import argparse
import inspect
import struct
import subprocess
import json
import re
import sys
import types
from pathlib import Path
import test_aspect_renderer_dos as renderer

ROOT = renderer.ROOT
OUT = ROOT / 'build/aspect-when-renderer-dos'
ESC = b'\x1b'


def definitions():
    header = ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+renderer.QUERY+renderer.DA
    def program(registration, workers, seconds=5):
        return ('proc main\n'+registration+'transmit "READY^M"\n'
                +f'waitfor "END" {seconds}\n'
                +'transmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'+workers)
    worker = 'proc worker\ntransmit "EVENT^M"\nendproc\n'
    cases = [
        dict(name='deferred-C7', source=program('when 0 "TRIG" call worker\n',worker), trigger=b'TRIG', events=[b'EVENT\r']),
        dict(name='deferred-C8-frame',source=program('when 0 "TRIG" call worker\n','proc worker\ninteger local_value\nlocal_value = 37\nif local_value == 37\ntransmit "FRAME^M"\nelse\ntransmit "BADFRAME^M"\nendif\nendproc\n'),trigger=b'TRIG',events=[b'FRAME\r'],forbidden=[b'BADFRAME\r'],framed=True),
        dict(name='two-pending-LIFO',source=program('when 0 "ONE" call first\nwhen 1 "TWO" call second\n','proc first\ntransmit "FIRST^M"\nendproc\nproc second\ntransmit "SECOND^M"\nendproc\n'),trigger=b'ONETWO',events=[b'SECOND\r',b'FIRST\r']),
        dict(name='XLT-monitor-mapped-lead-once',source=program('when 0 "!" call worker\n',worker),trigger=ESC,events=[b'EVENT\r'],xlt=True),
        dict(name='CSI-continuations-bypass-WHEN',source=program('when 0 "6n" call worker\n',worker),trigger=renderer.QUERY,events=[],forbidden=[b'EVENT\r']),
        dict(name='timeout-services-pending-CALL',source=program('when 0 "TRIG" call worker\n',worker,1),trigger=b'TRIG',events=[b'EVENT\r'],pending_timeout=True),
        dict(name='Escape-discards-pending-CALL',source=program('when 0 "TRIG" call worker\n',worker),trigger=b'TRIG',events=[],forbidden=[b'EVENT\r'],cancel=True,success=False),
        dict(name='typed-handler-error-parent-resumes',source=program('when 0 "TRIG" call worker\n','proc worker\ninteger value\ntransmit "EVENT^M"\nvalue = 1 / 0\nendproc\n'),trigger=b'TRIG',events=[b'EVENT\r'],success=False),
    ]
    for case in cases:
        case.setdefault('success', True)
        case.update(banner=b'',screen=[(0,0,'FIRST BYTE SAFE')],post=renderer.QUERY,
                    post_reply=ESC+(b'[1;16R' if case.get('pending_timeout') else b'[1;19R'))
        # Header queries prove real parent parsing before the trigger. Reset the
        # cursor before END so post-return CPR has an independently fixed value.
        stream=header+case['trigger']+ESC+b'[1;16H'
        if case.get('xlt'):
            stream=header.replace(ESC,b'z')+case['trigger']+b'z[1;16H'
            case['post']=renderer.QUERY.replace(ESC,b'z')
        case['ready_stream']=stream
        case['send_end']=not(case.get('pending_timeout') or case.get('cancel'))
        case['end_delay_seconds']=0.65
    return cases


def encoded_cases(cases):
    def encode(value):
        if isinstance(value,bytes): return {'hex':value.hex()}
        if isinstance(value,list): return [encode(v) for v in value]
        if isinstance(value,tuple): return [encode(v) for v in value]
        if isinstance(value,dict): return {k:encode(v) for k,v in value.items()}
        return value
    return encode(cases)


def adapter():
    """Use the real connection harness with a READY-gated synthetic peer only."""
    path=ROOT/'standalone/test_connection_dos.py'
    source=path.read_text()
    changes={
      "out=ROOT/'build/connection-dos'/name":"out=WHEN_OUT/name",
      "checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'":"checks['actual_screen_snapshot']=len(screen)==4000",
      'checks={};attempts=0':"checks={'WHEN_body_not_before_END':True};attempts=0",
      'while not stop.is_set():':'''while not stop.is_set():
     case=WHEN_CASES[name]
     if online and checks.get('WHEN_READY_observed') and case['send_end'] and not checks.get('WHEN_END_sent') and time.monotonic()-when_ready_at>=case['end_delay_seconds']:
      conn.sendall(b'END');checks['WHEN_END_sent']=True''',
      'if online:\n       line.append(byte)':'''if online:
       line.append(byte)
       if not checks.get('WHEN_READY_observed') and line.endswith(b'READY\\r'):
        checks['WHEN_READY_observed']=True;when_ready_at=time.monotonic();conn.sendall(WHEN_CASES[name]['ready_stream']);checks['WHEN_trigger_after_READY']=True
       if any(line.endswith(event) for event in WHEN_CASES[name]['events']) and WHEN_CASES[name]['send_end'] and not checks.get('WHEN_END_sent'):
        checks['WHEN_body_not_before_END']=False
       if RENDER_POST and not checks.get('renderer_post_sent') and RENDER_TRIGGER in line:
        conn.sendall(RENDER_POST);checks['renderer_post_sent']=True''',
    }
    for old,new in changes.items():
        assert source.count(old)==1,old
        source=source.replace(old,new)
    module=types.ModuleType('when_renderer_connection_adapter');module.__file__=str(path)
    module.WHEN_OUT=OUT;module.WHEN_CASES={c['name']:c for c in definitions()}
    module.RENDER_POST=b'';module.RENDER_TRIGGER=b'Synth42\r'
    exec(compile(source,str(path),'exec'),module.__dict__)
    return module


def run_product():
    # Reuse the unchanged actual observer/main assertions. This source adapter
    # changes only fixture selection, peer and output path, never product code.
    source=inspect.getsource(renderer.main)
    # Event lists contain bytes; preserve all predictions with recursive encoder.
    old="expectations=[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.items()} for c in cases]"
    assert source.count(old)==1
    source=source.replace(old,'expectations=encoded_cases(cases)')
    scope=dict(renderer.__dict__)
    scope.update(__file__=__file__,OUT=OUT,definitions=definitions,adapter=adapter,encoded_cases=encoded_cases)
    # adapter() uses this module's OUT; renderer main derives its own labelled OUT.
    real_adapter=adapter
    def labelled_adapter():
        global OUT
        OUT=scope['OUT']
        return real_adapter()
    scope['adapter']=labelled_adapter
    def labelled_observer(offsets):
        previous=renderer.OUT
        renderer.OUT=scope['OUT']
        try:
            _,modes,pairs,snapshots=renderer.observer(offsets)
            path=renderer.OUT/'observer.asm';asm=path.read_text()
            child_map=(ROOT/'build/aspect-runner/ASPECT.map').read_text()
            group=int(re.search(r'DGROUP\s+([0-9a-fA-F]{4}):0000',child_map)[1],16)
            def child_word(name):
                match=re.search(r'^\s*([0-9a-fA-F]{4}):([0-9a-fA-F]{4,8})[+*]?\s+'+re.escape(name)+r'$',child_map,re.M)
                assert match,name
                return int(match[1],16)*16+int(match[2],16)-group*16
            psp=child_word('__psp');gate=child_word('_runtime_wait_gate');depth=child_word('_runtime_depth')
            assert asm.count('sample_end:')==1
            asm=asm.replace('sample_end:','when_pending_ticks: dw 0\nwhen_max_gate: dw 0\nwhen_max_depth: dw 0\nsample_end:')
            hook=f"""timer:
 save
 cld
 cmp word [cs:exec_seen],1
 jne .when_done
 cmp word [cs:exec_done],0
 jne .when_done
 mov ax,ss
 mov es,ax
 cmp ax,{group+16}
 jb .when_done
 sub ax,{group+16}
 cmp ax,[es:{psp}]
 jne .when_done
 push es
 mov es,ax
 cmp word [es:0],0x20cd
 pop es
 jne .when_done
 mov ax,[es:{gate}]
 cmp ax,1
 jb .when_done
 cmp word [es:{depth}],0
 je .when_done
 inc word [cs:when_pending_ticks]
 cmp ax,[cs:when_max_gate]
 jbe .when_depth
 mov [cs:when_max_gate],ax
.when_depth:
 mov ax,[es:{depth}]
 cmp ax,[cs:when_max_depth]
 jbe .when_done
 mov [cs:when_max_depth],ax
.when_done:
"""
            assert asm.count('timer:\n save\n cld\n')==1
            asm=asm.replace('timer:\n save\n cld\n',hook)
            path.write_text(asm)
            subprocess.run(['nasm','-fbin',str(path),'-o',str(renderer.OUT/'RENDER.COM')],check=True)
            return (renderer.OUT/'RENDER.COM').read_bytes(),modes,pairs,snapshots
        finally:renderer.OUT=previous
    scope['observer']=labelled_observer
    exec(compile(source,__file__,'exec'),scope)
    status=scope['main']()
    output=scope['OUT'];report=json.loads((output/'checks.json').read_text())
    cases={case['name']:case for case in definitions()}
    for result in report['cases']:
        case=cases[result['case']];folder=output/result['case'];wire=(folder/'serial.bin').read_bytes()
        checks=result['checks']
        raw=(folder/'RENDER.BIN').read_bytes()
        pending_ticks,max_gate,max_depth=struct.unpack_from('<3H',raw,len(raw)-6)
        result['passive_pending_when']={'timer_samples':pending_ticks,'maximum_native_gate':max_gate,'maximum_native_depth':max_depth,'normal_open_gate':1}
        if case['events'] or case.get('cancel'):
            checks['actual_native_pending_CALL_observed']=pending_ticks>0 and max_gate>=1 and max_depth>=1
        if case['name']=='two-pending-LIFO':checks['two_native_pending_CALLs_observed']=max_gate>=2 and max_depth>=2
        if case['name']=='CSI-continuations-bypass-WHEN':checks['no_native_CALL_from_continuation']=pending_ticks==0 and max_depth==0
        checks['READY_once']=wire.count(b'READY\r')==1
        checks['trigger_during_wait']=bool(checks.get('WHEN_trigger_after_READY'))
        cursor=wire.find(b'READY\r')+len(b'READY\r')
        for index,event in enumerate(case['events']):
            found=wire.find(event,cursor)
            checks['handler_event_'+str(index)]=found>=cursor and wire.count(event)==1
            cursor=found+len(event)
        for index,event in enumerate(case.get('forbidden',[])):
            checks['no_forbidden_handler_'+str(index)]=event not in wire
        checks['handler_before_main_resume']=not case['success'] or cursor<=wire.find(b'Synth42\r')
        if case['send_end']:checks['END_sent_after_trigger']=bool(checks.get('WHEN_END_sent'))
        if case.get('framed'):checks['compiled_C8_frame']=b'\x07\xc8' in (folder/'LOGIN.ASX').read_bytes()
        result['passed']=all(checks.values());(folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    report.update(passed=all(c['passed'] for c in report['cases']),
                  reused_renderer_checker_sha256=renderer.sha(Path(renderer.__file__)),
                  scope='Actual product parent renderer and native WHEN runtime, READY-gated owned peer and passive observer. No parser/query substitute. MCB/IRQ/stack details delegated to independent proofs; no physical DCD/CTS or complete application claim.')
    (output/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('WHEN renderer:',len(report['cases']),'cases',sum(len(c['checks']) for c in report['cases']),'checks',report['passed'])
    return 0 if report['passed'] else 1


if __name__=='__main__':
    if '--prepare' in sys.argv:
        parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--label',required=True);args=parser.parse_args()
        assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
        folder=OUT/args.label;folder.mkdir(parents=True,exist_ok=False)
        cases=definitions()
        for case in cases:renderer.compile_source(case['source'])
        (folder/'predictions.json').write_text(json.dumps(encoded_cases(cases),indent=2)+'\n')
        print('Prepared',len(cases),'authored cases; no product execution')
    else:
        raise SystemExit(run_product())
