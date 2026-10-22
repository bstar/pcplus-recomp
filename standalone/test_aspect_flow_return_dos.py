#!/usr/bin/env python3
"""Actual DOS XOFF/XON script transmission and live parent handback.

The independent owned serial peer supplies flow bytes. The timer only reads
child/parent state; no product memory, UART status or VM instruction is changed.
"""
import argparse,inspect,json,re,shutil,struct,subprocess,types
from pathlib import Path
import test_aspect_renderer_dos as renderer
import test_aspect_script_window_dos as window
import test_connection_dos as connection
from directory_fixtures import directory,prm
ROOT=renderer.ROOT;sha=renderer.sha;ESC=b'\x1b'
PAYLOAD=b'0123456789ABCDEF'*128
FIELDS=('child_paused_ticks','parent_return_ticks','parent_paused_after_return')


def observer(out,entry_pause=False):
    renderer.OUT=out
    compiled,*_=renderer.observer(renderer.map_offsets(ROOT/'build/terminal/terminal.map'))
    parent=window.symbols(ROOT/'build/terminal/terminal.map');child=window.symbols(ROOT/'build/aspect-runner/ASPECT.map')
    p=out/'observer.asm';text=p.read_text()
    fields=FIELDS+('parent_entry_pause_seen',) if entry_pause else FIELDS
    text=text.replace('sample_end:\nowner_table:',''.join(n+': dw 0\n' for n in fields)+'sample_end:\nowner_table:')
    timer='''timer:
 save
 cld
 cmp word [cs:exec_seen],1
 jne .flow_done
 mov ax,[cs:parent_ds]
 or ax,ax
 jz .flow_done
 mov es,ax
 cmp word [cs:exec_done],0
 jne .parent_return
 mov ax,[cs:parent_psp]
 add ax,CHILD_OWNER_SEG+0x10
 mov es,ax
 mov ax,[es:CHILD_DS]
 or ax,ax
 jz .flow_done
 mov es,ax
 cmp word [es:CHILD_PAUSED],0
 je .flow_done
 inc word [cs:child_paused_ticks]
 jmp .flow_done
.parent_return:
 mov dx,ss
 cmp ax,dx
 jne .flow_done
 inc word [cs:parent_return_ticks]
 cmp word [es:PARENT_PAUSED],0
 je .flow_done
 inc word [cs:parent_paused_after_return]
.flow_done:
'''
    if entry_pause:
        needle=' jne .parent_return\n'
        timer=timer.replace(needle,needle+' test word [es:'+str(parent['_script_flow_flags'][1])+'],1\n jz .entry_checked\n mov word [cs:parent_entry_pause_seen],1\n.entry_checked:\n')
    for name,value in [('CHILD_OWNER_SEG',parent['render_child_ds'][0]),('CHILD_DS',parent['render_child_ds'][1]),('CHILD_PAUSED',child['uart_tx_paused'][1]),('PARENT_PAUSED',parent['uart_tx_paused'][1])]:timer=timer.replace(name,str(value))
    assert text.count('timer:\n save\n cld\n')==1
    text=text.replace('timer:\n save\n cld\n',timer);p.write_text(text)
    subprocess.run(['nasm','-fbin',str(p),'-o',str(out/'RENDER.COM')],check=True)
    return (out/'RENDER.COM').read_bytes()


def adapter(out,events,resume_after=1.2,entry_pause=False):
    text=inspect.getsource(connection.run)
    text=text.replace("out=ROOT/'build/connection-dos'/name","out=FLOW_OUT/name")
    start=text.index(' def peer():');end=text.index(' thread=threading.Thread',start)
    peer=r''' def event(kind,data=b''):
  events.append(dict(kind=kind,time=time.monotonic(),hex=data.hex()))
 def peer():
  nonlocal attempts
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(.03);line=bytearray();online=False;ready=None;held=False;resumed=False;reply=False;go_sent=False
    while not stop.is_set():
     now=time.monotonic()
     if ready is not None and not resumed and now-ready>=FLOW_RESUME_AFTER:
      conn.sendall(b'\x11');event('xon',b'\x11');resumed=True
     try:block=conn.recv(4096)
     except socket.timeout:continue
     if not block:break
     wire.extend(block);event('receive',block)
     for byte in block:
      if online:
       line.append(byte)
       if ENTRY_PAUSE and not go_sent and b'KEYREADY' in line:
        conn.sendall(b'GO');event('entry-go',b'GO');go_sent=True
       if ready is None and b'KEYREADY' in line:
        conn.sendall(b'\x13GO');event('xoff-go',b'\x13GO');ready=time.monotonic();held=True
       if ready is not None and not resumed and byte not in (17,19):
        checks['no_data_during_XOFF']=False
       if not reply and b'ready' in line:
        conn.sendall(b'\x1b[6n');event('parent-query',b'\x1b[6n');reply=True
       if line.endswith(b'+++ATH\r'):
        checks['configured_hangup_reached_wire']=True;conn.sendall(b'\r\nOK\r\n');line.clear();online=False
       continue
      if byte!=13:line.append(byte);continue
      command=bytes(line);commands.append(command.decode('ascii','replace'));line.clear()
      if command==b'ATZ':conn.sendall(b'\r\nOK\r\n')
      elif command==b'ATD'+target:
       attempts+=1;online=True
       conn.sendall(b'CONNECT\r\n'+(b'\x13' if ENTRY_PAUSE else b'')+banner);event('banner',banner)
       if ENTRY_PAUSE:ready=time.monotonic();event('entry-xoff',b'\x13')
      else:checks['unexpected_modem_command']=True
  except (OSError,AssertionError) as error:errors.append(str(error))
'''
    text=text[:start]+peer+text[end:]
    text=text.replace('checks={};attempts=0',"checks={'no_data_during_XOFF':True};attempts=0")
    # The final byte of KEYREADY itself precedes XOFF; do not classify it as
    # blocked application data in the same loop iteration.
    text=text.replace("ready=time.monotonic();held=True","ready=time.monotonic();held=True;continue")
    text=text.replace('cputype=386','cputype=8086')
    module=types.ModuleType('flow_return_peer');module.__dict__.update(connection.__dict__)
    module.__dict__.update(FLOW_OUT=out,events=events,FLOW_RESUME_AFTER=resume_after,ENTRY_PAUSE=entry_pause)
    exec(compile(text,__file__,'exec'),module.__dict__);return module


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--entry-pause',action='store_true');a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/aspect-flow-return-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
    inputs={}
    for directory_,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/directory_;manifest=json.loads((base/'manifest.json').read_text())
        assert manifest['binary_sha256']==sha(base/leaf);inputs.update(manifest['sources'])
        for file in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(file.relative_to(ROOT))]=sha(file)
    for file in (Path(__file__),Path(renderer.__file__),Path(connection.__file__),Path(window.__file__)):
        inputs[str(file.relative_to(ROOT))]=sha(file)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    compiled=observer(out,a.entry_pause);rows=[]
    script=('proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\nwaitfor "GO" 5\n'
            +'transmit "'+PAYLOAD.decode()+'"\nfopen 5 "FLOW.OK" "wb"\nfputs 5 "RESUMED"\nfclose 5\nendproc\n')
    # Use repeated short constants rather than exceeding ASPECT source-line limits.
    script=script.replace('transmit "'+PAYLOAD.decode()+'"','\n'.join('transmit "0123456789ABCDEF"' for _ in range(128)))
    for hard in (0,1):
        name='soft' if not hard else 'both';folder=out/name;folder.mkdir();events=[];peer=adapter(out,events,entry_pause=a.entry_pause)
        shutil.copy2(ROOT/'build/terminal/TERMINAL.EXE',folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        payload=bytearray(directory(profile=4));payload[302:311]=b'LOGIN\0\0\0\0'
        files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':renderer.compile_source(script),'ASPECT.EXE':(ROOT/'build/aspect-runner/ASPECT.EXE').read_bytes(),'RENDER.COM':compiled}
        try:
            r=peer.run(name,'success','p6000 r e a d y p900 a-x',directory=bytes(payload),prm=prm(soft=1,hard=hard),
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,profile=4,working_drive='d',observer='RENDER',
                banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0cLOGIN:')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw);fields=FIELDS+('parent_entry_pause_seen',) if a.entry_pause else FIELDS;state=dict(zip(fields,struct.unpack('<%dH'%len(fields),raw[-2*len(fields):])))
        wire=(folder/'serial.bin').read_bytes();application=bytes(c for c in wire if c not in (17,19))
        expected=b'ATZ\rATDCaseTest:23\r'+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+PAYLOAD+b'ready'+ESC+b'[1;24R'+b'+++ATH\r'
        checks=dict(r['checks'],actual_child_exit=header[:4]==(0x524e,1,1,1) and header[6]==0,
                    JFT_restored=raw[14:34]==raw[34:54],owners_restored=raw[54:470]==raw[470:886],
                    child_XOFF_observed=state['child_paused_ticks']>12,parent_return_observed=state['parent_return_ticks']>18,
                    parent_not_stuck_paused=state['parent_paused_after_return']==0,
                    script_resumed=(folder/'FLOW.OK').is_file() and (folder/'FLOW.OK').read_bytes()==b'RESUMED',exact_application_stream=application==expected,
                    exact_whole_wire=wire==b'ATZ\rATDCaseTest:23\r\x13\x11'+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+PAYLOAD+b'\x13\x11ready'+ESC+b'[1;24R+++ATH\r',
                    peer_stream_matches=wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive'))
        if a.entry_pause:checks['parent_pause_inherited_at_entry']=state['parent_entry_pause_seen']==1
        row=dict(case=name,passed=all(checks.values()),checks=checks,observations=state,wire_hex=wire.hex(),expected_application_hex=expected.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()})
        rows.append(row);print(json.dumps(dict(case=name,passed=row['passed'],checks=checks,observations=state)),flush=True)
    result=dict(passed=all(r['passed'] for r in rows),entry_pause=a.entry_pause,cases=rows,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),
                scope=__doc__+' SOFT and BOTH over DOSBox-X nullmodem with CTS always ready. Hardware CTS stalls, carrier reconnect and physical modem timing remain separate.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
