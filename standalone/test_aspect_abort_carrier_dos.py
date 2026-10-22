#!/usr/bin/env python3
"""Actual DOS virtual-modem hangup during native script confirmation.

The owned TCP peer closes its BBS socket. DOSBox-X's modem then changes DCD and
emits NO CARRIER; the observer only reads product/video state. No product flag,
MSR result, script FILE position or handler output is injected by the observer.
"""
import argparse,inspect,json,re,shutil,struct,subprocess,sys,types
from pathlib import Path
import test_connection_dos as connection
import test_aspect_renderer_dos as renderer
import test_aspect_script_window_dos as window
from test_aspect_abort_confirm_dos import confirmation_observer
from directory_fixtures import directory,prm
ROOT=renderer.ROOT;ESC=b'\x1b';QUERY=ESC+b'[6n'
sha=renderer.sha


def observer(out,product_root):
    renderer.OUT=out
    parent=window.symbols(product_root/'build/terminal/terminal.map')
    child=window.symbols(product_root/'build/aspect-runner/ASPECT.map')
    builder=window.make_observer(renderer.observer,parent,child)
    builder=confirmation_observer(builder,product_root)
    result=builder(renderer.map_offsets(product_root/'build/terminal/terminal.map'))
    path=out/'observer.asm';text=path.read_text()
    fields=['carrier_armed_seen','carrier_cleared_seen','carrier_pending_seen','carrier_error_seen','carrier_clear_ticks','carrier_depth_seen','carrier_last_key_seen','carrier_tx_paused_seen']
    text=text.replace('sample_end:\nowner_table:',''.join(n+': dw 0\n' for n in fields)+'sample_end:\nowner_table:')
    timer='''timer:
 save
 cld
 cmp word [cs:exec_seen],1
 jne .carrier_done
 cmp word [cs:exec_done],0
 jne .carrier_done
 mov ax,[cs:parent_psp]
 or ax,ax
 jz .carrier_done
 add ax,CONFIRM_CS+0x10
 mov es,ax
 cmp word [es:CONFIRM_ACTIVE],1
 jne .carrier_done
 mov ax,[es:CHILD_DS]
 or ax,ax
 jz .carrier_done
 mov es,ax
 cmp word [es:ARMED],0
 je .carrier_cleared
 mov word [cs:carrier_armed_seen],1
 jmp .carrier_pending
.carrier_cleared:
 mov word [cs:carrier_cleared_seen],1
 inc word [cs:carrier_clear_ticks]
.carrier_pending:
 cmp word [es:WAIT_GATE],0
 je .carrier_depth
 mov word [cs:carrier_pending_seen],1
.carrier_depth:
 mov ax,[es:DEPTH]
 cmp ax,[cs:carrier_depth_seen]
 jbe .carrier_error
 mov [cs:carrier_depth_seen],ax
.carrier_error:
 mov ax,[es:ERROR]
 or ax,ax
 jz .carrier_last_key
 mov [cs:carrier_error_seen],ax
.carrier_last_key:
 cmp word [es:TX_PAUSED],0
 je .carrier_key
 mov word [cs:carrier_tx_paused_seen],1
.carrier_key:
 cmp word [es:LAST_KEY],27
 jne .carrier_done
 mov word [cs:carrier_last_key_seen],1
.carrier_done:
'''
    for token,value in [('CONFIRM_CS',parent['terminal_script_confirm_active'][0]),('CONFIRM_ACTIVE',parent['terminal_script_confirm_active'][1]),('CHILD_DS',parent['render_child_ds'][1]),('ARMED',child['_runtime_when_disconnect_armed'][1]),('WAIT_GATE',child['_runtime_wait_gate'][1]),('DEPTH',child['_runtime_depth'][1]),('ERROR',child['_runtime_error'][1]),('LAST_KEY',child['_runtime_when_last_key'][1]),('TX_PAUSED',child['uart_tx_paused'][1])]:
        timer=timer.replace(token,str(value))
    assert text.count('timer:\n save\n cld\n')==1
    text=text.replace('timer:\n save\n cld\n',timer)
    path.write_text(text);subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'RENDER.COM')],check=True)
    return (out/'RENDER.COM').read_bytes(),fields


def adapter(out,events,blocked=False):
    text=inspect.getsource(connection.run)
    text=text.replace("out=ROOT/'build/connection-dos'/name",'out=CASE_OUT/name')
    start=text.index(' def peer():');end=text.index(' thread=threading.Thread',start)
    peer=''' def peer():
  nonlocal attempts
  def event(kind,data=b''):
   events.append(dict(kind=kind,time=time.monotonic(),hex=data.hex()))
  try:
   conn,_=server.accept();attempts+=1;event('connected')
   with conn:
    conn.settimeout(.05);ready_at=None;query_sent=False;xoff_sent=False
    conn.sendall(banner);event('send',banner)
    while not stop.is_set():
     now=time.monotonic()
     if ready_at is not None and not query_sent and now-ready_at>=2.5:
      conn.sendall(b'\\x1b[6n');event('send',b'\\x1b[6n');query_sent=True
     if ready_at is not None and BLOCKED and not xoff_sent and now-ready_at>=3.0:
      conn.sendall(b'\\x13');event('send',b'\\x13');xoff_sent=True
     if ready_at is not None and now-ready_at>=3.5:
      conn.shutdown(socket.SHUT_RDWR);event('hangup');checks['peer_closed_after_script_ready']=True;return
     try:block=conn.recv(4096)
     except socket.timeout:continue
     if not block:break
     wire.extend(block);event('receive',block)
     if ready_at is None and b'KEYREADY' in wire:ready_at=time.monotonic();event('script-ready')
  except OSError as error:errors.append(str(error))
'''
    text=text[:start]+peer+text[end:]
    bind=" server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(5)"
    assert text.count(bind)==1
    text=text.replace(bind,bind+'''
 target=('127.0.0.1:'+str(server.getsockname()[1])).encode()
 contact=bytearray(directory);at=250+(directory_entry-1)*114
 contact[at+25:at+46]=target.ljust(21,b'\\0');directory=bytes(contact)
 (out/'TEST.DIR').write_bytes(directory);(out/'DIAL.IN').write_bytes(directory)
''')
    serial="f'nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'"
    assert text.count(serial)==1;text=text.replace(serial,"'modem listenport:0'")
    text=text.replace("commands[:2]==['ATZ',('ATD'+target.decode('ascii'))]","attempts==1")
    text=text.replace("checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'","checks['screen_snapshot_complete']=len(screen)==4000")
    text=text.replace('timeout=20)','timeout=30)')
    text=text.replace('cputype=386','cputype=8086')
    module=types.ModuleType('virtual_modem_carrier');module.__dict__.update(connection.__dict__)
    module.__dict__.update(CASE_OUT=out,events=events,BLOCKED=blocked)
    exec(compile(text,__file__,'exec'),module.__dict__)
    return module


def source(kind):
    registration='when disconnect '+('transmit "^MAT^M"' if kind in ('TX','XOFF') else 'call worker')+'\n'
    body=('proc main\nwaitfor "LOGIN:" 5\nset duplex full\n'+registration+'transmit "KEYREADY"\n'
          'waitfor "NEVER" 30\nfopen 5 "MAIN.OK" "wb"\nfputs 5 "DECLINED"\nfclose 5\nendproc\n')
    if kind=='CALL':body+=('proc worker\ninteger value\nvalue=37\nfopen 5 "DCD.OK" "wb"\n'
                           'if value==37\nfputs 5 "FRAME37"\nelse\nfputs 5 "BADFRAME"\nendif\nfclose 5\nendproc\n')
    return body


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
    parser.add_argument('--case',action='append',choices=['TX-No','CALL-No','CALL-Yes','XOFF-error'])
    parser.add_argument('--expect-gap',action='store_true')
    parser.add_argument('--expect-parent-gap',action='store_true')
    parser.add_argument('--product-root',type=Path,default=ROOT);args=parser.parse_args()
    product_root=args.product_root.resolve();assert product_root==ROOT or product_root.is_relative_to(ROOT/'build')
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/aspect-abort-carrier-dos'/args.label;out.mkdir(parents=True,exist_ok=False)
    identities={};input_paths={}
    for d,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        product=product_root/'build'/d/leaf;m=json.loads((product.parent/'manifest.json').read_text())
        assert sha(product)==m['binary_sha256']
        for name,digest in m['sources'].items():
            assert sha(product_root/name)==digest,name;identities[name]=digest;input_paths[name]=product_root/name
        key=str(product.relative_to(product_root));identities[key]=sha(product);input_paths[key]=product
    for path in [Path(__file__),Path(connection.__file__),Path(window.__file__),ROOT/'standalone/test_aspect_abort_confirm_dos.py']:
        key=str(path.relative_to(ROOT));identities[key]=sha(path);input_paths[key]=path
    for name,digest in identities.items():
        target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(input_paths[name],target)
    compiled,fields=observer(out,product_root);results=[]
    for kind,answer in [('TX','No'),('CALL','No'),('CALL','Yes'),('XOFF','error')]:
        name=kind+'-'+answer
        if args.case and name not in args.case:continue
        events=[];harness=adapter(out,events,kind=='XOFF');folder=out/name;folder.mkdir()
        for d,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:shutil.copy2(product_root/'build'/d/leaf,folder/leaf)
        harness.BINARY=folder/'TERMINAL.EXE'
        payload=bytearray(directory(profile=4));payload[302:311]=b'LOGIN\0\0\0\0'
        script=source(kind);files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':renderer.compile_source(script),'RENDER.COM':compiled}
        keys='p2200 escape p5000 '+('y' if answer=='Yes' else 'n')+' p1900 a-z p800 escape p400 a-x'
        if kind=='XOFF':keys='p2200 escape p7500 a-z p800 escape p400 a-x'
        banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+ESC+b'[0cLOGIN:'
        # Carrier is already down when the parent exits. Use the configurable
        # command-mode hangup rather than sending an online escape sequence.
        settings=bytearray(prm(soft=int(kind=='XOFF'),hard=int(kind!='XOFF')));settings[0x79:0x79+25]=b'ATH^M'.ljust(25,b'\0')
        try:
            report=harness.run(name,'success',keys,directory=bytes(payload),prm=bytes(settings),profile=4,files=files,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',working_drive='d',observer='RENDER',banner=banner)
        finally:
            (folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw)
        extra=struct.unpack('<17H',raw[-34:]);window_state=extra[:5];confirmation=extra[5:9];carrier=dict(zip(fields,extra[9:]))
        wire=(folder/'serial.bin').read_bytes()
        expected=(b'\x13\x11' if kind=='XOFF' else b'')+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+ESC+b'[1;22R'
        modem_log=(folder/'dosbox.log').read_text();not_parent_gap=not args.expect_parent_gap
        checks=dict(parent_status_OFF_LINE=(b'OFF-LINE' in (folder/'SCREEN.BIN').read_bytes()[3840:4000:2])==not_parent_gap,modem_carrier_loss=modem_log.count('Modem response: NO CARRIER')==1,
                    exit_hangup_matches_carrier_policy=(('Command sent to modem: ->ATH<-' in modem_log)==(args.expect_parent_gap and kind!='XOFF')) and 'Modem response: ERROR' not in modem_log,
                    native_TX_action_in_modem=(('Command sent to modem: ->AT<-' in modem_log)==(kind=='TX')),
                    base_DOS_hardware_directory_and_peer=report['passed'],exact_whole_BBS_wire=wire==expected,
                    peer_stream_matches=wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive'),
                    actual_child_exit=header[:4]==(0x524e,1,1,1) and header[6]==(14 if kind=='XOFF' else 13 if answer=='Yes' else 0),
                    JFT_restored=raw[14:34]==raw[34:54],owners_restored=raw[54:470]==raw[470:886],
                    prompt_owned_and_visible=confirmation[2]==1 and confirmation[3]>18,
                    parser_advances_in_prompt=confirmation[1]==1,parent_menu_after_child=window_state[4]==1,
                    carrier_initially_armed=carrier['carrier_armed_seen']==1,
                    modal_error_matches_path=carrier['carrier_error_seen'] in ((0,14) if kind=='XOFF' else (0,)),
                    native_escape_retained=carrier['carrier_last_key_seen']==1,
                    disarm_under_prompt=carrier['carrier_cleared_seen']==int(not args.expect_gap and kind!='XOFF'),
                    staged_CALL_under_prompt=carrier['carrier_pending_seen']==int(kind=='CALL' and not args.expect_gap),
                    software_pause_observed=carrier['carrier_tx_paused_seen']==int(kind=='XOFF'),
                    main_tail=(not (folder/'MAIN.OK').exists() if answer in ('Yes','error') else (folder/'MAIN.OK').read_bytes()==b'DECLINED'),
                    framed_CALL=(not (folder/'DCD.OK').exists() if kind!='CALL' or answer=='Yes' else (folder/'DCD.OK').read_bytes()==b'FRAME37'))
        result=dict(case=name,passed=all(checks.values()),checks=checks,
                    known_unaccepted_status=dict(stale_ON_LINE_label=b'ON-LINE' in (folder/'SCREEN.BIN').read_bytes()[::2]),carrier=carrier,confirmation=confirmation,window=window_state,
                    wire_sha256=sha(folder/'serial.bin'),captures={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()})
        (folder/'carrier-checks.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(json.dumps(dict(case=name,passed=result['passed'],checks=checks,carrier=carrier)),flush=True)
    report=dict(passed=all(r['passed'] for r in results),gap_reproduced=args.expect_gap,expected_parent_gap=args.expect_parent_gap,compatibility_accepted=not (args.expect_gap or args.expect_parent_gap),
                cases=results,inputs=identities,product_source_root=str(product_root),parent_sha256=sha(product_root/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(product_root/'build/aspect-runner/ASPECT.EXE'),
                observer_fields=fields,observer_sha256=sha(out/'RENDER.COM'),checker_sha256=sha(Path(__file__)),scope=__doc__+' Emulated modem/DCD; no physical modem or14.4 negotiation claim.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']


if __name__=='__main__':main()
