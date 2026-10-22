#!/usr/bin/env python3
"""Compare cancellation/retry through the actual stock DOSBox-X modem parser."""
import argparse, inspect, json, re, shutil, types
from pathlib import Path
import test_connection_dos as base
from modem_fixtures import fixture
from audit_aspect_transmit_wait import ROOT, sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline-product','candidate-product','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();OUT=args.output.resolve()
    assert OUT.is_relative_to(ROOT/'build') and not OUT.exists();OUT.mkdir(parents=True)
    text=inspect.getsource(base.run).replace("out=ROOT/'build/connection-dos'/name",'out=CASE_OUT/name')
    start=text.index(' def peer():');end=text.index(' thread=threading.Thread',start)
    peer=''' def peer():
      try:
       conn,_=server.accept()
       with conn:
        conn.settimeout(.05)
        conn.sendall(b'\\x1b[2J\\x1b[HFIRST BYTE SAFE\\x1b[6n\\x1b[0c')
        while not stop.is_set():
         try:block=conn.recv(4096)
         except socket.timeout:continue
         if not block:break
         wire.extend(block)
      except OSError as error:errors.append(str(error))
    '''
    peer_lines=peer.splitlines();peer=peer_lines[0]+'\n'+'\n'.join(line[4:] for line in peer_lines[1:])+'\n'
    text=text[:start]+peer+text[end:]
    text=text.replace('server.settimeout(5)','server.settimeout(20)')
    text=text.replace("f'nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'","'modem listenport:0'")
    text=text.replace("else:checks['actual_init_and_dial']=commands[:2]==['ATZ',('ATD'+target.decode('ascii'))]","else:checks['stock_modem_backend']=True")
    text=text.replace('cputype=386','cputype=8086')
    module=types.ModuleType('stock_modem');module.__dict__.update(base.__dict__);module.CASE_OUT=OUT
    exec(compile(text,__file__,'exec'),module.__dict__)
    reports=[]
    for name,product in [('baseline',args.baseline_product.resolve()),('candidate',args.candidate_product.resolve())]:
     admitted=OUT/name/'admitted-product';admitted.mkdir(parents=True)
     shutil.copy2(product/'TERMINAL.EXE',admitted/'TERMINAL.EXE');module.BINARY=admitted/'TERMINAL.EXE'
     data=bytearray(fixture(timeout=15));init=b'AT'+b' '*30+b'Z^M';data[0x18:0x47]=init.ljust(47,b'\0')
     # Allocate the listening socket in run, then build the actual dial argument
     # from that socket's port rather than assuming modem hostname behavior.
     src=text.replace("arguments=arguments or '@D:\\\\TEST.PRM /D:CaseTest:23'","arguments='@D:\\\\TEST.PRM /D:127.0.0.1:'+str(server.getsockname()[1])")
     assert src!=text
     exec(compile(src,__file__,'exec'),module.__dict__)
     r=module.run(name,'success','p1000 escape p3000 a-d p9000 r e a d y p700 a-x',prm=bytes(data),profile=6)
     log=(OUT/name/'dosbox.log').read_bytes();cmds=re.findall(rb'Command sent to modem: ->(.*?)<-',log)
     responses=re.findall(rb'Modem response: ([^\r\n]+)',log)
     clean=b'AT'+b' '*30+b'Z'
     assert r['passed'] and cmds[-1].startswith(b'ATD127.0.0.1:')
     if name=='baseline':assert len(cmds)==2 and b'\x1bAT' in cmds[0] and responses[:2]==[b'ERROR',b'CONNECT 57600']
     else:assert len(cmds)==3 and b'\x1b' in cmds[0] and cmds[1]==clean and responses[:3]==[b'OK',b'OK',b'CONNECT 57600']
     reports.append(dict(case=name,passed=True,parent_sha256=sha(module.BINARY),commands_hex=[c.hex() for c in cmds],responses=[c.decode('ascii') for c in responses],captures={str(p.relative_to(OUT/name)):sha(p) for p in (OUT/name).rglob('*') if p.is_file()}))
     print(name,'passed',flush=True)
    (OUT/'experiment-source.py').write_text(Path(__file__).read_text())

    (OUT/'checks.json').write_text(json.dumps(dict(passed=True,cases=reports,checker_sha256=sha(Path(__file__)),base_checker_sha256=sha(Path(base.__file__)),scope='Actual stock DOSBox-X modem parser; timed Escape during long configured initialization, followed by retry and ANSI replies. Old joins partial command and gets ERROR; candidate gets clean initialization OK. SOFTWARE backend accepts loopback address dialing; no such command is assumed for physical Boca. No physical modem acceptance.'),indent=2)+'\n')


if __name__=='__main__':main()
