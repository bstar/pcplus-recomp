#!/usr/bin/env python3
"""Run the maintained compiler corpus and line-limit expressions with checked16KB stacks.

The candidate CLI retains24KB. A deliberate checked-stack overflow separately
proves that the test toolchain's guard is live; no grammar limit is reduced.
"""
import argparse,hashlib,json,os,re,shutil
from pathlib import Path
import check_aspect_compiler_dos as corpus

ROOT=corpus.ROOT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PROBE=r'''
#include <stdio.h>
static volatile unsigned calls;
static unsigned recurse(unsigned value){
 volatile unsigned char space[128];unsigned result;
 space[value&127]=(unsigned char)value;++calls;
 result=value<4096?recurse(value+1):value;
 return result+space[value&127];
}
int main(void){
 FILE *f=fopen("STKENTER.OK","wb");if(!f)return 2;fputs("ENTER",f);fclose(f);
 if(!freopen("STKFAIL.ERR","wb",stderr))return 2;
 recurse(0);f=fopen("STKRET.OK","wb");if(f){fputs("RETURN",f);fclose(f);}return 0;
}
'''
VIDEO=r'''
bits 16
cpu 8086
org 100h
push cs
pop ds
mov ax,0xb800
mov es,ax
xor si,si
mov di,buffer
mov cx,2000
.copy:
mov ax,[es:si]
mov [di],ax
add si,2
add di,2
loop .copy
mov dx,name
xor cx,cx
mov ah,0x3c
int 0x21
jc .bad
mov bx,ax
mov dx,buffer
mov cx,4000
mov ah,0x40
int 0x21
jc .close_bad
cmp ax,4000
jne .close_bad
mov ah,0x3e
int 0x21
jc .bad
mov ax,0x4c00
int 0x21
.close_bad:
mov ah,0x3e
int 0x21
.bad:
mov ax,0x4c01
int 0x21
name: db 'STKVIDEO.BIN',0
buffer: times 4000 db 0
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler-dir',type=Path,default=ROOT/'build/aspect-compiler-dos')
    parser.add_argument('--compiler-source-root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    directory=a.compiler_dir.resolve();source_root=a.compiler_source_root.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    manifest=json.loads((directory/'manifest.json').read_text());binary=directory/'ASPCOMP.EXE'
    assert manifest['original_inputs']==[] and manifest['binary_sha256']==sha(binary)
    for name,digest in manifest['sources'].items():
        assert sha(source_root/name)==digest,name
        if Path(name).suffix in ('.c','.h'):assert sha(ROOT/name)==digest,name
    listing=(directory/'ASPCOMP.map').read_text()
    stack=re.search(r'^STACK\s+STACK\s+DGROUP\s+\S+\s+([0-9a-f]+)',listing,re.M|re.I)
    assert stack and int(stack[1],16)==24576
    for name in ('ASPCOMP.EXE','ASPCOMP.map','manifest.json'):shutil.copy2(directory/name,out/name)
    limit=int(re.search(r'#define ASPECT_COMPILER_LINE_MAX (\d+)',(ROOT/'src/aspect/compiler_lexer.h').read_text())[1])
    deep={};depth=(limit-3)//2
    for kind in ('integer','long','float'):
        expressions={
            'parentheses':'i='+('('*depth)+'i'+(')'*depth),
            'prefix':'i='+('- '*depth)+'i',
            'left-add':'i='+('i+'*depth)+'i',
            'right-assign':('i='*((limit-1)//2))+'i',
            'logical-and':'i='+('i&&'*((limit-3)//3))+'i',
            'logical-or':'i='+('i||'*((limit-3)//3))+'i',
        }
        for name,line in expressions.items():
            assert len(line)<=limit
            source=(kind+' i\nproc main\n'+line+'\nendproc\n').encode()
            # These stress cases must remain accepted, not merely be rejected
            # before reaching deep parsing/type resolution/emission.
            expected=corpus.compiler.compile_source(source.decode())
            assert expected
            key='stack-'+kind+'-'+name;corpus.EDGES[key]=source
            deep[key]=dict(line_bytes=len(line),source_sha256=hashlib.sha256(source).hexdigest())
    corpus.OUT=out;corpus.build=lambda:None
    original_run=corpus.subprocess.run;guarded=[]
    def run(arguments,*args,**kwargs):
        arguments=list(arguments)
        if Path(str(arguments[0])).name=='wcl':
            arguments=[x for x in arguments if x!='-s']
            if '-k32768' in arguments:
                arguments[arguments.index('-k32768')]='-k16384';guarded.append(arguments)
        if Path(str(arguments[0])).name=='dosbox-x':
            folder=out/'tests';probe=folder/'stack_probe.c';probe.write_text(PROBE)
            original_run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-w4','-we','-k2048',
                '-fe=STACKCHK.EXE',str(probe)],cwd=folder,check=True)
            video=folder/'stack_video.asm';video.write_text(VIDEO)
            original_run(['nasm','-fbin',str(video),'-o',str(folder/'STKVID.COM')],check=True)
            config=folder/'dosbox.conf';text=config.read_text()
            assert text.count('PROGRAM >RUN.TXT')==1
            text=text.replace('PROGRAM >RUN.TXT','STACKCHK\nif not errorlevel 1 goto failed\nSTKVID\nif errorlevel 1 goto failed\nif not exist STKENTER.OK goto failed\nif exist STKRET.OK goto failed\nPROGRAM >RUN.TXT')
            config.write_text(text)
        return original_run(arguments,*args,**kwargs)
    corpus.subprocess.run=run
    try:corpus.main()
    finally:corpus.subprocess.run=original_run
    report=json.loads((out/'checks.json').read_text());assert report['passed'] and len(guarded)==3
    # This pinned CRT writes its fatal message to the console, bypassing the
    # reopened stderr stream. Observe the real video before PROGRAM runs.
    video=(out/'tests/STKVIDEO.BIN').read_bytes();assert len(video)==4000
    assert b'stack overflow' in video[::2].lower(),video[::2]
    assert (out/'tests/STKENTER.OK').read_bytes()==b'ENTER' and not (out/'tests/STKRET.OK').exists()
    # Exercise the CLI's own automatic workspace, not only the heap-context API
    # in PROGRAM. Build all CLI frames with the pinned CRT stack checks enabled.
    cli=out/'checked-cli';cli.mkdir()
    command=['wcl','-q','-bt=dos','-0','-ml','-fpc','-ecc','-w4','-we','-k24576',
             '-fm=ASPCOMP.map','-fe=ASPCOMP.EXE',
             *[str(ROOT/'src/aspect'/(name+'.c'))for name in corpus.MODULES],
             str(ROOT/'src/aspect/compiler_main.c')]
    original_run(command,cwd=cli,check=True)
    expected={};commands=[]
    for index,key in enumerate(deep):
        stem='D%07d'%index;source=corpus.EDGES[key]
        (cli/(stem+'.ASP')).write_bytes(source)
        expected[stem]=corpus.compiler.compile_source(source.decode())
        commands += [f'ASPCOMP {stem}.ASP >{stem}.TXT','if errorlevel 1 goto failed']
    small=[x.replace('-k24576','-k2048').replace('-fe=ASPCOMP.EXE','-fe=STKCLI.EXE')
           .replace('-fm=ASPCOMP.map','-fm=STKCLI.map')for x in command]
    original_run(small,cwd=cli,check=True)
    shutil.copyfile(out/'tests/STKVID.COM',cli/'STKVID.COM')
    commands += ['STKCLI D0000000.ASP OVR.ASX >OVERFLOW.TXT',
                 'if not errorlevel 1 goto failed','STKVID',
                 'echo PASS>PASS.TXT','exit',':failed','echo FAIL>FAIL.TXT','exit']
    config=cli/'dosbox.conf'
    config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n'
                      '[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(cli)+'"\nc:\n'+'\n'.join(commands)+'\n')
    with (cli/'dosbox.log').open('w')as log:
        completed=original_run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],
            cwd=cli,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),
            stdout=log,stderr=log,timeout=45)
    assert completed.returncode==0 and (cli/'PASS.TXT').exists() and not (cli/'FAIL.TXT').exists()
    assert all((cli/(stem+'.ASX')).read_bytes()==raw for stem,raw in expected.items())
    assert b'stack overflow' in (cli/'STKVIDEO.BIN').read_bytes()[::2].lower()
    assert not (cli/'OVR.ASX').exists()
    result=dict(passed=True,candidate_CLI_stack_bytes=24576,checked_API_stack_bytes=16384,
        checked_CLI_stack_bytes=24576,checked_CLI_cases=len(expected),
        checked_CLI_sha256=sha(cli/'ASPCOMP.EXE'),checked_CLI_command=command,
        checked_CLI_overflow_sha256=sha(cli/'STKCLI.EXE'),
        deliberate_overflow_stack_bytes=2048,guarded_compile_commands=guarded,depth_cases=deep,
        corpus_cases=report['case_count'],accepted=report['accepted'],rejected=report['rejected'],
        compiler_sha256=sha(binary),checker_sha256=sha(Path(__file__)),reused_corpus_checker_sha256=sha(Path(corpus.__file__)),
        scope=__doc__+' Checked16KB parser/emitter/API corpus plus a24KB candidate CLI. This constrains the existing253-byte line/node grammar and selected DOS toolchain; future grammar changes and physical systems require revalidation.')
    (out/'stack-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,cases=result['corpus_cases'],deep_cases=len(deep))))

if __name__=='__main__':main()
