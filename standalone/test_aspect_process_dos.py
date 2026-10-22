#!/usr/bin/env python3
"""Real ASPECT streams/VM -> native PROGRAM -> DOS child -> VM/source compiler."""
import argparse,itertools,json,os,re,shutil,socket,struct,subprocess,sys,threading,uuid
from pathlib import Path
import build_aspect_process as build
import build_aspect_compiler_dos as dos_compiler
ROOT=build.ROOT;OUT=build.OUT;sha=build.sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

DECL='integer finished,value,setting\nlong position\nstring preserved\n'
OPEN='putenv "CTRLVAR=OWNED"\nset keys off\nset display off\nset fgets_crlf off\n'
for slot in range(5):OPEN+=f'fopen {slot} "SLOT{slot}.BIN" "rb"\nfgetc {slot} value\nfgetc {slot} value\n'
OPEN+='fopen 5 "SLOT5.BIN" "wb"\nfputs 5 "pending5"\npreserved="GLOBAL ALIVE"\n'
READY='transmit "D"\npause 1\ncomgetc value\nif value!=0\nmessage "FAIL initial byte"\nexit\nendif\n'
VERIFY=''
for slot in range(5):VERIFY+=f'ftell {slot} position\nif position!=2L\nmessage "FAIL position"\nexit\nendif\nfgetc {slot} value\nif value!=69\nmessage "FAIL buffered read"\nexit\nendif\nfseek {slot} 2L 0\n'
VERIFY+='strcmp preserved "GLOBAL ALIVE"\nif failure\nmessage "FAIL global"\nexit\nendif\n'
DRAIN=''
for byte in (26,128,255):DRAIN+=f'comgetc value\nif value!={byte}\nmessage "FAIL queued byte"\nexit\nendif\n'
FINISH='transmit "R"\nwaitfor "NEXT" 5\nif failure\nmessage "FAIL input after return"\nexit\nendif\nfinished=317\ntransmit "F"\nwaitfor "END" 5\nendproc\n'


def fixtures(port):
    child=f'OWN{port}'
    common=DECL+'proc main\n'+OPEN+READY
    worker=('proc worker\ninteger guard=1234\nstring local_value="LOCAL ALIVE"\n'
        f'run "{child} S"\nif guard!=1234\nmessage "FAIL local integer"\nexit\nendif\n'
        'strcmp local_value "LOCAL ALIVE"\nif failure\nmessage "FAIL local string"\nexit\nendif\nendproc\n')
    full=common+'findfirst "ENUM\\*.DAT"\nif found==0\nmessage "FAIL first enumeration"\nexit\nendif\ncall worker\n'+DRAIN+VERIFY+f'run "{child} N" NOCLEAR\nrun "{child} W" WAIT\n'
    full+='run "ABSENT.COM"\nif success\nmessage "FAIL missing target"\nexit\nendif\n'
    full+='dos "ver > SYSTEM.OUT"\nrun "ROUTE.BAT"\nrun "OWN.EXE"\n'
    full+=f'putenv "PATH=C:\\BIN"\nrun "PATHCH S"\nputenv "COMSPEC=SHELLGO.COM"\n'
    full+='strcmp "A" "A"\nshell\nif failure\nmessage "FAIL SHELL comparison"\nexit\nendif\n'
    full+='isfile "SHELL.OUT"\nif failure\nmessage "FAIL real shell"\nexit\nendif\n'
    full+='putenv "COMSPEC="\nstrcmp "A" "A"\nshell\nif failure\nmessage "FAIL missing SHELL comparison"\nexit\nendif\n'
    full+='putenv "COMSPEC=Z:\\COMMAND.COM"\n'+VERIFY+'execute "NEXT.ASP"\nendproc\n'+worker
    next_source=DECL+'proc main\nstrcmp preserved ""\nif failure\nmessage "FAIL per-file string reset"\nexit\nendif\n'
    next_source+='getenv "CTRLVAR" preserved\nstrcmp preserved "OWNED"\nif failure\nmessage "FAIL persistent environment"\nexit\nendif\n'
    next_source+='fetch fgets_crlf setting\nif setting!=0\nmessage "FAIL persistent setting"\nexit\nendif\n'
    next_source+='preserved="GLOBAL ALIVE"\n'+f'run "{child} S"\n'+VERIFY
    next_source+='findnext\nif found==0\nmessage "FAIL enumeration continuation"\nexit\nendif\nfindnext\nif found\nmessage "FAIL enumeration exhaustion"\nexit\nendif\n'+FINISH
    solo=common+'call worker\n'+DRAIN+VERIFY+FINISH+worker
    divide=common+'call worker\n'+DRAIN+VERIFY+FINISH+worker.replace(f'run "{child} S"','run "DIVIDE.COM"')
    abort=common+'call worker\nvalue=1/finished\nendproc\n'+worker
    budget=common+'call worker\nwhile 1\nendwhile\nendproc\n'+worker
    recover=DECL+'proc main\n'+OPEN+f'run "{child} S"\n'+DRAIN+VERIFY+FINISH
    return dict(FULL=full,NEXT=next_source,SOLO=solo,DIVIDE=divide,ABORT=abort,BUDGET=budget,RECOVER=recover)


def run(folder,port,flow,kind,manifest):
    folder.mkdir();sources=fixtures(port)
    for name,source in sources.items():
        (folder/(name+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('ascii'))
        if name!='NEXT':(folder/(name+'.ASX')).write_bytes(compile_source(source))
    shutil.copyfile(OUT/'ASPECT.EXE',folder/'ASPECT.EXE')
    shutil.copyfile(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE',folder/'ASPCOMP.EXE')
    include='-I'+str(ROOT/'standalone')+'/'
    subprocess.run(['nasm','-fbin',include,'-DCHILD_PORT='+str(port),str(ROOT/'standalone/aspect_process_child.asm'),'-o',str(folder/f'OWN{port}.COM')],check=True)
    (folder/'BIN').mkdir();shutil.copyfile(folder/f'OWN{port}.COM',folder/'BIN/PATHCH.COM')
    (folder/'ENUM').mkdir();(folder/'ENUM/A.DAT').write_bytes(b'A');(folder/'ENUM/B.DAT').write_bytes(b'B')
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/aspect_process_shell.asm'),'-o',str(folder/'SHELLGO.COM')],check=True)
    subprocess.run(['nasm','-fbin','-DCHILD_DIVIDE',str(ROOT/'standalone/native_process_child.asm'),'-o',str(folder/'DIVIDE.COM')],check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-fe=OWN.EXE',str(ROOT/'standalone/aspect_process_exe.c')],cwd=folder,check=True)
    for slot in range(5):(folder/f'SLOT{slot}.BIN').write_bytes(f'SEED{slot}'.encode())
    (folder/'ROUTE.BAT').write_bytes(b'@echo off\r\necho BATCHPASS>BATCH.OUT\r\n')
    source_name='FULL' if kind=='full' else 'DIVIDE' if kind=='divide' else kind.upper() if kind in ('abort','budget') else 'SOLO'
    argument='' if kind=='full' else ' '+kind
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/process_capture_idle.asm'),'-o',str(folder/'DRAIN.COM')],check=True)
    (folder/'PCPTEST.BAT').write_text(f'@echo off\nset COMSPEC=Z:\\COMMAND.COM\nASPECT {source_name}.ASX /S{port}:0003:03:{flow}{argument} >CHECKS.TXT\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto done\n:bad\necho FAIL>RESULT.TXT\n:done\nDRAIN\nif errorlevel 1 goto drainbad\nexit\n:drainbad\necho FAIL>RESULT.TXT\nexit\n')
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(.2)
    wire=bytearray();sent=[];errors=[];stop=threading.Event()
    def peer():
        try:
            connection=None
            while not stop.is_set():
                try:connection,_=listener.accept();break
                except socket.timeout:continue
            if connection is None:return
            with connection:
                connection.settimeout(.1)
                while not stop.is_set():
                    try:chunk=connection.recv(4096)
                    except socket.timeout:continue
                    if not chunk:break
                    wire.extend(chunk)
                    if b'D' in wire and not sent:connection.sendall(bytes.fromhex('001a80ff'));sent.append('initial')
                    if b'R' in wire and len(sent)==1:connection.sendall(b'NEXT');sent.append('after')
                    if b'F' in wire and len(sent)==2:connection.sendall(b'END');sent.append('finished')
        except OSError as error:
            if not stop.is_set():errors.append(str(error))
    thread=threading.Thread(target=peer,daemon=True);thread.start()
    serial=[f'serial{i}=disabled' for i in range(1,5)];serial[port-1]=f'serial{port}=nullmodem server:127.0.0.1 port:{listener.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'
    (folder/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[serial]\n'+ '\n'.join(serial)+f'\n[autoexec]\nmount c "{folder}"\nc:\nPCPTEST.BAT\nexit\n')
    timeout=False
    try:
        with (folder/'dosbox.log').open('w') as log:
            try:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=35)
            except subprocess.TimeoutExpired:timeout=True
    finally:thread.join(timeout=1);stop.set();listener.close();thread.join(timeout=1)
    (folder/'wire.bin').write_bytes(wire)
    text=(folder/'CHECKS.TXT').read_text(errors='replace') if (folder/'CHECKS.TXT').exists() else ''
    match=re.search(r'ASPECT PROCESS COM(\d) ([NSHB]) result(\d+) raw(\d+) calls(\d+) private(\d+) compiler(\d+) checks(\d+) failures(\d+)',text)
    expected_data=b'DRF'
    brackets=11 if kind=='full' else 2 if kind in ('abort','budget') else 1
    expected_wire=b'\x11D'+b'\x13\x11'*brackets+b'RF\x13' if flow in 'SB' else expected_data
    checks=dict(DOS_pass=not timeout and (folder/'RESULT.TXT').exists() and (folder/'RESULT.TXT').read_text().strip()=='PASS',
        assertions=bool(match) and int(match[9])==0,no_script_failure='FAIL' not in text,
        wire_data=bytes(b for b in wire if b not in (17,19))==expected_data,exact_wire=bytes(wire)==expected_wire,peer_no_error=not errors,
        binary_unchanged=sha(folder/'ASPECT.EXE')==manifest['binary_sha256'])
    raw_values=[37,37,37,65535,0,0,37,37,0,1,37] if kind=='full' else [65535 if kind=='memory' else 12 if kind=='divide' else 37]*(2 if kind in ('abort','budget') else 1)
    expected_trace=[(i,raw,int(kind=='full' and i==4),int(kind=='full' and i==2),int(kind!='full' or i!=1)) for i,raw in enumerate(raw_values)]
    trace=[tuple(map(int,row)) for row in re.findall(r'EXTERNAL (\d+) raw(\d+) processor(\d+) wait(\d+) save(\d+)',text)]
    drain=struct.unpack('<4H',(folder/'DRAIN.BIN').read_bytes()) if (folder/'DRAIN.BIN').is_file() else ()
    checks['post_return_emulator_drain_observed']=len(drain)==4 and (drain[2]+65536*drain[3])>=2
    checks['all_command_results_and_flags']=trace==expected_trace
    checks['VM_status_and_invocations']=bool(match) and int(match[3])==({'abort':11,'budget':6}.get(kind,0)) and int(match[5])==len(expected_trace) and int(match[6])==7 and int(match[7])==int(kind=='full')
    checks['streams_preserved']=all((folder/f'SLOT{i}.BIN').read_bytes()==f'SEED{i}'.encode() for i in range(5)) and (folder/'SLOT5.BIN').read_bytes()==b'pending5'
    if kind=='full':checks.update(real_shell=(folder/'SHELL.OUT').is_file() and (folder/'SHELL.OUT').read_bytes()==b'SHELLREAL',real_exe=(folder/'EXE.OUT').is_file() and (folder/'EXE.OUT').read_bytes()==b'REAL EXE',batch=(folder/'BATCH.OUT').is_file() and (folder/'BATCH.OUT').read_text().strip()=='BATCHPASS',DOS_source_compiled=(folder/'NEXT.ASX').is_file() and (folder/'NEXT.ASX').read_bytes()==compile_source(sources['NEXT']))
    checks['all_peer_stages']=sent==['initial','after','finished']
    if kind=='large':
        overlap=re.search(r'ARENA borrowed(\d+) live-frame(\d+)',text)
        checks['actual_live_frame_overlap']=bool(overlap) and int(overlap[1])>int(overlap[2])>0
    checks['real_inheritance_control']='control98 JFT-preserved' in text
    if kind in ('abort','budget'):checks['same_process_recovery']='recovery1 control98' in text
    result=dict(passed=all(checks.values()),checks=checks,port=port,flow=flow,kind=kind,timed_out=timeout,
        tx_hex=bytes(wire).hex(),peer_errors=errors,assertions=int(match[8]) if match else 0,
        runtime_result=int(match[3]) if match else None,raw_status=int(match[4]) if match else None,
        calls=int(match[5]) if match else None,compiler_calls=int(match[7]) if match else None,trace=trace,
        artifacts={p.name:sha(p) for p in folder.iterdir() if p.is_file()})
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'COM{port}/{flow}/{kind}:', 'PASS' if result['passed'] else checks,flush=True)
    if not result['passed']:print(text,flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='run-'+uuid.uuid4().hex)
    parser.add_argument('--port',type=int,choices=(1,2),action='append');parser.add_argument('--flow',choices=list('NSHB'),action='append')
    parser.add_argument('--kind',choices=('full','fallback','large','memory','divide','abort','budget'),action='append')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=OUT/'runs'/args.label;folder.mkdir(parents=True,exist_ok=False)
    dos_compiler.main()
    build.main(ROOT/'standalone/aspect_process_diagnostic.c')
    manifest=json.loads((OUT/'manifest.json').read_text());shutil.copyfile(OUT/'manifest.json',folder/'manifest.json')
    for name,digest in manifest['sources'].items():
        assert sha(ROOT/name)==digest,name
        target=folder/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    owned_sources={name:sha(ROOT/name) for name in ('standalone/aspect_process_child.asm','standalone/aspect_process_shell.asm','standalone/aspect_process_exe.c','standalone/native_process_child.asm','standalone/process_capture_idle.asm','src/aspect/compiler.py')}
    for name in owned_sources:
        target=folder/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    cases=[]
    for port,flow,kind in itertools.product(args.port or (1,2),args.flow or 'NSHB',args.kind or ('full','fallback','large','memory','divide','abort','budget')):
        cases.append(run(folder/f'com{port}-{flow}-{kind}',port,flow,kind,manifest))
        if not cases[-1]['passed']:break
    result=dict(passed=all(c['passed'] for c in cases),cases=cases,owned_sources=owned_sources,binary_sha256=manifest['binary_sha256'],manifest_sha256=sha(folder/'manifest.json'),checker_sha256=sha(Path(__file__)),scope=manifest['scope'])
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(folder)
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
