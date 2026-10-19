#!/usr/bin/env python3
"""Real DOS environment ownership, native alias control and child inheritance."""
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
    'CONTROL': '''integer first,second
string a,b
proc main
putenv "LOC_A=one"
first=failure
putenv "LOC_B=two"
second=failure
getenv "loc_a" a
getenv "loc_b" b
endproc
''',
    'CHECKENV': '''string a,b
proc main
getenv "LOC_A" a
getenv "LOC_B" b
putenv "LOC_A="
putenv "LOC_B="
endproc
''',
    'ROUND': '''integer set_status,bad_status,get_status
string inherited,a,b,replaced,after_bad,removed,empty_name,missing
proc main
getenv "loc_parent" inherited
putenv "loc_a=MiXeD"
set_status=failure
putenv "loc_b=value=equals"
getenv "LOC_A" a
getenv "LOC_B" b
putenv "loc_a=replaced"
getenv "LOC_A" replaced
putenv "LOC_A"
bad_status=failure
getenv "LOC_A" after_bad
putenv "LOC_A="
getenv "LOC_A" removed
putenv "=EmptyValue"
getenv "" empty_name
putenv "="
strcmp "A" "B"
getenv "LOC_MISSING" missing
get_status=failure
putenv "LOC_B="
endproc
''',
    'LOCAL': '''string local_value,local_source,param_value,param_source,register_value,register_source,alias
proc main
call local_worker
call param_worker with "loc_p=MiXeD" "OLD"
s0="loc_r=MiXeD"
putenv s0
strcpy register_source s0
getenv "loc_r" s1
strcpy register_value s1
alias="loc_parent"
getenv alias alias
putenv "LOC_R="
endproc
proc local_worker
string assignment="loc_c=MiXeD",result
putenv assignment
getenv "loc_c" result
strcpy local_value result
strcpy local_source assignment
putenv "LOC_C="
endproc
proc param_worker
strparm assignment
strparm result
putenv assignment
getenv "loc_p" result
strcpy param_value result
strcpy param_source assignment
putenv "LOC_P="
endproc
''',
    'SIX': '''string value
proc main
''' + ''.join(f'fopen {i} "STREAM.BIN" "rb"\n' for i in range(6)) + '''putenv "LOC_A=one"
getenv "loc_a" value
putenv "LOC_A="
endproc
''',
    'CHAIN1': '''proc main
putenv "LOC_CHAIN=first"
execute "CHAIN2"
endproc
''',
    'CHAIN2': '''string before,after
proc main
getenv "loc_chain" before
putenv "LOC_CHAIN=second"
getenv "loc_chain" after
putenv "LOC_CHAIN="
endproc
''',
    'LONG': '''string value
proc main
value="KEEP"
getenv "LOC_LONG" value
endproc
''',
    'ABORT': '''integer zero,result
proc main
putenv "LOC_ABORT=kept"
result=1/zero
endproc
''',
    'BUDGET': '''proc main
putenv "LOC_BUDGET=kept"
while 1
endwhile
endproc
''',
    'CLISRC': '''string value
proc main
getenv "loc_parent" value
strcmp value "MiXeD"
if failure
exit
endif
putenv "LOC_CLI=MiXeD"
getenv "loc_cli" value
strcmp value "MIXED"
if success
message "ENVIRONMENT READY"
endif
endproc
''',
}
CASES = [('CONTROL', 0), ('CHECKENV', 0), ('ROUND', 0), ('LOCAL', 0), ('SIX', 0),
         ('CHAIN1', 0), ('LONG', 7), ('ABORT', 11), ('BUDGET', 6),
         ('GTRUNC', 5), ('GBAD', 7), ('PTRUNC', 5), ('PBAD', 7)]

C = base.C.split('static void run(')[0] + r'''
#include "environment_runtime.h"
#include <process.h>
#include <stdlib.h>
static char **original_environment;
static const char *value(const char *name){const char *p=getenv(name);return p?p:"";}
static void run(const char *name,unsigned expected){
 unsigned result,flags=cpu_flags();current=name;++cases;
 {void (__interrupt __far *vector)(void)=_dos_getvect(0);
 result=aspect_runtime_run(name,!strcmp(name,"BUDGET.ASX")?20:2000);
 ck(result==expected);ck(_dos_getvect(0)==vector);}
 ck((cpu_flags()&0x600)==(flags&0x600));
 ck(!runtime_script_file_live&&!runtime_live&&!runtime_find_live&&!runtime_file.handle&&!runtime_abi_bad);
 if(!strcmp(name,"CONTROL.ASX")){
  ck(runtime_integer_b[0]==0&&runtime_integer_b[1]==0);
#ifdef ENVIRONMENT_UNOWNED_CONTROL
  ck(!strcmp((char *)runtime_string_snapshot[0],""));ck(!strcmp((char *)runtime_string_snapshot[1],"TWO"));
#else
  ck(!strcmp((char *)runtime_string_snapshot[0],"ONE"));ck(!strcmp((char *)runtime_string_snapshot[1],"TWO"));
  ck(runtime_environment_owned_entries==2);
  ck(spawnl(P_WAIT,"ENVCHECK.EXE","ENVCHECK",(char *)0)==0);
#endif
 }else if(!strcmp(name,"CHECKENV.ASX")){
  ck(!strcmp((char *)runtime_string_snapshot[0],"ONE"));ck(!strcmp((char *)runtime_string_snapshot[1],"TWO"));
 }else if(!strcmp(name,"ROUND.ASX")){
  static const char *expected[]={"MiXeD","MIXED","VALUE=EQUALS","REPLACED","REPLACED","","EMPTYVALUE",""};unsigned i;
  for(i=0;i<8;++i)ck(!strcmp((char *)runtime_string_snapshot[i],expected[i]));
  ck(runtime_integer_b[0]==0&&runtime_integer_b[1]==65535U&&runtime_integer_b[2]==65535U);
 }else if(!strcmp(name,"LOCAL.ASX")){
  static const char *expected[]={"MIXED","loc_c=MiXeD","MIXED","loc_p=MiXeD","MIXED","loc_r=MiXeD","MiXeD"};unsigned i;
  for(i=0;i<7;++i)ck(!strcmp((char *)runtime_string_snapshot[i],expected[i]));
 }else if(!strcmp(name,"SIX.ASX")){
  ck(!strcmp((char *)runtime_string_snapshot[0],"ONE"));ck(runtime_script_file_peak==6&&runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
 }else if(!strcmp(name,"CHAIN1.ASX")){
  ck(!strcmp((char *)runtime_string_snapshot[0],"FIRST"));ck(!strcmp((char *)runtime_string_snapshot[1],"SECOND"));ck(runtime_cleanup_count==2);
 }else if(!strcmp(name,"LONG.ASX")){
  ck(runtime_native_error_code==3);ck(!strcmp((char *)runtime_string_snapshot[0],"KEEP"));
 }else if(!strcmp(name,"ABORT.ASX")){
  ck(!strcmp(value("LOC_ABORT"),"KEPT"));ck(runtime_environment_put("LOC_ABORT=")==0);
 }else if(!strcmp(name,"BUDGET.ASX")){
  ck(!strcmp(value("LOC_BUDGET"),"KEPT"));ck(runtime_environment_put("LOC_BUDGET=")==0);
 }
#ifndef ENVIRONMENT_UNOWNED_CONTROL
 if(strcmp(name,"CONTROL.ASX"))ck(runtime_environment_owned_entries==0);
#endif
 printf("CASE %s error%u owned%u\n",name,result,runtime_environment_owned_entries);
}
static void faults(void){
 unsigned i,result;current="allocation faults";
 for(i=0;i<4;++i){
  runtime_environment_release();ck(environ==original_environment);
  runtime_environment_alloc_calls=0;runtime_environment_fail_after=i;
  result=runtime_environment_put("LOC_FAULT=VALUE");
  ck((result==0)==(i==3));ck(runtime_environment_owned_entries==(i==3));
  ck(!strcmp(value("LOC_FAULT"),i==3?"VALUE":""));
  runtime_environment_release();ck(environ==original_environment&&!runtime_environment_owned_entries&&!runtime_environment_initialized);
 }
 runtime_environment_fail_after=65535U;
 ck(runtime_environment_put("LOC_A=ONE")==0);ck(runtime_environment_put("LOC_B=TWO")==0);
 runtime_environment_alloc_calls=0;runtime_environment_fail_after=0;
 ck(runtime_environment_put("LOC_A=")==0);ck(!strcmp(value("LOC_A"),""));ck(!strcmp(value("LOC_B"),"TWO"));ck(runtime_environment_owned_entries==1);
 runtime_environment_fail_after=65535U;runtime_environment_release();
}
static void __watcall exit_verify(void){
 FILE *f=fopen("EXIT.OK","wb");if(!f)return;
 if(environ==original_environment&&!runtime_environment_owned_entries&&!runtime_environment_initialized)fputs("RESTORED",f);
 fclose(f);
}
int main(void){unsigned cycle,far_count=0,far_after_count=0,near_count,near_after_count,i;
 original_environment=environ;
#if defined(ENVIRONMENT_EXIT_CHILD)
 ck(atexit(exit_verify)==0);ck(runtime_environment_put("LOC_EXIT=OWNED")==0);return failures?1:0;
#elif defined(ENVIRONMENT_UNOWNED_CONTROL)
 ck(runtime_environment_prepare()==0);run("CONTROL.ASX",0);runtime_environment_release();
 ck(environ==original_environment);printf("NATIVE_ENV_CONTROL %u checks %u failures first-value=missing second=TWO\n",checks,failures);return failures?1:0;
#else
 faults();ck(spawnl(P_WAIT,"ENVEXIT.EXE","ENVEXIT",(char *)0)==0);
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    out = ROOT / 'build/aspect-environment-dos' / args.label
    out.mkdir(parents=True, exist_ok=False)
    stage = out / 'drive'
    stage.mkdir()
    binary, compiler = ROOT / 'build/aspect-runner/ASPECT.EXE', ROOT / 'build/aspect-compiler-dos/ASPCOMP.EXE'
    before = {str(p.relative_to(ROOT)): sha(p) for p in (binary, compiler, Path(__file__))}
    for path in (binary, compiler):
        shutil.copyfile(path, stage / path.name)
    for name, source in SOURCES.items():
        compile_source(source)
        (stage / (name + '.ASP')).write_bytes(source.replace('\n', '\r\n').encode('cp437'))
    for prefix, command in [('G', 'getenv "LOC_PARENT" value'), ('P', 'putenv value')]:
        valid = compile_source(f'string value\nproc main\n{command}\nendproc\n')
        assert valid[-3:] == b'\x8c\x00\x94'
        (stage / (prefix + 'TRUNC.ASX')).write_bytes(valid[:-3])
        (stage / (prefix + 'BAD.ASX')).write_bytes(valid[:-3] + b'\xff\x00\x94')
    (stage / 'STREAM.BIN').write_bytes(b'unchanged-environment-stream')
    calls = ''.join(f' run("{name}.ASX",{error});\n' for name, error in CASES)
    program = C + calls + r''' runtime_environment_release();current="baseline";
 ck(environ==original_environment);ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<30;++cycle){
''' + calls + r''' }
 runtime_environment_release();current="final";ck(environ==original_environment);
 jft(jft_after);ck(!memcmp(jft_before,jft_after,20));ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("ENV_VM %u cases %u checks %u failures farheap%u nearheap%u JFT-preserved\n",cases,checks,failures,far_count,near_count);return failures?1:0;
#endif
}
'''
    (out / 'harness.c').write_text(program)
    cs = ['runtime.c', 'environment_runtime.c', 'script_file_runtime.c', 'file_info_runtime.c', 'file_times_runtime.c', 'enumeration_runtime.c', 'file_io.c', 'script_path.c', 'serial_runtime.c', 'receive_runtime.c', 'directory_runtime.c', 'when_runtime.c', 'set_runtime.c', 'find_runtime.c']
    for name, macro, native in [('ENVVM', None, False), ('NATIVE', 'ENVIRONMENT_UNOWNED_CONTROL', True), ('ENVEXIT', 'ENVIRONMENT_EXIT_CHILD', False)]:
        objects = [str(ROOT / 'build/aspect-environment/environment_unowned.obj') if native and n == 'environment' else str(COMPONENT / (n + '.obj')) for n, _, _ in ASM]
        subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k8192', '-dASPECT_RUNTIME_DIAGNOSTIC',
                        *(['-d' + macro, '-wcd=202'] if macro else ['-wcd=202']),
                        '-i=' + str(ROOT / 'src/aspect'), '-i=' + str(ROOT / 'standalone'), '-fm=' + str(out / (name + '.map')), '-fe=' + str(stage / (name + '.EXE')),
                        str(out / 'harness.c'), str(ROOT / 'standalone/compiler_heap_snapshot.c'), *[str(ROOT / 'src/aspect' / n) for n in cs], *objects], cwd=out, check=True)
    child = '#include <stdlib.h>\n#include <string.h>\nint main(void){const char *a=getenv("LOC_A"),*b=getenv("LOC_B");return !a||!b||strcmp(a,"ONE")||strcmp(b,"TWO");}\n'
    (out / 'child.c').write_text(child)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-fe=' + str(stage / 'ENVCHECK.EXE'), str(out / 'child.c')], cwd=out, check=True)
    batch = ['@echo off', 'SET LOC_PARENT=MiXeD', 'SET LOC_LONG=' + 'X' * 81]
    for name in SOURCES:
        if name != 'CLISRC':
            batch += [f'ASPCOMP {name}.ASP >{name}.CMP', 'if errorlevel 1 goto failed']
    batch += ['ASPECT CLISRC.ASP >CLI.LOG', 'if errorlevel 1 goto failed', 'NATIVE >NATIVE.TXT', 'if errorlevel 1 goto failed', 'ENVVM >RESULT.TXT', 'if errorlevel 1 goto failed', 'echo PASS>PASS.TXT', 'goto done', ':failed', 'echo FAIL>FAIL.TXT', ':done', 'exit']
    (stage / 'RUN.BAT').write_text('\n'.join(batch) + '\n')
    (out / 'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{stage}"\nc:\ncall RUN.BAT\nexit\n')
    with (out / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')], cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'), stdout=log, stderr=log, check=True, timeout=120)
    output = (stage / 'RESULT.TXT').read_text() if (stage / 'RESULT.TXT').exists() else 'Inspect compiler/CLI/native logs'
    assert (stage / 'PASS.TXT').exists() and not (stage / 'FAIL.TXT').exists(), output
    summary = re.search(r'^ENV_VM (\d+) cases (\d+) checks 0 failures farheap(\d+) nearheap(\d+) JFT-preserved$', output, re.M)
    assert summary, output
    native = (stage / 'NATIVE.TXT').read_text()
    assert re.search(r'NATIVE_ENV_CONTROL \d+ checks 0 failures first-value=missing second=TWO', native)
    for name, source in SOURCES.items():
        assert (stage / (name + '.ASX')).read_bytes() == compile_source(source), name
    assert b'ENVIRONMENT READY' in (stage / 'CLI.LOG').read_bytes()
    assert (stage / 'EXIT.OK').read_bytes() == b'RESTORED'
    assert (stage / 'STREAM.BIN').read_bytes() == b'unchanged-environment-stream'
    assert before == {p: sha(ROOT / p) for p in before}
    result = dict(passed=True, cases=int(summary[1]), assertions=int(summary[2]), same_process_rounds=31,
                  DOS_summary=summary[0], native_control_summary=native.strip().splitlines()[-1],
                  native_control_sha256=sha(stage / 'NATIVE.EXE'), native_result_sha256=sha(stage / 'NATIVE.TXT'),
                  native_object_sha256=sha(ROOT / 'build/aspect-environment/environment_unowned.obj'),
                  runtime_object_sha256=sha(COMPONENT / 'environment.obj'),
                  exit_child_sha256=sha(stage / 'ENVEXIT.EXE'), exit_result_sha256=sha(stage / 'EXIT.OK'),
                  inheritance_child_sha256=sha(stage / 'ENVCHECK.EXE'),
                  runner_sha256=sha(binary), compiler_sha256=sha(compiler), checker_sha256=sha(Path(__file__)),
                  reused_harness_sha256=sha(Path(base.__file__)), harness_sha256=sha(out / 'harness.c'), result_sha256=sha(stage / 'RESULT.TXT'),
                  fixtures=SOURCES, original_inputs=[],
                  scope='Actual8086 DOS source compiler/VM/CLI, native CRT with owned near assignment/vector adapter. Inherited values, full-assignment uppercase, case-sensitive lookup, empty names/deletion/malformed inputs, persistence across invocations/EXECUTE, standard DOS child inheritance and automatic exit restore. Native command control reproduces reused-buffer loss. Local/parameter/register/alias destinations and immutable inputs, six streams, long inherited value typed error, post-mutation divide/budget exits, malformed operands, admitted allocation faults including ignored shrink failure, restored heaps/JFT/INT0/FLAGS/ABI. Process environment owner is deliberately distinct from per-script cleanup; no physical/whole-application claim.')
    (out / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['DOS_summary'])
    print(result['native_control_summary'])


if __name__ == '__main__':
    main()
