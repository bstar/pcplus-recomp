#!/usr/bin/env python3
"""Compare compact internal formatters with CRT printf on host and actual DOS8086."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "runtime_format.h"
#include "runner_error.h"
static unsigned cases,failures;
static const char *errors[]={"success","cannot open script","invalid script header",
 "unsupported command or service","floating-point service unavailable","file or output error",
 "instruction budget exhausted","invalid operand","out of memory","script stack overflow",
 "invalid runtime state","division by zero","CPU arithmetic fault","cancelled","serial service error"};
static void ck(unsigned ok){if(!ok)++failures;}
static void compare(const char *format,...)
{
 unsigned char guarded[224];char expected[192];int n,want;unsigned i;va_list a,b;
 memset(guarded,0xa5,sizeof(guarded));memset(expected,0,sizeof(expected));
 va_start(a,format);n=aspect_runtime_format((char *)guarded+16,format,a);va_end(a);
 va_start(b,format);want=vsprintf(expected,format,b);va_end(b);
 ck(n==want&&n>=0&&n<192);ck(!memcmp(guarded+16,expected,want+1));
 for(i=0;i<16;++i)ck(guarded[i]==0xa5);
 for(i=(unsigned)want+17;i<sizeof(guarded);++i)ck(guarded[i]==0xa5);
 ++cases;
}
static void error_case(unsigned result,unsigned opcode,unsigned steps,unsigned bits)
{
 char expected[192];unsigned char got[224];unsigned n,want,i,capacity;
 unsigned native=bits&1?65535U:0,serial=bits&2?12345U:0,pacing=bits&4?65535U:0;
 want=(unsigned)sprintf(expected,"ASPECT: %s (error %u, opcode %02X, step %u",
   result<15?errors[result]:"runtime error",result,opcode,steps);
 if(native)want+=(unsigned)sprintf(expected+want,", native %u",native);
 if(serial)want+=(unsigned)sprintf(expected+want,", serial %u",serial);
 if(pacing)want+=(unsigned)sprintf(expected+want,", pacing %u",pacing);
 expected[want++]=')';expected[want]=0;
 for(capacity=0;capacity<=192;capacity=capacity==0?1:capacity==1?7:capacity==7?192:193){
  memset(got,0xa5,sizeof(got));n=aspect_runner_error((char *)got+16,capacity,result,opcode,steps,native,serial,pacing);
  ck(n==want);if(capacity){i=want<capacity?want:capacity-1;ck(!memcmp(got+16,expected,i));ck(got[16+i]==0);}
  for(i=0;i<16;++i)ck(got[i]==0xa5);
  for(i=capacity+16;i<sizeof(got);++i)ck(got[i]==0xa5);
 }
 ++cases;
}
int main(void)
{
 unsigned i,j,k;unsigned long sizes[]={0UL,1UL,65535UL,65536UL,70001UL,2147483647UL,4294967295UL};
 const char *names[]={"","A","TWELVE12.ZIP","LONGER_THAN_12"};char guard[32];
 for(i=0;i<256;++i){
  compare("%d.%02d",(int)i,(int)(255-i));compare("%c:\\",(int)i);
  compare("%2u-%.2u-%.2u",i,i/2U,i/3U);compare("%.2u:%.2u",i/4U,i/5U);
 }
 compare("%d.%02d",-32767-1,-1);compare("%d.%02d",32767,32767);
 compare("%2u-%.2u-%.2u",65535U,65535U,65535U);
 for(i=0;i<4;++i)for(j=0;j<7;++j)for(k=0;k<32;++k){
  compare("%-12s  %6lu  %2u-%.2u-%.2u  %.2u:%.2u",names[i],sizes[j],k,k,k,k,k);
  compare("%-12s   <DIR>  %2u-%.2u-%.2u  %.2u:%.2u",names[i],k,k,k,k,k);
 }
 for(i=0;i<17;++i)for(j=0;j<8;++j)for(k=0;k<8;++k)
  error_case(i==16?65535U:i,j==7?65535U:j*37U,k==7?65535U:k*997U,k);
 memset(guard,0x5a,sizeof(guard));
 /* The adapter is deliberately private to six recovered format strings. */
 {va_list unused;memset(&unused,0,sizeof(unused));ck(aspect_runtime_format(guard,"%n",unused)==-1);}
 for(i=0;i<sizeof(guard);++i)ck(guard[i]==0x5a);
 printf("COMPACT_FORMAT %u cases %u failures\n",cases,failures);return failures?1:0;
}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 source=out/'format.c';source.write_text(HARNESS)
 subprocess.run(['cc','-std=c90','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src/aspect'),str(source),'-o',str(out/'format-host')],check=True)
 host=subprocess.check_output([str(out/'format-host')],text=True);assert '0 failures'in host
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k4096','-i='+str(ROOT/'src/aspect'),'-fm=FORMAT.map','-fe=FORMAT.EXE',str(source)],cwd=out,check=True)
 cfg='''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "'''+str(out)+'''"
c:
FORMAT > RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (out/'dosbox.conf').write_text(cfg)
 with(out/'dosbox.log').open('w')as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 dos=(out/'RESULT.TXT').read_text();assert dos.strip()==host.strip()and(out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists(),dos
 paths=[ROOT/'src/aspect/runtime_format.h',ROOT/'src/aspect/runner_error.h',Path(__file__)]
 result=dict(passed=True,host=host.strip(),DOS=dos.strip(),sources={str(p.relative_to(ROOT)):sha(p)for p in paths},
  artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()},original_inputs=[],scope=__doc__+' Exact return lengths, bytes, output guards and short-capacity diagnostics; long file sizes and signed16 extrema included. No general printf interface promised.')
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(dos.strip())
if __name__=='__main__':main()
