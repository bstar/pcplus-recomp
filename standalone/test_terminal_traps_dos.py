#!/usr/bin/env python3
"""Real DOS terminal traps, raw-child handoff and independent exit observer."""
import argparse,json,re,shutil,struct,subprocess,types,uuid
from pathlib import Path
import test_aspect_renderer_dos as render
from modem_fixtures import fixture
ROOT=render.ROOT;sha=render.sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mouse',action='store_true')
    p.add_argument('--terminal-prefix',type=Path,help='Build directory prefix before -probe-MODE')
    p.add_argument('--label',default='traps-'+uuid.uuid4().hex);p.add_argument('--case',action='append',choices=[str(m)+str(b) for m in range(5) for b in [0,1]])
    args=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/terminal-trap-tests'/args.label;out.mkdir(parents=True,exist_ok=False)
    helpers=['test_terminal_traps_dos.py','terminal_trap_parent.c','trap_startup_child.asm','test_connection_dos.py','test_terminal.py',
        'test_aspect_renderer_dos.py','modem_fixtures.py','terminal_config_fixtures.py','directory_fixtures.py','directory_test_support.py']
    sources={'standalone/'+n:sha(ROOT/'standalone'/n) for n in helpers};products={}
    modes=sorted({int(c[0]) for c in args.case}) if args.case else list(range(5))
    for mode in modes:
        binary=ROOT/'build'/('terminal-traps-mouse-probe-'+str(mode) if args.mouse else 'terminal-traps-probe-'+str(mode))/'TERMINAL.EXE'
        if args.terminal_prefix:binary=Path(str(args.terminal_prefix.resolve())+'-probe-'+str(mode))/'TERMINAL.EXE'
        manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['terminal_traps'] and manifest['terminal_trap_probe']==mode
        assert manifest['experimental_mouse']==args.mouse
        assert manifest['binary_sha256']==sha(binary)
        for n,h in manifest['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
        products[mode]=(binary,manifest)
    for n,h in sources.items():
        assert sha(ROOT/n)==h,n
        target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    source=(ROOT/'standalone/test_connection_dos.py').read_text().replace('cputype=386','cputype=8086')
    replacements={"out=ROOT/'build/connection-dos'/name":'out=TRAP_OUT/name',
        "checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'":"checks['actual_screen_snapshot']=len(screen)==4000",
        r'C:\\TERMINAL {arguments}':r'D:\\TROBS {TRAP_MODE} {arguments}'}
    for old,new in replacements.items():assert source.count(old)==1;source=source.replace(old,new)
    harness=types.ModuleType('trap_connection');harness.__file__=str(ROOT/'standalone/test_connection_dos.py');harness.TRAP_OUT=out
    exec(compile(source,harness.__file__,'exec'),harness.__dict__);results=[]
    for mode in modes:
        binary,manifest=products[mode];build=out/('parent-'+str(mode));build.mkdir()
        syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(binary.parent/'terminal.map').read_text(),re.M|re.I)}
        offsets=render.map_offsets(binary.parent/'terminal.map')
        seg,off=syms['terminal_trap_probe_foreign'];ds,hits=syms['terminal_trap_probe_hits']
        defines=dict(EXPECTED_ISR_SEG=seg,EXPECTED_ISR_OFF=off,EXPECTED_DATA_SEG=ds,EXPECTED_HITS_OFF=hits)
        subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',*['-d'+n+'='+str(v) for n,v in defines.items()],'-fe=TROBS.EXE','-fm=TROBS.map',str(out/'sources/standalone/terminal_trap_parent.c')],cwd=build,check=True)
        child_defines=dict(PARENT_DGROUP=manifest['memory_layout']['near_relative_segment'],**{'PARENT_'+k.upper():offsets['terminal_trap_'+k] for k in ['phase','owner','originals','flag']})
        subprocess.run(['nasm','-fbin',*['-D'+n+'='+str(v) for n,v in child_defines.items()],str(out/'sources/standalone/trap_startup_child.asm'),'-o',str(build/'PRMEDIT.EXE')],check=True)
        for initial in [0,1]:
            name=str(mode)+str(initial)
            if args.case and name not in args.case:continue
            folder=out/name;folder.mkdir();shutil.copyfile(binary,folder/'TERMINAL.EXE');harness.BINARY=folder/'TERMINAL.EXE';harness.TRAP_MODE=name
            settings=bytearray(fixture(timeout=5));struct.pack_into('<HH',settings,0x4e4,8,4)
            result=harness.run(name,'success','p2200 r e a d y p2600 a-x',prm=bytes(settings),arguments='/S @TEST.PRM /D:CaseTest:23',
                files={'TROBS.EXE':(build/'TROBS.EXE').read_bytes(),'PRMEDIT.EXE':(build/'PRMEDIT.EXE').read_bytes()},working_drive='d')
            report=(folder/'TRAPPAR.OUT').read_text() if (folder/'TRAPPAR.OUT').exists() else ''
            match=re.fullmatch(r'TRAPOBS mode=(\d+) break=(\d+) checks=(\d+) failures=(\d+) child=(\d+) pressure=(\d+)\s*',report)
            result['checks'].update(independent_DOS_parent=bool(match) and int(match[4])==0 and int(match[3])>=15,
                ordinary_keyboard_before_event=b'ready' in (folder/'serial.bin').read_bytes())
            result.update(passed=all(result['checks'].values()),mode=mode,initial_break=initial,mouse=args.mouse,parent_report=report,
                parent_sha256=sha(build/'TROBS.EXE'),child_sha256=sha(binary),startup_child_sha256=sha(build/'PRMEDIT.EXE'))
            (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(name,'TRAP PASS' if result['passed'] else 'TRAP FAIL',flush=True)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    report=dict(passed=all(c['passed'] for c in results),cases=results,sources=sources,checker_sha256=sha(Path(__file__)),
        scope='Real8086 DOS terminal/EXEC/IRQ handlers and kernel Ctrl-C via BIOS keys/DOS08; critical event is explicitly synthetic. Unknown-vector retention checked after largest-free-block overwrite. No physical modem/device-fault acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
