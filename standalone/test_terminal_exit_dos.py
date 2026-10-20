#!/usr/bin/env python3
"""Actual terminal final-exit guard through an independent DOS EXEC parent."""
import argparse,json,re,shutil,struct,subprocess,types,uuid
from pathlib import Path
import test_aspect_renderer_dos as render
from modem_fixtures import fixture
ROOT=render.ROOT;sha=render.sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mouse',action='store_true')
    p.add_argument('--process-bank',action='store_true')
    p.add_argument('--label',default='exit-'+uuid.uuid4().hex);p.add_argument('--case',action='append',choices=[str(m)+str(b) for m in range(4) for b in [0,1]])
    args=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/terminal-exit-tests'/args.label;out.mkdir(parents=True,exist_ok=False)
    source=(ROOT/'standalone/test_connection_dos.py').read_text().replace('cputype=386','cputype=8086')
    replacements={"out=ROOT/'build/connection-dos'/name":'out=RENDER_OUT/name',
        "checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'":"checks['actual_screen_snapshot']=len(screen)==4000",
        r'C:\\TERMINAL {arguments}':r'D:\\TEOBS {EXIT_MODE} {arguments}'}
    for old,new in replacements.items():assert source.count(old)==1;source=source.replace(old,new)
    harness=types.ModuleType('terminal_exit_harness');harness.__file__=str(ROOT/'standalone/test_connection_dos.py');harness.RENDER_OUT=out
    exec(compile(source,harness.__file__,'exec'),harness.__dict__)
    results=[];identities={n:sha(ROOT/n) for n in ['standalone/test_terminal_exit_dos.py','standalone/terminal_exit_parent.c','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/test_aspect_renderer_dos.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/directory_fixtures.py','standalone/directory_test_support.py']}
    modes=sorted({int(c[0]) for c in args.case}) if args.case else list(range(4))
    products={}
    for mode in modes:
        binary=ROOT/'build'/('terminal-exit-mouse-probe-'+str(mode) if args.mouse else 'terminal-exit-probe-'+str(mode))/'TERMINAL.EXE'
        if args.process_bank:binary=ROOT/'build'/('terminal-process-bank-mouse-probe-'+str(mode) if args.mouse else 'terminal-process-bank-probe-'+str(mode))/'TERMINAL.EXE'
        manifest=json.loads((binary.parent/'manifest.json').read_text())
        assert manifest['terminal_exit_guard'] and manifest['terminal_exit_probe']==mode and manifest['experimental_mouse']==args.mouse
        assert manifest['binary_sha256']==sha(binary)
        for name,digest in manifest['sources'].items():
            assert name not in identities or identities[name]==digest,name
            identities[name]=digest
        products[mode]=(binary,manifest)
    for name,digest in identities.items():
        assert sha(ROOT/name)==digest,name
        target=out/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    for mode in modes:
        binary,manifest=products[mode]
        syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(binary.parent/'terminal.map').read_text(),re.M|re.I)}
        code_seg,code_off=syms['terminal_exit_probe_isr'];data_seg,hits=syms['terminal_exit_probe_hits']
        parent=out/('parent-'+str(mode));parent.mkdir()
        defines=dict(EXPECTED_KEEP=manifest['memory_layout']['retained_parent_paragraphs'],EXPECTED_ISR_SEG=code_seg,EXPECTED_ISR_OFF=code_off,EXPECTED_DATA_SEG=data_seg,EXPECTED_HITS_OFF=hits)
        subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',*['-d'+n+'='+str(v) for n,v in defines.items()],'-fe=TEOBS.EXE','-fm=TEOBS.map',str(ROOT/'standalone/terminal_exit_parent.c')],cwd=parent,check=True)
        for initial in [0,1]:
            name=str(mode)+str(initial)
            if args.case and name not in args.case:continue
            folder=out/name;folder.mkdir();shutil.copyfile(binary,folder/'TERMINAL.EXE');harness.BINARY=folder/'TERMINAL.EXE';harness.EXIT_MODE=name
            settings=bytearray(fixture(timeout=5));struct.pack_into('<HH',settings,0x4e4,8,4)
            keys='p2200 a-z p300 a p300 a b s e n t . a s x enter p1200 space p500 r e a d y p500 a-x'
            result=harness.run(name,'success',keys,prm=bytes(settings),files={'TEOBS.EXE':(parent/'TEOBS.EXE').read_bytes()},arguments='@D:\\TEST.PRM /D:CaseTest:23',working_drive='d')
            report=(folder/'TERMPAR.OUT').read_text() if (folder/'TERMPAR.OUT').exists() else ''
            match=re.fullmatch(r'TERMEXIT mode=(\d+) break=(\d+) checks=(\d+) failures=(\d+) status=(\d+) retained=(\d+) pressure=(\d+)\s*',report)
            checks=result['checks'];checks.update(independent_parent=bool(match) and int(match[4])==0 and int(match[3])>=13,
                serial_keyboard_before_exit=b'ready' in (folder/'serial.bin').read_bytes())
            result.update(passed=all(checks.values()),banked_process=args.process_bank,mouse=args.mouse,mode=mode,initial_break=initial,parent_report=report,child_sha256=sha(binary),parent_sha256=sha(parent/'TEOBS.EXE'),linked_addresses=defines)
            (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL',flush=True)
    for name,digest in identities.items():
        assert sha(ROOT/name)==digest,name
    report=dict(passed=all(r['passed'] for r in results),cases=results,sources=identities,checker_sha256=sha(Path(__file__)),scope='Actual terminal and DOS EXEC parent, full free-block overwrite and source-owned ISR. Busy/foreign-PSP probes are controlled flags/tokens, not a corrupt DOS kernel. No physical hardware acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
