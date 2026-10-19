#!/usr/bin/env python3
"""Real DOS query services, per-drive CWDs and native/fixed DOSVER controls."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import test_aspect_script_files_dos as base
from build_aspect_runtime import ROOT, ASM, OUT as COMPONENT
from compiler import compile_source

sha = base.sha
SOURCES = {
    'SYSTEM': '''integer free_status,version_status,dir_status,bad_status
long free_current,free_c,free_d,free_bad
string cwd,explicit_c,explicit_d,invalid_path,version
proc main
version="OLD-VERSION"
strcmp "A" "B"
diskfree 0 free_current
free_status=failure
dosver version
version_status=failure
diskfree 3 free_c
diskfree 4 free_d
diskfree 5 free_bad
getdir 0 cwd
dir_status=failure
getdir 3 explicit_c
getdir 4 explicit_d
getdir 5 invalid_path
bad_status=failure
endproc
''',
    'LOCAL': '''string local_version,local_cwd,param_version,param_cwd,register_version
long param_free
proc main
call local_worker
call param_worker with "OLD" "OLD" 0L
s0="OLD"
dosver s0
strcpy register_version s0
endproc
proc local_worker
string ver="OLD",folder="OLD"
dosver ver
getdir 0 folder
strcpy local_version ver
strcpy local_cwd folder
endproc
proc param_worker
strparm ver
strparm folder
longparm available
dosver ver
getdir 0 folder
diskfree 0 available
strcpy param_version ver
strcpy param_cwd folder
param_free=available
endproc
''',
    'SIX': '''string folder,version
long available
proc main
''' + ''.join(f'fopen {i} "C:\\STREAM.BIN" "rb"\n' for i in range(6)) + '''getdir 0 folder
dosver version
diskfree 0 available
endproc
''',
    'CHAIN1': r'''proc main
execute "C:\CHAIN2"
endproc
''',
    'CHAIN2': '''string folder,version
long available
proc main
getdir 0 folder
dosver version
diskfree 0 available
endproc
''',
    'DRIVES': r'''string from_d,retained_c,from_c,retained_d
proc main
chdir "D:\LIBRARY\CLASSIC"
getdir 0 from_d
getdir 3 retained_c
chdir "C:\GAMES\ADVENT"
getdir 0 from_c
getdir 4 retained_d
endproc
''',
    'CLISRC': '''string folder,version
long available
proc main
getdir 0 folder
if failure
exit
endif
dosver version
diskfree 0 available
if available > 0L
message "SYSTEM QUERIES READY"
endif
endproc
''',
}
CASES = [('SYSTEM', 0), ('LOCAL', 0), ('SIX', 0), ('CHAIN1', 0), ('DRIVES', 0)]
for prefix in ('D', 'V', 'F'):
    CASES.extend([(prefix + 'TRUNC', 5), (prefix + 'BAD', 7)])

C = base.C.split('static void run(')[0] + r'''
#include <direct.h>
static char version[12];
static unsigned long free_c,free_d;
static unsigned long available(unsigned drive){
 struct diskfree_t value;
 if(_dos_getdiskfree(drive,&value))return 0xffffffffUL;
 return (unsigned)(value.sectors_per_cluster*value.bytes_per_sector)*(unsigned long)value.avail_clusters;
}
static void run(const char *name,unsigned expected){
 unsigned result,i,drives,flags=cpu_flags();char path[32];
 void (__interrupt __far *vector)(void)=_dos_getvect(0);
 current=name;++cases;
 _dos_setdrive(4,&drives);ck(chdir("\\LIBRARY\\CLASSIC")==0);
 _dos_setdrive(3,&drives);ck(chdir("\\GAMES\\ADVENT")==0);
 free_c=available(3);free_d=available(4);
 sprintf(path,"C:\\%s.ASX",name);result=aspect_runtime_run(path,2000);
 ck(result==expected);ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(!runtime_script_file_live&&!runtime_live&&!runtime_find_live&&!runtime_file.handle&&!runtime_abi_bad);
 if(!strcmp(name,"SYSTEM")){
  ck(runtime_integer_b[0]==65535U&&runtime_integer_b[1]==65535U);
  ck(runtime_integer_b[2]==0&&runtime_integer_b[3]==15);
  ck(runtime_longs[0]==free_c&&runtime_longs[1]==free_c&&runtime_longs[2]==free_d&&runtime_longs[3]==0xffffffffUL);
  ck(!strcmp((char *)runtime_string_snapshot[0],"C:\\GAMES\\ADVENT"));
  ck(!strcmp((char *)runtime_string_snapshot[1],"C:\\GAMES\\ADVENT"));
  ck(!strcmp((char *)runtime_string_snapshot[2],"D:\\LIBRARY\\CLASSIC"));
  ck(!strcmp((char *)runtime_string_snapshot[3],"E:\\"));
#ifdef QUERY_NATIVE_CONTROL
  ck(!strcmp((char *)runtime_string_snapshot[4],"OLD-VERSION"));
#else
  ck(!strcmp((char *)runtime_string_snapshot[4],version));
#endif
 }else if(!strcmp(name,"LOCAL")){
  ck(!strcmp((char *)runtime_string_snapshot[0],version));
  ck(!strcmp((char *)runtime_string_snapshot[1],"C:\\GAMES\\ADVENT"));
  ck(!strcmp((char *)runtime_string_snapshot[2],version));
  ck(!strcmp((char *)runtime_string_snapshot[3],"C:\\GAMES\\ADVENT"));
  ck(!strcmp((char *)runtime_string_snapshot[4],version));ck(runtime_longs[0]==free_c);
 }else if(!strcmp(name,"SIX")||!strcmp(name,"CHAIN1")){
  ck(!strcmp((char *)runtime_string_snapshot[0],"C:\\GAMES\\ADVENT"));
  ck(!strcmp((char *)runtime_string_snapshot[1],version));ck(runtime_longs[0]==free_c);
  if(!strcmp(name,"SIX"))ck(runtime_script_file_peak==6&&runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
  else ck(runtime_cleanup_count==2);
 }else if(!strcmp(name,"DRIVES")){
  static const char *values[]={"D:\\LIBRARY\\CLASSIC","C:\\GAMES\\ADVENT","C:\\GAMES\\ADVENT","D:\\LIBRARY\\CLASSIC"};
  for(i=0;i<4;++i)ck(!strcmp((char *)runtime_string_snapshot[i],values[i]));
 }
 printf("CASE %s error%u\n",name,result);
}
int main(void){unsigned cycle,far_count=0,far_after_count=0,near_count,near_after_count,i,drives;
 union REGS in,out;in.h.ah=0x30;intdos(&in,&out);sprintf(version,"%u.%02u",out.h.al,out.h.ah);
#ifdef QUERY_NATIVE_CONTROL
 run("SYSTEM",0);printf("NATIVE_QUERY_CONTROL %u checks %u failures DOSVER-global=OLD\n",checks,failures);return failures?1:0;
#else
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    out = ROOT / 'build/aspect-system-query-dos' / args.label
    out.mkdir(parents=True, exist_ok=False)
    stage, other = out / 'drive', out / 'other'
    stage.mkdir()
    (stage / 'GAMES/ADVENT').mkdir(parents=True)
    (other / 'LIBRARY/CLASSIC').mkdir(parents=True)
    binary = ROOT / 'build/aspect-runner/ASPECT.EXE'
    compiler = ROOT / 'build/aspect-compiler-dos/ASPCOMP.EXE'
    before = {str(p.relative_to(ROOT)): sha(p) for p in (binary, compiler, Path(__file__))}
    for f in (binary, compiler):
        shutil.copyfile(f, stage / f.name)
    for name, source in SOURCES.items():
        compile_source(source)
        (stage / (name + '.ASP')).write_bytes(source.replace('\n', '\r\n').encode('cp437'))
    for prefix, command, decl in [('D', 'getdir 0 value', 'string'), ('V', 'dosver value', 'string'), ('F', 'diskfree 0 value', 'long')]:
        valid = compile_source(f'{decl} value\nproc main\n{command}\nendproc\n')
        assert valid[-3:] == (b'\x8e\x00\x94' if decl == 'long' else b'\x8c\x00\x94')
        (stage / (prefix + 'TRUNC.ASX')).write_bytes(valid[:-3])
        (stage / (prefix + 'BAD.ASX')).write_bytes(valid[:-3] + b'\xff\x00\x94')
    (stage / 'STREAM.BIN').write_bytes(b'unchanged-query-stream')
    calls = ''.join(f' run("{name}",{error});\n' for name, error in CASES)
    program = C + calls + ''' current="baseline";ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<30;++cycle){
''' + calls + r''' }
 current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 _dos_setdrive(3,&drives);ck(chdir("\\")==0);
 printf("QUERY_VM %u cases %u checks %u failures farheap%u nearheap%u JFT-preserved\n",cases,checks,failures,far_count,near_count);return failures?1:0;
#endif
}
'''
    (out / 'harness.c').write_text(program)
    cs = ['runtime.c', 'environment_runtime.c', 'script_file_runtime.c', 'file_info_runtime.c', 'file_times_runtime.c', 'enumeration_runtime.c', 'file_io.c', 'script_path.c', 'serial_runtime.c', 'receive_runtime.c', 'directory_runtime.c', 'when_runtime.c', 'set_runtime.c', 'find_runtime.c']
    for native in (False, True):
        name = 'NATIVE' if native else 'QUERYVM'
        objects = [str(ROOT / 'build/aspect-system-query/system_query.obj') if native and n == 'system_query' else str(COMPONENT / (n + '.obj')) for n, _, _ in ASM]
        subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k8192', '-dASPECT_RUNTIME_DIAGNOSTIC',
                        *(['-dQUERY_NATIVE_CONTROL', '-wcd=202'] if native else []),
                        '-i=' + str(ROOT / 'src/aspect'), '-i=' + str(ROOT / 'standalone'), '-fm=' + str(out / (name + '.map')), '-fe=' + str(stage / (name + '.EXE')),
                        str(out / 'harness.c'), str(ROOT / 'standalone/compiler_heap_snapshot.c'), *[str(ROOT / 'src/aspect' / n) for n in cs], *objects], cwd=out, check=True)
    batch = ['@echo off']
    for name in SOURCES:
        if name != 'CLISRC':
            batch += [f'ASPCOMP {name}.ASP >{name}.CMP', 'if errorlevel 1 goto failed']
    batch += ['ASPECT CLISRC.ASP >CLI.LOG', 'if errorlevel 1 goto failed', 'NATIVE >C:\\NATIVE.TXT', 'if errorlevel 1 goto failed', 'C:', 'CD \\', 'QUERYVM >C:\\RESULT.TXT', 'if errorlevel 1 goto failed', 'C:', 'CD \\', 'echo PASS>PASS.TXT', 'goto done', ':failed', 'C:', 'CD \\', 'echo FAIL>FAIL.TXT', ':done', 'exit']
    (stage / 'RUN.BAT').write_text('\n'.join(batch) + '\n')
    (out / 'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{stage}"\nmount d "{other}"\nc:\ncall RUN.BAT\nexit\n')
    with (out / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')], cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'), stdout=log, stderr=log, check=True, timeout=120)
    output = (stage / 'RESULT.TXT').read_text() if (stage / 'RESULT.TXT').exists() else 'Inspect compiler/CLI/native logs'
    assert (stage / 'PASS.TXT').exists() and not (stage / 'FAIL.TXT').exists(), output
    summary = re.search(r'^QUERY_VM (\d+) cases (\d+) checks 0 failures farheap(\d+) nearheap(\d+) JFT-preserved$', output, re.M)
    assert summary, output
    native = (stage / 'NATIVE.TXT').read_text()
    assert re.search(r'NATIVE_QUERY_CONTROL \d+ checks 0 failures DOSVER-global=OLD', native)
    for name, source in SOURCES.items():
        assert (stage / (name + '.ASX')).read_bytes() == compile_source(source), name
    assert b'SYSTEM QUERIES READY' in (stage / 'CLI.LOG').read_bytes()
    assert (stage / 'STREAM.BIN').read_bytes() == b'unchanged-query-stream'
    assert before == {p: sha(ROOT / p) for p in before}
    report = dict(passed=True, cases=int(summary[1]), assertions=int(summary[2]), same_process_rounds=31,
                  DOS_summary=summary[0], native_control_summary=native.strip().splitlines()[-1],
                  native_control_sha256=sha(stage / 'NATIVE.EXE'), native_control_result_sha256=sha(stage / 'NATIVE.TXT'),
                  native_object_sha256=sha(ROOT / 'build/aspect-system-query/system_query.obj'), runtime_object_sha256=sha(COMPONENT / 'system_query.obj'),
                  runner_sha256=sha(binary), compiler_sha256=sha(compiler), checker_sha256=sha(Path(__file__)),
                  reused_harness_sha256=sha(Path(base.__file__)), harness_sha256=sha(out / 'harness.c'), result_sha256=sha(stage / 'RESULT.TXT'),
                  fixtures=SOURCES, original_inputs=[],
                  scope='Actual8086 DOS query interrupts/VM and source compiler, two independently retained drive CWDs, raw invalid-drive errors/prefixes, native DISKFREE arithmetic and unchanged comparison. DOSVER far/local/parameter/register writeback; native core control retains OLD global. Six open streams, EXECUTE, malformed destinations, repeated heap/JFT/INT0/FLAGS/ABI cleanup. No physical/whole-application claim.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['DOS_summary'])
    print(report['native_control_summary'])


if __name__ == '__main__':
    main()
