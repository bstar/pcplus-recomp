#!/usr/bin/env python3
"""Real DOS child changes UART/vector; independent loopback peer checks return."""
import argparse,itertools,json,os,re,shutil,socket,subprocess,threading,time,uuid
from pathlib import Path
from build_process_serial import ROOT,OUT,sha


def run(parent,port,flow,manifest):
    folder=parent/f'com{port}-{flow}';folder.mkdir()
    for name in ('PSERIAL.EXE',f'UART{port}.COM'):shutil.copyfile(OUT/name,folder/name)
    server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2)
    wire=bytearray();sent=[];errors=[];stop=threading.Event()
    def peer():
        try:
            connection=None
            while not stop.is_set():
                try:connection,_=server.accept();break
                except socket.timeout:continue
            if connection is None:return
            with connection:
                connection.settimeout(.1)
                while not stop.is_set():
                    try:chunk=connection.recv(4096)
                    except socket.timeout:continue
                    if not chunk:break
                    wire.extend(chunk)
                    if b'D' in wire and not sent:connection.sendall(b'\0\x1a\x80\xff');sent.append('initial')
                    if b'R' in wire and len(sent)==1:connection.sendall(b'NEXT');sent.append('after')
        except OSError as e:
            if not stop.is_set():errors.append(str(e))
    thread=threading.Thread(target=peer,daemon=True);thread.start()
    serial=[f'serial{i}=disabled' for i in range(1,5)]
    serial[port-1]=f'serial{port}=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'
    (folder/'PCPTEST.BAT').write_text(f'@echo off\nPSERIAL /S{port}:0003:03:{flow} >CHECKS.TXT\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto done\n:bad\necho FAIL>RESULT.TXT\n:done\nexit\n')
    (folder/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[serial]
{chr(10).join(serial)}
[autoexec]
mount c "{folder}"
c:
PCPTEST.BAT
exit
''')
    timeout=False;started=time.monotonic()
    try:
        with (folder/'dosbox.log').open('w') as log:
            try:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],
                env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
            except subprocess.TimeoutExpired:timeout=True
    finally:stop.set();server.close();thread.join(timeout=1)
    (folder/'wire.bin').write_bytes(wire)
    text=(folder/'CHECKS.TXT').read_text() if (folder/'CHECKS.TXT').exists() else ''
    match=re.search(r'PROCESS SERIAL COM(\d) ([NSHB]) (\d+) checks (\d+) failures',text)
    expected=(b'\x11D\x13\x11RF\x13' if flow in 'SB' else b'DRF')
    checks=dict(DOS_pass=not timeout and (folder/'RESULT.TXT').exists() and (folder/'RESULT.TXT').read_text().strip()=='PASS',
        assertions=bool(match) and match[1]==str(port) and match[2]==flow and int(match[4])==0,
        exact_wire=bytes(wire)==expected,peer_stages=sent==['initial','after'],peer_no_error=not errors,
        actual_child=(folder/'CHILD.OUT').is_file() and (folder/'CHILD.OUT').read_bytes()==f'COM{port}'.encode(),
        executable_unchanged=sha(folder/'PSERIAL.EXE')==manifest['binary_sha256'])
    report=dict(passed=all(checks.values()),checks=checks,assertions=int(match[3]) if match else 0,
        port=port,flow=flow,timed_out=timeout,elapsed=round(time.monotonic()-started,3),
        tx_hex=bytes(wire).hex(),expected_tx_hex=expected.hex(),peer_errors=errors,
        artifacts={p.name:sha(p) for p in folder.iterdir() if p.is_file()})
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'COM{port}/{flow}:', 'PASS' if report['passed'] else checks,flush=True)
    if not report['passed']:print(text,flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='run-'+uuid.uuid4().hex)
    parser.add_argument('--port',type=int,choices=(1,2),action='append');parser.add_argument('--flow',choices=list('NSHB'),action='append')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=OUT/'runs'/args.label;folder.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((OUT/'manifest.json').read_text());shutil.copyfile(OUT/'manifest.json',folder/'manifest.json')
    for p,h in {**manifest['sources'],**manifest['process_sources']}.items():
        assert sha(ROOT/p)==h,p
        dest=folder/'sources'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,dest)
    reports=[]
    for port,flow in itertools.product(args.port or (1,2),args.flow or 'NSHB'):
        reports.append(run(folder,port,flow,manifest))
        if not reports[-1]['passed']:break
    result=dict(passed=all(r['passed'] for r in reports),cases=reports,binary_sha256=manifest['binary_sha256'],
        manifest_sha256=sha(folder/'manifest.json'),checker_sha256=sha(Path(__file__)),scope=manifest['scope'])
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(folder)
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
