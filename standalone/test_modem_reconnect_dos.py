#!/usr/bin/env python3
"""Actual DOS carrier loss under XOFF, followed by Alt-D virtual-modem redial.

An owned TCP BBS drops its first carrier. A passive observer reads parent state
after the first child returns. A second socket must complete an automatic
script and manual query. No product flag or hardware status is injected.
"""
import argparse,inspect,json,re,shutil,struct,subprocess,types
from pathlib import Path
import test_aspect_abort_carrier_dos as carrier
import test_aspect_renderer_dos as renderer
import test_aspect_script_window_dos as window
from directory_fixtures import directory,prm
ROOT=carrier.ROOT;sha=carrier.sha;ESC=b'\x1b'
FIELDS=('parent_disconnected_ticks','parent_stale_pause_seen','parent_reconnected_ticks')


def adapter(out,events,gap):
    text=inspect.getsource(carrier.connection.run).replace("out=ROOT/'build/connection-dos'/name",'out=CASE_OUT/name')
    start=text.index(' def peer():');end=text.index(' thread=threading.Thread',start)
    peer=r''' def event(kind,data=b'',session=0):
  events.append(dict(kind=kind,time=time.monotonic(),hex=data.hex(),session=session))
 def peer():
  nonlocal attempts
  try:
   server.settimeout(.1)
   while not stop.is_set() and attempts<2:
    try:conn,_=server.accept()
    except socket.timeout:continue
    attempts+=1;session=attempts;event('connected',session=session)
    with conn:
     conn.settimeout(.03);local=bytearray();ready=None;xoff=False;completed=None
     conn.sendall(banner);event('send',banner,session)
     while not stop.is_set():
      now=time.monotonic()
      if session==1 and ready is not None and not xoff:
       conn.sendall(b'\x13');event('xoff',b'\x13',session);xoff=True
      if session==1 and ready is not None and now-ready>=1:
       conn.shutdown(socket.SHUT_RDWR);event('first-hangup',session=session);checks['first_peer_carrier_drop']=True;break
      if session==2 and completed is not None and now-completed>=.2:
       conn.shutdown(socket.SHUT_RDWR);event('completed-hangup',session=session);break
      try:block=conn.recv(4096)
      except socket.timeout:continue
      if not block:break
      wire.extend(block);local.extend(block);event('receive',block,session)
      if ready is None and b'KEYREADY' in local:
       ready=time.monotonic();event('script-ready',session=session)
       if session==2:
        conn.sendall(b'\x1b[6nEND');event('send',b'\x1b[6nEND',session)
      if session==2 and b'ready' in local and not checks.get('manual_query_sent'):
       conn.sendall(b'\x1b[6n');event('send',b'\x1b[6n',session);checks['manual_query_sent']=True
      if session==2 and completed is None and b'ready\x1b[1;25R' in local:completed=time.monotonic()
  except OSError as error:
   if not stop.is_set():errors.append(str(error))
'''
    text=text[:start]+peer+text[end:]
    bind=" server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(5)"
    assert text.count(bind)==1
    text=text.replace(bind,bind+r'''
 target=('127.0.0.1:'+str(server.getsockname()[1])).encode()
 contact=bytearray(directory);at=250+(directory_entry-1)*114
 contact[at+25:at+46]=target.ljust(21,b'\0');directory=bytes(contact)
 (out/'TEST.DIR').write_bytes(directory);(out/'DIAL.IN').write_bytes(directory)
''')
    serial="f'nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'"
    assert text.count(serial)==1;text=text.replace(serial,"'modem listenport:0'")
    text=text.replace("commands[:2]==['ATZ',('ATD'+target.decode('ascii'))]",'attempts==2')
    text=text.replace("checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'","checks['screen_snapshot_complete']=len(screen)==4000")
    text=text.replace('timeout=20)','timeout=35)').replace('cputype=386','cputype=8086')
    module=types.ModuleType('reconnect_modem_peer');module.__dict__.update(carrier.connection.__dict__)
    module.__dict__.update(CASE_OUT=out,events=events,EXPECT_GAP=gap)
    exec(compile(text,__file__,'exec'),module.__dict__);return module


def observer(out):
    renderer.OUT=out;renderer.observer(renderer.map_offsets(ROOT/'build/terminal/terminal.map'))
    symbols=window.symbols(ROOT/'build/terminal/terminal.map');path=out/'observer.asm';text=path.read_text()
    text=text.replace('sample_end:\nowner_table:',''.join(n+': dw 0\n' for n in FIELDS)+'sample_end:\nowner_table:')
    timer='''timer:
 save
 cld
 cmp word [cs:exec_done],1
 jne .reconnect_done
 mov ax,[cs:parent_ds]
 mov dx,ss
 cmp ax,dx
 jne .reconnect_done
 mov es,ax
 cmp word [es:STATE],0
 jne .online
 cmp word [es:STATUS],6
 jne .reconnect_done
 inc word [cs:parent_disconnected_ticks]
 cmp word [es:PAUSED],0
 je .reconnect_done
 mov word [cs:parent_stale_pause_seen],1
 jmp .reconnect_done
.online:
 cmp word [cs:parent_disconnected_ticks],0
 je .reconnect_done
 cmp word [es:STATE],6
 jne .reconnect_done
 inc word [cs:parent_reconnected_ticks]
.reconnect_done:
'''
    for name,value in [('STATE',symbols['connection_state'][1]),('STATUS',symbols['connection_status'][1]),('PAUSED',symbols['uart_tx_paused'][1])]:timer=timer.replace(name,str(value))
    assert text.count('timer:\n save\n cld\n')==1;text=text.replace('timer:\n save\n cld\n',timer)
    path.write_text(text);subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'RENDER.COM')],check=True)
    return (out/'RENDER.COM').read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--expect-gap',action='store_true');p.add_argument('--flow',choices=['soft','both'],action='append');a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/modem-reconnect-dos'/a.label;out.mkdir(parents=True,exist_ok=False);inputs={}
    for d,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/d;m=json.loads((base/'manifest.json').read_text());assert sha(base/leaf)==m['binary_sha256'];inputs.update(m['sources'])
        for file in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(file.relative_to(ROOT))]=sha(file)
    for file in (Path(__file__),Path(carrier.__file__),Path(carrier.connection.__file__),Path(renderer.__file__),Path(window.__file__)):
        inputs[str(file.relative_to(ROOT))]=sha(file)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    compiled=observer(out);rows=[]
    script='proc main\nwaitfor "LOGIN:" 5\nset duplex full\nwhen disconnect transmit "^MAT^M"\ntransmit "KEYREADY"\nwaitfor "END" 30\nif waitfor\ntransmit "SECONDOK"\nfopen 5 "SECOND.OK" "wb"\nfputs 5 "RECONNECTED"\nfclose 5\nendif\nendproc\n'
    for flow in a.flow or ['soft','both']:
        folder=out/flow;folder.mkdir();events=[];peer=adapter(out,events,a.expect_gap)
        shutil.copy2(ROOT/'build/terminal/TERMINAL.EXE',folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        payload=bytearray(directory(profile=4));payload[302:311]=b'LOGIN\0\0\0\0'
        settings=bytearray(prm(soft=1,hard=int(flow=='both')));settings[0x79:0x79+25]=b'ATH^M'.ljust(25,b'\0')
        files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':renderer.compile_source(script),'ASPECT.EXE':(ROOT/'build/aspect-runner/ASPECT.EXE').read_bytes(),'RENDER.COM':compiled}
        try:
            r=peer.run(flow,'success','p6000 a-d p4000 r e a d y p800 a-x',directory=bytes(payload),prm=bytes(settings),profile=4,files=files,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',working_drive='d',observer='RENDER',accounting_delta=2,
                banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0cLOGIN:')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);state=dict(zip(FIELDS,struct.unpack('<3H',raw[-6:])))
        sessions=[e for e in events if e['kind']=='connected'];second=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and e['session']==2)
        clean_second=bytes(c for c in second if c not in (17,19))
        checks=dict(r['checks'],first_child_exit=head[:4]==(0x524e,1,1,1) and head[6]==14,JFT_restored=raw[14:34]==raw[34:54],owners_restored=raw[54:470]==raw[470:886],DCD_loss_observed=state['parent_disconnected_ticks']>18,first_carrier_drop=sum(e['kind']=='first-hangup' for e in events)==1,
            second_connection=len(sessions)==2,second_script=(folder/'SECOND.OK').is_file() and (folder/'SECOND.OK').read_bytes()==b'RECONNECTED',manual_after_reconnect=b'SECONDOKready' in clean_second and ESC+b'[1;25R' in second,parent_online_again=state['parent_reconnected_ticks']>18,
            final_peer_close=sum(e['kind']=='completed-hangup' for e in events)==1)
        log=(folder/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log)
        dial=(folder/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
        desired=dict(no_modem_ERROR='Modem response: ERROR' not in log,clean_modem_commands=commands==['ATZ','ATD'+dial,'ATZ','ATD'+dial])
        passed=all(checks.values()) and (all(not v for v in desired.values()) if a.expect_gap else all(desired.values()))
        rows.append(dict(case=flow,passed=passed,checks=checks,desired_checks=desired,observations=state,second_wire_hex=second.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=flow,passed=passed,checks=checks,desired_checks=desired,observations=state,second_wire_hex=second.hex())),flush=True)
    report=dict(passed=all(r['passed'] for r in rows),gap_reproduced=a.expect_gap,compatibility_accepted=not a.expect_gap and all(r['passed'] for r in rows),cases=rows,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),scope=__doc__+' Observer covers first child JFT/owner return, not second child frame. Overall hardware snapshots, actual second socket/script/file/manual stream and directory accounting cover reconnect. No physical modem/timing claim.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']


if __name__=='__main__':main()
