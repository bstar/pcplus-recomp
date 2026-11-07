#!/usr/bin/env python3
"""Compare ordinary and compact ALARM CLI path admission in actual DOS8086."""
import argparse,itertools,json,os,random,re,struct,subprocess
from pathlib import Path
from build_context_help import ROOT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    source=(ROOT/'src/aspect/runner.c').read_text()
    block=source[source.index('static unsigned folded('):source.index('static unsigned budget(')]
    (out/'paths.h').write_text(block)
    values={b'',b'C:',b'C:\\',b'normal.ASX',b'CON',b'con.ASP',b'D:\\LPT9.ASX',b'COM0.ASX',b'COM10.ASX'}
    for letters in itertools.product(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ',repeat=3):values.add(bytes(letters))
    for word in (b'CON',b'PRN',b'AUX',b'NUL',b'COM',b'LPT'):
        for letters in itertools.product(*[(c,c+32) for c in word]):
            base=bytes(letters)
            for pos in range(3):
                for byte in range(256):
                    changed=base[:pos]+bytes([byte])+base[pos+1:]
                    for root,suffix in itertools.product((b'',b'D:\\BIN\\'),(b'',b'.ASX')):values.add(root+changed+suffix)
            if word in (b'COM',b'LPT'):
                for byte in range(256):
                    for root,suffix in itertools.product((b'',b'D:\\BIN\\'),(b'',b'.ASX')):values.add(root+base+bytes([byte])+suffix)
    for n in range(513):
        values.add(b'A'*n)
        if n<=509:values.add(b'D:\\'+b'A'*n)
    rng=random.Random(0x414c4152)
    for _ in range(10000):values.add(bytes(rng.randrange(256) for _ in range(rng.randrange(130))))
    vectors=sorted(values);data=struct.pack('<I',len(vectors))+b''.join(struct.pack('<H',len(v))+v for v in vectors)
    (out/'PATHS.BIN').write_bytes(data)
    program=r'''
#include <stdio.h>
#include <string.h>
#define folded original_folded
#define path_ok original_path_ok
#include "paths.h"
#undef folded
#undef path_ok
#define ASPECT_ALARM_VM 1
#define folded compact_folded
#define path_ok compact_path_ok
#include "paths.h"
int main(void){
 FILE *f;unsigned size,a,b;unsigned long count,i,failures=0;char value[513];
 if(original_path_ok(0)||compact_path_ok(0))return 2;
 if(original_path_ok("CON")||compact_path_ok("CON")||!compact_path_ok("COM0.ASX")||compact_path_ok("LPT9.ASX"))return 3;
 f=fopen("PATHS.BIN","rb");if(!f||fread(&count,4,1,f)!=1)return 4;
 for(i=0;i<count;++i){
  if(fread(&size,2,1,f)!=1||size>512||fread(value,1,size,f)!=size)return 5;
  value[size]=0;a=original_path_ok(value);b=compact_path_ok(value);
  if(a!=b){if(failures<10)printf("MISMATCH %lu original%u compact%u\n",i,a,b);++failures;}
 }
 if(fgetc(f)!=EOF||fclose(f))return 6;
 printf("CLI_PATH %lu cases %lu failures\n",count,failures);return failures?1:0;
}
'''
    (out/'test.c').write_text(program)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-k4096','-fe=PATHS.EXE',str(out/'test.c')],cwd=out,check=True)
    (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nPATHS >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with(out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=90)
    text=(out/'RESULT.TXT').read_text();assert (out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists(),text
    assert re.fullmatch(r'CLI_PATH '+str(len(vectors))+r' cases 0 failures\s*',text),text
    result=dict(passed=True,cases=len(vectors),sources={n:sha(ROOT/n)for n in ('src/aspect/runner.c','standalone/test_runner_path_compact_dos.py','standalone/build_context_help.py')},artifacts={str(p.relative_to(out)):sha(p)for p in out.iterdir()if p.is_file()},original_inputs=[],scope=__doc__+' Both actual source branches, same optimized Watcom flags and16-bit unsigned/char behavior. All uppercase3-letter stems; case variants and each byte in reserved-name positions; every port suffix byte, rooted/dotted variants,0..512 lengths and fixed-seed byte strings including NUL. Does not change OS path resolution or claim arbitrary pointer safety.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text)


if __name__=='__main__':main()
