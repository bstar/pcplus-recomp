#!/usr/bin/env python3
"""Build and test PCHELP context/HLP decoding from fresh source, without originals."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--compat-help',type=Path,help='Explicit optional original-resource check; excluded from normal source-only tests');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    names=['src/help/format.h','src/help/format.c','standalone/help_format_diagnostic.c','standalone/help_format_inspect.c','standalone/test_help_format_dos.py']
    sources={n:sha(ROOT/n) for n in names}
    for n in names:
        target=out/'source'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    c_sources=[str(out/'source'/n) for n in ['src/help/format.c','standalone/help_format_diagnostic.c']]
    build=['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-fm=HELPFMT.map','-fe=HELPFMT.EXE',*c_sources]
    subprocess.run(build,cwd=out,check=True)
    inspector_sources=[str(out/'source'/n) for n in ['src/help/format.c','standalone/help_format_inspect.c']]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-fe=HELPREAD.EXE',*inspector_sources],cwd=out,check=True)
    host=out/'host';host.mkdir();subprocess.run(['cc','-std=c89','-Wall','-Wextra','-Werror','-o',str(host/'helpfmt'),*c_sources],check=True)
    h=subprocess.run([str(host/'helpfmt')],cwd=host,check=True,capture_output=True)
    subprocess.run(['cc','-std=c89','-Wall','-Wextra','-Werror','-o',str(host/'helpread'),*inspector_sources],check=True)
    host_read=subprocess.run([str(host/'helpread'),'HELPTEST.HLP'],cwd=host,check=True,capture_output=True)
    originals=[];compat_commands='';compat_host=None
    if a.compat_help:
        original=a.compat_help.resolve();shutil.copyfile(original,out/'COMPAT.HLP')
        originals=[dict(sha256=sha(original),bytes=original.stat().st_size)]
        compat_host=subprocess.run([str(host/'helpread'),str(original)],cwd=host,check=True,capture_output=True)
        compat_commands='HELPREAD COMPAT.HLP >COMPAT.TXT\nif errorlevel 1 goto fail\n'
    rebuild=out/'rebuild';rebuild.mkdir();subprocess.run(build,cwd=rebuild,check=True)
    cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
c:
HELPFMT >OUTPUT.TXT
if errorlevel 1 goto fail
HELPREAD HELPTEST.HLP >INDEX.TXT
if errorlevel 1 goto fail
{compat_commands}
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
'''
    (out/'dosbox.conf').write_text(cfg)
    with (out/'dosbox.log').open('w') as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
    raw=(out/'OUTPUT.TXT').read_bytes() if (out/'OUTPUT.TXT').exists() else b''
    summary=re.fullmatch(rb'HELPFMT checks=(\d+) failures=0\r\n',raw)
    checks=dict(emulator_exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
        self_checks=bool(summary) and int(summary[1])>=50,
        host_DOS_checks_match=h.stdout.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),
        host_DOS_file_bytes_match=(host/'HELPTEST.HLP').read_bytes()==(out/'HELPTEST.HLP').read_bytes(),
        host_DOS_index_reader_match=host_read.stdout.replace(b'\r\n',b'\n')==(out/'INDEX.TXT').read_bytes().replace(b'\r\n',b'\n')==b'HELP INDEX topics=2 lines=3 bytes=65543\n',
        fresh_rebuild=sha(out/'HELPFMT.EXE')==sha(rebuild/'HELPFMT.EXE'),
        sources_unchanged=all(sha(ROOT/n)==digest==sha(out/'source'/n) for n,digest in sources.items()))
    if a.compat_help:
        checks['explicit_original_host_DOS_match']=compat_host.stdout.replace(b'\r\n',b'\n')==(out/'COMPAT.TXT').read_bytes().replace(b'\r\n',b'\n')
        checks['explicit_original_unchanged']=sha(a.compat_help.resolve())==sha(out/'COMPAT.HLP')==originals[0]['sha256']
    result=dict(passed=all(checks.values()),checks=checks,self_checks=int(summary[1]) if summary else None,
        binary_sha256=sha(out/'HELPFMT.EXE'),reader_sha256=sha(out/'HELPREAD.EXE'),original_inputs=originals,sources=sources,command=build,
        scope='Fresh-source C89 host and actual8086 DOS component:18-byte context decoding without dereference, checked decimal far pointers, signed topic fallback,3-byte HLP header,38-byte index records,32-byte CP437 title bounds, full index totals/order/ranges and actual DOS file seek/read beyond64KiB. No help UI, original resource dependency, parent ABI admission, contextual Alt-Z integration, nested EXEC or full application acceptance.')
    result['captures_sha256']={str(x.relative_to(out)):sha(x) for x in out.rglob('*') if x.is_file()}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k in ('passed','checks','self_checks','binary_sha256')}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
