#!/usr/bin/env python3
"""Actual virtual-modem carrier loss and service errors inside sounding ALARM."""
import argparse
import inspect
import json
import re
import shutil
import struct
from pathlib import Path
import test_aspect_abort_carrier_dos as carrier
import test_aspect_renderer_dos as renderer
import test_aspect_script_window_dos as window
from alarm_speaker_observer import instrument
from directory_fixtures import directory, prm
ROOT = renderer.ROOT
sha = renderer.sha
PARENT_FIELDS = ['terminal_transfer_pending','terminal_transfer_active','terminal_program_pending',
                 'terminal_program_active','terminal_macro_active','terminal_monitor_active',
                 'terminal_controller_active','terminal_ansi_wait_active','terminal_snapshot_active',
                 'uart_break_hold','text_cga_status_port','text_video_segment',
                 'screen_attribute_row_bytes','screen_viewport_enabled','screen_video_row_bytes',
                 'terminal_menu_pending','_command_menu_active']


def observer(out, parent, child):
    renderer.OUT = out
    text = inspect.getsource(renderer.observer)
    old = ' cmp word [PROGRAM_KIND],4\n jne .chain\n'
    assert text.count(old) == 1
    text = text.replace(old, '')
    fields = ['armed_seen','disarmed_seen','disarm_during_alarm','pending_seen','tx_pause_seen']
    old = 'sample_end:\nowner_table:'
    assert text.count(old) == 1
    text = text.replace(old, 'armed_at_exit: dw 0xffff\npost_menu_seen: dw 0\npost_menu_row: times 2000 db 0\npost_parent: times '+str(len(PARENT_FIELDS))+' dw 0xffff\nobserver_segment: dw 0\n' + ''.join(n + ': dw 0\n' for n in fields) + old)
    old = ' mov dx,handler\n'
    assert text.count(old) == 1
    text = text.replace(old, ' mov ax,cs\n mov [observer_segment],ax\n' + old)
    child_symbols = window.symbols(child.with_name('ASPECT.map'))
    parent_symbols = window.symbols(parent.with_name('terminal.map'))
    timer = '''timer:
 save
 cld
 cmp word [cs:exec_seen],1
 jne .alarm_carrier_done
 cmp word [cs:exec_done],0
 jne .alarm_carrier_done
 mov ax,[cs:parent_psp]
 or ax,ax
 jz .alarm_carrier_done
 add ax,PARENT_RENDER_CS+0x10
 mov es,ax
 mov ax,[es:CHILD_DS]
 or ax,ax
 jz .alarm_carrier_done
 mov es,ax
 cmp word [es:ARMED],0
 je .alarm_disarmed
 mov word [cs:armed_seen],1
 jmp .alarm_pending
.alarm_disarmed:
 cmp word [cs:armed_seen],1
 jne .alarm_pending
 mov word [cs:disarmed_seen],1
 cmp word [es:DURATION],6
 jne .alarm_pending
 mov word [cs:disarm_during_alarm],1
.alarm_pending:
 cmp word [es:DURATION],6
 jne .alarm_tx
 cmp word [cs:disarmed_seen],1
 jne .alarm_tx
 cmp word [es:WAIT_GATE],0
 je .alarm_tx
 mov word [cs:pending_seen],1
.alarm_tx:
 cmp word [es:TX_PAUSED],0
 je .alarm_carrier_done
 mov word [cs:tx_pause_seen],1
.alarm_carrier_done:
'''
    values = {'PARENT_RENDER_CS':parent_symbols['render_child_ds'][0],
              'CHILD_DS':parent_symbols['render_child_ds'][1],
              'ARMED':child_symbols['_runtime_when_disconnect_armed'][1],
              'DURATION':child_symbols['alarm_duration'][1],
              'WAIT_GATE':child_symbols['_runtime_wait_gate'][1],
              'TX_PAUSED':child_symbols['uart_tx_paused'][1]}
    for token, value in values.items():
        timer = timer.replace(token, str(value))
    old = ' cmp word [cs:exec_done],0\n jne .alarm_carrier_done\n'
    assert timer.count(old) == 1
    parent_sample = ' cmp word [cs:exec_done],0\n je .alarm_child_running\n mov ax,[cs:parent_ds]\n mov es,ax\n'
    for i,name in enumerate(PARENT_FIELDS):
        parent_sample += ' mov ax,[es:'+str(parent_symbols[name][1])+']\n mov [cs:post_parent+'+str(i*2)+'],ax\n'
    parent_sample += ''' cmp word [es:MENU_ACTIVE],0
 je .alarm_post_sampled
 mov word [cs:post_menu_seen],1
 mov ax,0xb800
 mov es,ax
 xor si,si
 mov di,post_menu_row
 mov cx,2000
.alarm_menu_row:
 mov al,[es:si]
 mov [cs:di],al
 add si,2
 inc di
 loop .alarm_menu_row
.alarm_post_sampled:
'''.replace('MENU_ACTIVE',str(parent_symbols['_command_menu_active'][1]))
    parent_sample += ' jmp .alarm_carrier_done\n.alarm_child_running:\n'
    timer = timer.replace(old,parent_sample)
    old = 'timer:\n save\n cld\n'
    assert text.count(old) == 1
    text = text.replace(old, timer)
    text = instrument(text, child_symbols)
    old = ' push cs\n pop ds\n inc word [child_exits]'
    assert text.count(old) == 1
    text = text.replace(old,' mov ax,[ss:'+str(child_symbols['_runtime_when_disconnect_armed'][1])+']\n mov [cs:armed_at_exit],ax\n'+old)
    exec(compile(text, __file__, 'exec'), renderer.__dict__)
    compiled = window.make_observer(renderer.observer, parent_symbols, child_symbols, render_progress=True)
    result = compiled(renderer.map_offsets(parent.with_name('terminal.map')))
    return result[0], fields


def source(kind):
    registration = '' if kind == 'NONE' else 'when disconnect ' + ('call worker' if kind == 'CALL' else 'transmit "^MAT^M"') + '\n'
    text = ('proc main\nwaitfor "LOGIN:" 5\nset duplex full\n' + registration +
            'fopen 0 "TRACE.LOG" "wb"\nfputs 0 "BEGIN|"\nfclose 0\n'
            'transmit "KEYREADY"\nwaitfor "HOLD" 10\nalarm 6\n'
            'fopen 0 "TRACE.LOG" "ab"\nfputs 0 "MAIN|"\nfclose 0\nendproc\n')
    if kind == 'CALL':
        text += ('proc worker\ninteger value\nvalue=37\nfopen 1 "TRACE.LOG" "ab"\n'
                 'if value==37\nfputs 1 "CALL37|"\nelse\nfputs 1 "BADFRAME|"\nendif\nfclose 1\nendproc\n')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent','child','output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--case', action='append', choices=('NONE','CALL','TX','XOFF'))
    parser.add_argument('--profile',type=int,choices=(4,6),default=4,help='4=VT220,6=ANSI')
    parser.add_argument('--reuse-driver',action='store_true',help='Only the explicitly marked same-process diagnostic, XOFF case')
    args = parser.parse_args()
    if args.reuse_driver:assert args.case==['XOFF']
    parent, child, out = (getattr(args,n).resolve() for n in ('parent','child','output'))
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    sources = {}
    for product in (parent, child):
        manifest = json.loads(product.with_name('manifest.json').read_text())
        assert sha(product) == manifest['binary_sha256']
        if product==child and args.reuse_driver:
            assert manifest.get('diagnostic_build') and manifest.get('diagnostic_alarm_reuse') and manifest['main_source']=='standalone/alarm_reuse_driver.c'
        else:assert not manifest.get('diagnostic_build')
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest, name
            sources[name] = digest
    out.mkdir()
    compiled, fields = observer(out, parent, child)
    # Reuse the actual DOSBox modem/DCD peer. Add HOLD before its query/drop,
    # so the initial setup key cannot be mistaken for an alert completion key.
    text = inspect.getsource(carrier.adapter)
    # The older ordinary-interpreter fixture forces8086. This large passive
    # observer needs a386 DOS UMB profile; require actual high residency below.
    old = "    text=text.replace('cputype=386','cputype=8086')\n"
    assert text.count(old) == 1
    text = text.replace(old, '')
    old = 'ready_at=None;query_sent=False;xoff_sent=False'
    assert text.count(old) == 1
    text = text.replace(old, old + ';hold_sent=False')
    old = '     now=time.monotonic()\n'
    assert text.count(old) == 1
    text = text.replace(old, old + '''     if ready_at is not None and not hold_sent and now-ready_at>=1.5:
      conn.sendall(b'HOLD');event('send',b'HOLD');hold_sent=True
''')
    exec(compile(text, __file__, 'exec'), carrier.__dict__)
    results = []
    for kind in args.case or ('NONE','CALL','TX','XOFF'):
        folder = out / kind
        folder.mkdir()
        for product in (parent, child):
            shutil.copyfile(product, folder / product.name)
        events = []
        harness = carrier.adapter(out, events, kind == 'XOFF')
        harness.BINARY = folder / 'TERMINAL.EXE'
        payload = bytearray(directory(profile=args.profile))
        payload[302:311] = b'LOGIN\0\0\0\0'
        text = source(kind)
        files = {'LOGIN.ASP':text.encode(), 'LOGIN.ASX':renderer.compile_source(text), 'RENDER.COM':compiled}
        if args.reuse_driver:
            recovery='proc main\n'
            for slot in range(6):
                recovery+='fopen '+str(slot)+' "D:\\R'+str(slot)+'.LOG" "ab"\nif failure\nexit\nendif\nfputs '+str(slot)+' "PASS|"\nfclose '+str(slot)+'\n'
            recovery+='alarm 1\nendproc\n'
            files.update({'RECOVER.ASP':recovery.encode(),'RECOVER.ASX':renderer.compile_source(recovery)})
        settings = bytearray(prm(soft=int(kind == 'XOFF'), hard=int(kind != 'XOFF')))
        settings[0x79:0x79+25] = b'ATH^M'.ljust(25,b'\0')
        for offset, value in ((0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),
                              (0x4ec,0),(0x1bc,1),(0x1be,4),(0x1e6,0),(0x1e4,0)):
            struct.pack_into('<H',settings,offset,value)
        try:
            base = harness.run(kind, 'success', 'p900 enter p11000 space p700 a-z p800 escape p400 a-x',
                               directory=bytes(payload), prm=bytes(settings), profile=args.profile, files=files,
                               arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK /B:STANDARD',
                               working_drive='d', observer='RENDER', observer_high=True,
                               banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',
                               environment={'PCPLUS_TXWAIT':'2'} if kind == 'XOFF' else {})
        finally:
            (folder / 'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw = (folder / 'RENDER.BIN').read_bytes()
        head = struct.unpack_from('<7H',raw)
        observed = dict(zip(fields,struct.unpack('<5H',raw[-38:-28])))
        on, edges, last, port, owner, duration, abi = struct.unpack('<7H',raw[-28:-14])
        windows = struct.unpack('<7H',raw[-14:])
        observer_segment = struct.unpack('<H',raw[-40:-38])[0]
        post_parent = dict(zip(PARENT_FIELDS,struct.unpack('<'+str(len(PARENT_FIELDS))+'H',raw[-40-2*len(PARENT_FIELDS):-40])))
        at=len(raw)-40-2*len(PARENT_FIELDS)-2002
        post_menu_seen=struct.unpack_from('<H',raw,at)[0]
        armed_at_exit=struct.unpack_from('<H',raw,at-2)[0]
        post_menu_row=raw[at+2:at+2002].decode('cp437')
        modem = (folder / 'dosbox.log').read_text()
        wire = (folder / 'serial.bin').read_bytes()
        expected = (b'\x13\x11' if kind == 'XOFF' else b'') + b'\x1b[1;16R'+(b'\x1b[?62;2c' if args.profile==4 else b'\x1b[?1;2c')+b'KEYREADY\x1b[1;26R'
        trace = (folder / 'TRACE.LOG').read_bytes() if (folder / 'TRACE.LOG').is_file() else b''
        hold = next((e['time'] for e in events if e['kind']=='send' and e['hex']==b'HOLD'.hex()),None)
        query = next((e['time'] for e in events if e['kind']=='send' and e['hex']==b'\x1b[6n'.hex()),None)
        hangup = next((e['time'] for e in events if e['kind']=='hangup'),None)
        received = b''
        reply = None
        for event in events:
            if event['kind']=='receive':
                received += bytes.fromhex(event['hex'])
                if reply is None and b'\x1b[1;26R' in received:reply=event['time']
        checks = dict(base['checks'], real_modem_carrier_loss=modem.count('Modem response: NO CARRIER') == 1,
                      peer_hangup_after_ready=bool(base['checks'].get('peer_closed_after_script_ready')),
                      actual_query_before_hangup=all(v is not None for v in (hold,query,reply,hangup)) and hold < query <= reply < hangup,
                      parent_OFF_LINE=b'OFF-LINE' in (folder / 'SCREEN.BIN').read_bytes()[3840:4000:2],
                      typed_child_exit=head[:4] == (0x524e,1,1,1) and head[6] == (14 if kind == 'XOFF' else 0),
                      JFT_restored=raw[14:34] == raw[34:54], sink_owners_restored=raw[54:470] == raw[470:886],
                      exact_peer_wire=wire == expected, peer_capture_matches=wire == b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive'),
                      disconnect_handler_observed=(observed['armed_seen']==1 and observed['disarm_during_alarm']==0) if kind=='XOFF' else observed['armed_seen'] == observed['disarmed_seen'] == observed['disarm_during_alarm'] == int(kind != 'NONE'),
                      disconnect_registration_retired=armed_at_exit==0,
                      framed_CALL_staged=observed['pending_seen'] == int(kind == 'CALL'),
                      XOFF_observed=observed['tx_pause_seen'] == int(kind == 'XOFF'),
                      speaker_active=on > 0 and edges >= 2, speaker_cleanup=(port,owner) == (0,0),
                      duration_restored=duration == 4, child_DS_SS=abi == 1,
                      observer_actually_high=observer_segment >= 0xa000,
                      ordered_file_effects=trace == (b'BEGIN|' if kind=='XOFF' else b'BEGIN|CALL37|MAIN|' if kind=='CALL' else b'BEGIN|MAIN|'),
                      one_modem_AT_action=modem.count('Command sent to modem: ->AT<-') == int(kind == 'TX'),
                      parent_owners_retired=all(post_parent[n]==0 for n in PARENT_FIELDS[:11]+['terminal_menu_pending','_command_menu_active']),
                      parent_menu_after_child=post_menu_seen == 1 and 'P R O C O M M   P L U S   C O M M A N D   M E N U' in post_menu_row)
        result = dict(case=kind,passed=all(checks.values()),checks=checks,child_header=head,
                      carrier_observation=observed,speaker_words=[on,edges,last,port,owner,duration,abi],
                      trace_hex=trace.hex(), wire_hex=wire.hex(), window_words=windows,observer_segment=observer_segment,
                      event_times=dict(hold=hold,query=query,reply=reply,hangup=hangup),
                      post_parent=post_parent,
                      post_menu_seen=post_menu_seen,post_menu_row=post_menu_row,
                      armed_at_exit=armed_at_exit,
                      captures={str(p.relative_to(folder)):sha(p) for p in folder.iterdir() if p.is_file()})
        if args.reuse_driver:
            data=(folder/'REUSE.BIN').read_bytes()
            assert len(data)==130 and struct.unpack_from('<3H',data)==(0x414c,1,3)
            rows=[struct.unpack_from('<14H',data,6+i*28) for i in range(3)]
            checks.update(same_process_results=[r[0] for r in rows]==[14,0,0],
                          first_error_inside_ALARM=rows[0][1]==1,
                          all_owners_retired_per_invocation=all(r[2]==r[3]==r[5]==r[6]==r[7]==r[8]==0 for r in rows),
                          abort_then_normal_checkpoint=[r[4] for r in rows]==[1,0,0],
                          all_same_process_ABIs=all(r[9]==r[10]==rows[0][9] and r[11]==0x200 for r in rows),
                          INT0_unchanged=all(r[12:]==rows[0][12:] for r in rows),
                          JFT_retained_across_three_calls=data[90:110]==data[110:130],
                          all_six_slots_reused=all((folder/f'R{i}.LOG').read_bytes()==b'PASS|PASS|' for i in range(6)))
            result.update(passed=all(checks.values()),reuse_rows=rows)
        (folder / 'carrier-checks.json').write_text(json.dumps(result,indent=2)+'\n')
        results.append(result)
        print(kind,'PASS' if result['passed'] else 'FAIL '+','.join(k for k,v in checks.items() if not v),flush=True)
    for name in ('standalone/test_alarm_carrier_dos.py','standalone/test_aspect_abort_carrier_dos.py',
                 'standalone/test_aspect_renderer_dos.py','standalone/test_aspect_script_window_dos.py',
                 'standalone/alarm_speaker_observer.py','standalone/test_connection_dos.py','standalone/directory_fixtures.py'):
        sources[name] = sha(ROOT / name)
    report = dict(passed=all(c['passed'] for c in results),cases=results,sources=sources,diagnostic_reuse=args.reuse_driver,profile=args.profile,
                  products={'TERMINAL.EXE':sha(parent),'ASPECT.EXE':sha(child)},original_inputs=[],
                  scope=__doc__+' Owned peer closes socket; actual DOSBox modem changes DCD/NO CARRIER. Passive UMB observer reads gate/child policy/native disconnect state; no product writes or parser substitutes. Standard BIOS, selected VT220/ANSI profile,386 with verified UMB residency. Not physical modem/SIP/CTS or acoustic acceptance.')
    (out / 'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['passed']


if __name__ == '__main__':
    main()
