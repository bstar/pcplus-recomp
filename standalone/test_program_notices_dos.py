#!/usr/bin/env python3
"""Actual ASPECT PROGRAM error popup, outer faults and same-VM UART reuse."""
import argparse,hashlib,itertools,json,os,shutil,socket,struct,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
PAYLOAD=bytes(i for i in range(256) if i not in (17,19))*2
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def scripts():
    opening='set display off\nset keys off\nset fgets_crlf off\n'
    for i in range(5):opening+=f'fopen {i} "SLOT{i}.BIN" "rb"\nfgetc {i} value\nfgetc {i} value\n'
    first='integer value\nproc main\n'+opening+'fopen 5 "WRITE.BIN" "wb"\nfputs 5 "FIRST"\ntransmit "R"\nrun "ABSENT.COM"\nif success\ntransmit "BAD"\nendif\nendproc\n'
    second='integer value\nlong position\nproc main\n'+opening+'fopen 5 "WRITE.BIN" "ab"\nfputs 5 "SECOND"\nrun "ABSENT.COM"\nif success\ntransmit "BAD"\nexit\nendif\n'
    for i in range(5):second+=f'ftell {i} position\nif position!=2L\ntransmit "BAD"\nexit\nendif\nfgetc {i} value\nif value!=69\ntransmit "BAD"\nexit\nendif\nfclose {i}\n'
    for value in PAYLOAD:second+=f'comgetc value\nif value!={value}\ntransmit "BAD"\nexit\nendif\n'
    second+='fclose 5\ntransmit "P"\nwaitfor "READY!" 5\nif failure\ntransmit "BAD"\nexit\nendif\ntransmit "F"\nwaitfor "END" 5\nendproc\n'
    return first,second
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',action='append',choices=['0N','1D','2D','3D','2A','2F']);parser.add_argument('--port',type=int,choices=[1,2],default=1);parser.add_argument('--flow',choices=list('NSHB'),default='H')
    args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/aspect-notice-fault';m=json.loads((base/'manifest.json').read_text());assert m['original_inputs']==[] and m['experimental_notice_error_binding']
    assert sha(base/'ASPECT.EXE')==m['binary_sha256'] and all(sha(ROOT/p)==h for p,h in m['sources'].items())
    cases=[(args.port,args.flow,mode) for mode in args.mode] if args.mode else [(p,f,'0N') for p,f in itertools.product([1,2],'NSHB')]+[(1,'H',mode) for mode in ['1D','2D','3D','2A','2F']]+[(2,'B','2F')]
    first,second=scripts();results=[]
    for port,flow,mode in cases:
        folder=out/f'com{port}-{flow}-{mode}';folder.mkdir();shutil.copy2(base/'ASPECT.EXE',folder/'ASPECT.EXE')
        for name,source in [('FIRST',first),('RECOVER',second)]:
            (folder/(name+'.ASP')).write_text(source);(folder/(name+'.ASX')).write_bytes(compile_source(source))
        for i in range(5):(folder/f'SLOT{i}.BIN').write_bytes(b'SEED0')
        server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2)
        stop=threading.Event();done=threading.Event();wire=bytearray();events=[];errors=[];started=time.monotonic()
        def peer():
            try:
                connection=None
                while not stop.is_set():
                    try:connection,_=server.accept();break
                    except socket.timeout:continue
                if connection is None:return
                stage=0
                with connection:
                    connection.settimeout(.1)
                    while not stop.is_set():
                        try:data=connection.recv(4096)
                        except socket.timeout:continue
                        if not data:events.append(dict(kind='EOF',seconds=time.monotonic()-started));break
                        wire.extend(data);events.append(dict(kind='receive',hex=data.hex(),seconds=time.monotonic()-started))
                        if b'R' in wire and not stage:
                            packet=(b'\x13'+PAYLOAD+b'\x11') if flow in 'SB' else PAYLOAD
                            connection.sendall(packet);events.append(dict(kind='send',hex=packet.hex(),seconds=time.monotonic()-started));stage=1
                        if b'P' in wire and stage==1:
                            connection.sendall(b'READY!');events.append(dict(kind='send',hex=b'READY!'.hex(),seconds=time.monotonic()-started));stage=2
                        if b'F' in wire and stage==2:
                            connection.sendall(b'END');events.append(dict(kind='send',hex=b'END'.hex(),seconds=time.monotonic()-started));stage=3
            except OSError as error:
                if not stop.is_set():errors.append(str(error))
            finally:done.set()
        thread=threading.Thread(target=peer,daemon=True);thread.start()
        serial=[f'serial{i}=disabled' for i in range(1,5)];serial[port-1]=f'serial{port}=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'
        expected=0 if mode=='0N' else 5 if mode[1]=='A' else 12
        config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
{chr(10).join(serial)}
[autoexec]
@echo off
mount c "{folder}"
c:
set PCPNOTICE={mode}{port}
ASPECT FIRST.ASX 60000 /S{port}:0003:03:{flow} >OUTPUT.TXT
if errorlevel {expected+1} goto failed
if errorlevel {expected} goto passed
:failed
echo FAIL>FAIL.TXT
exit
:passed
echo PASS>PASS.TXT
exit
'''
        (folder/'dosbox.conf').write_text(config);code=None;timed_out=False
        try:
            with (folder/'dosbox.log').open('w') as log:
                try:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=35);code=r.returncode
                except subprocess.TimeoutExpired:timed_out=True
            done.wait(2)
        finally:stop.set();server.close();thread.join(1)
        (folder/'wire.bin').write_bytes(wire);(folder/'peer.json').write_text(json.dumps(dict(events=events,errors=errors),indent=2)+'\n')
        raw=(folder/'NOTICE.BIN').read_bytes() if (folder/'NOTICE.BIN').exists() else b'';words=struct.unpack('<29H',raw) if len(raw)==58 else ()
        phase=int(mode[0]);kind=1 if mode[1]=='A' else 2 if mode[1]=='F' else 0
        expected_wire=b'\x11R'+b'\x13\x11'*2+b'PF\x13' if flow in 'SB' else b'RPF'
        checks=dict(emulator_exit=code==0 and not timed_out,DOS_exit=(folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),report=bool(words),wire_exact=bytes(wire)==expected_wire,peer_complete=not errors and events and events[-1]['kind']=='EOF',private_output=(folder/'WRITE.BIN').exists() and (folder/'WRITE.BIN').read_bytes()==b'FIRSTSECOND')
        if words:checks.update(header=words[:4]==(0x4e46,phase,kind,int(phase!=0)),first_status=words[4]==expected,errno=words[5:7]==(1,2),first_notice_status=words[7] in ([9] if phase==2 else [0,1,2]),first_window=words[8]==0,first_retired=words[9:11]==(1,1),actual_popup=words[11]==int(phase!=1),first_retained=words[12]==(0 if phase==1 else 508),second_retained=words[13]==508,first_resources=words[14]==1,raw_first=words[15]==65535,first_recovery=words[16]==int(phase!=0),first_serial=words[17]==1,reusable_VM=words[18:20]==(0,2),second_notice=words[20] in [0,1,2] and words[21]==0,second_retired=words[22:25]==(1,1,1),raw_second=words[25]==65535,recovery_count=words[26]==int(phase!=0),second_serial=words[27]==1)
        if words:checks['ordinary_CLI_status']=words[28]==expected
        row=dict(passed=all(checks.values()),port=port,flow=flow,mode=mode,checks=checks,report_words=words,folder=str(folder.relative_to(ROOT)),captures_sha256={p.name:sha(p) for p in folder.iterdir() if p.is_file()})
        results.append(row);(out/'result.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in results),cases=results,binary_sha256=m['binary_sha256'],sources={**m['sources'],str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)), 'src/aspect/compiler.py':sha(ROOT/'src/aspect/compiler.py')},scope=__doc__+' Failed real DOS name lookup preserves FFFF raw status; independent socket peer supplies508 bytes consumed by ASPECT only after both popups. Real DIV/foreign-DS DIV/native typed abort; screen/cursor/JFT/PSP/vectors and six streams checked around two actual VM runs. Raw CLI, not attached-parent fault/physical acceptance.'),indent=2)+'\n')
        print(json.dumps(dict(port=port,flow=flow,mode=mode,passed=row['passed'],failed=[name for name,value in checks.items() if not value],words=words)),flush=True)
        assert row['passed']
if __name__=='__main__':main()
