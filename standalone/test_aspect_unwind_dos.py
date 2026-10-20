#!/usr/bin/env python3
"""Real foreground DIV/typed abort while PROGRAM owners are live, then reuse."""
import argparse,json,re,shutil,struct,subprocess,sys,uuid
from pathlib import Path
import test_aspect_renderer_dos as render
from test_aspect_parent_process_dos import prepare_observer
from directory_fixtures import directory,prm
ROOT=render.ROOT;sha=render.sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


def scripts(phase,control=False):
    opening='set display on\nset keys off\nset fgets_crlf off\n'
    for slot in range(5):opening+=f'fopen {slot} "SLOT{slot}.BIN" "rb"\nfgetc {slot} value\n'
    opening+='fopen 5 "WRITE.BIN" "wb"\nfputs 5 "pending5"\n'
    command='run "DIVIDE.COM"' if control else 'run "NESTED.COM G"'+(' WAIT' if phase in (12,21) else '')
    first='integer value\nproc main\nwaitfor "LOGIN:" 5\n'+opening+'call worker\nmessage "FIRST RETURNED"\nendproc\n'
    first+='proc worker\ninteger guard=1234\nstring canary="LIVE FRAME"\n'+command+'\nif guard!=1234\nmessage "FAIL local"\nexit\nendif\nstrcmp canary "LIVE FRAME"\nif failure\nmessage "FAIL string"\nexit\nendif\nendproc\n'
    second='integer value\nlong position\nproc main\n'+opening+'run "NESTED.COM T" NOCLEAR\n'
    for slot in range(5):second+=f'ftell {slot} position\nif position!=1L\nmessage "FAIL position"\nexit\nendif\nfgetc {slot} value\nif value!=69\nmessage "FAIL buffered input"\nexit\nendif\nfclose {slot}\n'
    second+='fclose 5\nmessage "RECOVERY OK"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
    return first,second


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='unwind-'+uuid.uuid4().hex)
    parser.add_argument('--phase',type=int,action='append');parser.add_argument('--kind',choices=['D','A','F','L'],action='append')
    parser.add_argument('--port',type=int,choices=[1,2],default=1);parser.add_argument('--flow',choices=list('NSHB'),default='H');parser.add_argument('--control',action='store_true')
    parser.add_argument('--mouse',action='store_true')
    parser.add_argument('--break-owner',action='store_true')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    phases=args.phase or list(range(1,23));assert all(1<=p<=22 for p in phases)
    out=ROOT/('build/aspect-unwind-break/runs' if args.break_owner else 'build/aspect-unwind-mouse/runs' if args.mouse else 'build/aspect-unwind/runs')/args.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/('build/terminal-mouse-process/TERMINAL.EXE' if args.mouse else 'build/terminal-process/TERMINAL.EXE');child=ROOT/('build/aspect-fault-break/ASPECT.EXE' if args.break_owner else 'build/aspect-fault/ASPECT.EXE')
    sources={}
    for product in (parent,child):
        manifest=json.loads((product.parent/'manifest.json').read_text());assert manifest['binary_sha256']==sha(product)
        for name,digest in manifest['sources'].items():
            assert name not in sources or sources[name]==digest,name
            sources[name]=digest
    for name in ('standalone/test_aspect_unwind_dos.py','standalone/test_aspect_parent_process_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/directory_test_support.py','standalone/aspect_parent_child.asm','standalone/native_process_child.asm','src/aspect/compiler.py'):sources[name]=sha(ROOT/name)
    for name,digest in sources.items():
        assert sha(ROOT/name)==digest,name
        target=out/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    render.OUT=out;observer,size=prepare_observer(out,render.map_offsets(parent.parent/'terminal.map'),parent.parent/'terminal.map')
    harness=render.adapter(cpu='8086');results=[];port=args.port;flow=args.flow
    cases=[(p,k,False) for p in phases for k in (args.kind or ['D','A'])]
    if args.control:cases.append((0,'D',True))
    for phase,kind,control in cases:
        name='child-divide-control' if control else f'p{phase:02}-{kind}';folder=out/name;folder.mkdir()
        shutil.copyfile(parent,folder/'TERMINAL.EXE');shutil.copyfile(child,folder/'ASPECT.EXE');harness.BINARY=folder/'TERMINAL.EXE'
        subprocess.run(['nasm','-fbin','-DPORT='+hex(0x3f8 if port==1 else 0x2f8),'-DVECTOR='+str(12 if port==1 else 11),'-DIRQBIT='+str(16 if port==1 else 8),'-DREQUIRE_OUTPUT','-DMUTATE_DOS_VECTORS',*(['-DMUTATE_BREAK'] if args.break_owner else []),str(out/'sources/standalone/aspect_parent_child.asm'),'-o',str(folder/'NESTED.COM')],check=True)
        subprocess.run(['nasm','-fbin','-DCHILD_DIVIDE',str(out/'sources/standalone/native_process_child.asm'),'-o',str(folder/'DIVIDE.COM')],check=True)
        first,second=scripts(phase,control)
        files={'LOGIN.ASP':first.encode(),'LOGIN.ASX':compile_source(first),'RECOVER.ASP':second.encode(),'RECOVER.ASX':compile_source(second),
            'RENDER.COM':observer,'NESTED.COM':(folder/'NESTED.COM').read_bytes(),'DIVIDE.COM':(folder/'DIVIDE.COM').read_bytes()}
        for slot in range(5):files[f'SLOT{slot}.BIN']=b'SEED0'
        (folder/'CHILD.LOG').write_bytes(b'')
        payload=bytearray(directory(port=port));payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
        harness.RENDER_POST=render.QUERY;harness.RENDER_TRIGGER=b'Synth42\r'
        settings=bytearray(prm(port=port,soft=int(flow in 'SB'),hard=int(flow in 'HB')))
        if args.mouse:struct.pack_into('<HH',settings,0x4e4,8,4)
        result=harness.run(name,'success','p6500 space p700 r e a d y p700 a-x',directory=bytes(payload),
            prm=bytes(settings),com=port,
            arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,environment={'PCPFAULT':str(phase)+kind},
            banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',working_drive='d',observer='RENDER')
        report=struct.unpack('<20H',(folder/'FAULT.BIN').read_bytes()) if (folder/'FAULT.BIN').is_file() else ()
        raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);words=struct.unpack_from('<13H',raw,len(raw)-26-32*70-size*2)
        screen=(folder/'SCREEN.BIN').read_bytes()[::2];wire=(folder/'serial.bin').read_bytes();error=0 if control else 5 if kind in 'AL' else 12
        checks=result['checks'];checks.update(typed_first_result=bool(report) and report[:10]==(0x4652,phase,{'D':0,'A':1,'F':2,'L':3}[kind],error,0,int(not control),int(not control),0,int(not control),1),
            actual_VM_reuse=bool(report) and report[12:16]==(0,1,1,1),
            no_WAIT_in_recovery=bool(report) and report[17]<36,
            snapshot_allocation_retired=bool(report) and report[19]==1,
            real_outer_error=head[:4]==(0x524e,1,1,1) and head[6]==error,
            parent_JFT=raw[14:34]==raw[34:54],parent_file_owners=raw[54:470]==raw[470:886],
            parent_resources=words[2]==0 and raw[-size*2:-size]==raw[-size:],
            parent_lease_retired=words[7]==0 and words[8]==words[9],
            recovery_marker=b'RECOVERY OK' in screen and b'FAIL' not in screen,
            continued_serial=wire.count(b'Synth42\r')==1 and b'ready' in wire,
            actual_recovery_child=(folder/'CHILD.LOG').read_bytes().endswith(b'T'),
            output_stream=(folder/'WRITE.BIN').is_file() and (folder/'WRITE.BIN').read_bytes()==b'pending5')
        if phase==9:checks['overwritten_live_frame_restored']=bool(report) and report[10]>report[11]>0 and report[18]==1
        if phase==20:checks['uninitialized_backup_not_restored']=bool(report) and report[10]>report[11]>0 and report[18]==0
        if control:checks['child_fault_is_not_parent_fault']=bool(report) and report[16]==12 and b'FIRST RETURNED' in screen
        result.update(passed=all(checks.values()),phase=phase,kind=kind,port=port,flow=flow,report_words=report,passive_header=head,owner_words=words,compared_parent_bytes=size)
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL '+','.join(k for k,v in checks.items() if not v),flush=True)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=all(r['passed'] for r in results),experimental_mouse=args.mouse,experimental_break_owner=args.break_owner,cases=results,parent_sha256=sha(parent),child_sha256=sha(child),sources=sources,
        checker_sha256=sha(Path(__file__)),observer_sha256=sha(out/'RENDER.COM'),
        scope='Actual DOS checkpoint recovery and same-process VM/UART/renderer reuse. Diagnostic probes raise real DIV or native typed abort; kernel/BIOS/allocator corruption and recursive recovery faults are not simulated.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
