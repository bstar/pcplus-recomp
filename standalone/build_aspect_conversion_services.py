#!/usr/bin/env python3
"""Build exact native integer ASCII CRT services, no original build inputs."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-conversion-services'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('atoi',0x984e,0x9851,'fe88359c4bc376749fb2129125e052ae5091dfe2960b5be0d32a16447e6185a4'),('atol',0x9b32,0x9b35,'1c589aae5fb0b0e0c07c611c1d1b3569eefef70cdfe6b9d8921fbfb50f6f0cf9'),('itoa',0x8e6c,0x8e87,'43983fe093078241e840dc0c2f6d7b31d7cd82a37eeff9063e0d036e6f133c33'),('ltoa',0x9ae8,0x9af2,'f340a7c35109b43a60993b8c623439c1a14c6bcbe31c18db0bd31e570f9d0400'),('format_long',0xa5e8,0xa647,'aee8e26adbdc63381dbfee990f1087b8d98eed83783f635169093763b6e45623'),('parse',0xa7ce,0xa822,'ca547c2d88206de485e20f717617be4af319036d63c65a0c2c54c1227719f612'),('strcspn',0x9b36,0x9b90,'e31a0c9b0a1618e533bbcc9b54effe7dfec551bba1579f9edccbf261732979e2')]
ASM=r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _conversion_call
extern aspect_conversion_atoi,aspect_conversion_atol,aspect_conversion_itoa,aspect_conversion_ltoa,aspect_conversion_strcspn
extern _result_high
_conversion_call:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 cld
 mov bx,[bp+4]
 shl bx,1
 call word[cs:operations+bx]
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
operations: dw atoi,atol,itoa,ltoa,span
atoi:
 push word[bp+6]
 call aspect_conversion_atoi
 add sp,2
 mov [_result_high],dx
 ret
atol:
 push word[bp+6]
 call aspect_conversion_atol
 add sp,2
 mov [_result_high],dx
 ret
itoa:
 push word[bp+10]
 push word[bp+8]
 push word[bp+6]
 call aspect_conversion_itoa
 add sp,6
 ret
ltoa:
 push word[bp+12]
 push word[bp+10]
 push word[bp+8]
 push word[bp+6]
 call aspect_conversion_ltoa
 add sp,8
 ret
span:
 push word[bp+8]
 push word[bp+6]
 call aspect_conversion_strcspn
 add sp,4
 ret
SEGMENT _DATA public class=DATA use16
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
GROUP DGROUP _DATA _BSS STACK
'''
C=r'''
#include <stdio.h>
#include <string.h>
unsigned __cdecl conversion_call(unsigned op,unsigned a,unsigned b,unsigned c,unsigned d);
unsigned result_high,vectors,failures;unsigned long assertions;
unsigned char source[512],reject[256],buffer[100];
static void ck(unsigned y){++assertions;if(!y)++failures;}
static unsigned long parsed(const unsigned char *s)
{unsigned minus;unsigned long v=0;while(*s==' '||*s==9)++s;minus=*s=='-';if(*s=='-'||*s=='+')++s;while(*s>='0'&&*s<='9')v=v*10+(*s++-'0');return minus?0UL-v:v;}
static void format(unsigned long v,unsigned radix,unsigned char *out)
{unsigned char temp[40];unsigned i=0,j=0;unsigned rem;if(radix==10 && (v&0x80000000UL)){out[j++]='-';v=0UL-v;}do{rem=(unsigned)(v%radix);temp[i++]=(unsigned char)(rem<10?rem+'0':rem-10+'a');v/=radix;}while(v);while(i)out[j++]=temp[--i];out[j]=0;}
unsigned __cdecl conversions_dos_test(void)
{
 static const char *strings[]={"","0","-0","+","-","1","-1","\t +00123suffix","\n12","\r12","\v12","\f12","32767","32768","65535","65536","-32768","-32769","2147483647","2147483648","-2147483648","4294967295","4294967296","4294967297","-4294967295","18446744073709551615","--1","-+1"," +\t12","0x10","1e3","1.5","junk"};
 static const unsigned long values[]={0UL,1UL,9UL,10UL,35UL,255UL,32767UL,32768UL,65535UL,65536UL,0x7fffffffUL,0x80000000UL,0xffffffffUL};
 unsigned i,j,k,op,radix,r,n;unsigned long v,w;unsigned char expected[40];
 vectors=failures=0;assertions=0;
 for(i=0;i<sizeof(strings)/sizeof(strings[0]);++i)for(op=0;op<2;++op){
  strcpy((char*)source,strings[i]);w=parsed(source);r=conversion_call(op,(unsigned)source,0,0,0);v=((unsigned long)result_high<<16)|r;ck(v==w);++vectors;
 }
 for(op=2;op<=3;++op)for(i=0;i<13;++i)for(radix=2;radix<=36;++radix){
  v=values[i];w=op==2?(unsigned)v:v;if(op==2 && radix==10)w=(unsigned long)(long)(int)(unsigned)v;format(w,radix,expected);memset(buffer,0xa5,sizeof(buffer));
  if(op==2)r=conversion_call(op,(unsigned)v,(unsigned)(buffer+4),radix,0);else r=conversion_call(op,(unsigned)v,(unsigned)(v>>16),(unsigned)(buffer+4),radix);
  n=strlen((char*)expected);ck(r==(unsigned)(buffer+4));ck(!memcmp(buffer+4,expected,n+1));for(j=0;j<4;++j)ck(buffer[j]==0xa5);ck(buffer[n+5]==0xa5);++vectors;
 }
 for(i=1;i<256;++i){source[0]='A';source[1]=(unsigned char)i;source[2]='B';source[3]=0;reject[0]=(unsigned char)i;reject[1]=0;n=i=='A'?0:1;ck(conversion_call(4,(unsigned)source,(unsigned)reject,0,0)==n);++vectors;}
 strcpy((char*)source,"near CRT");reject[0]=0;ck(conversion_call(4,(unsigned)source,(unsigned)reject,0,0)==8);++vectors;
 source[0]=0;strcpy((char*)reject,"anything");ck(conversion_call(4,(unsigned)source,(unsigned)reject,0,0)==0);++vectors;
 for(k=0;k<255;++k)reject[k]=(unsigned char)(k+1);reject[255]=0;source[0]=255;source[1]=0;ck(conversion_call(4,(unsigned)source,(unsigned)reject,0,0)==0);++vectors;
 return failures;
}
int main(void){unsigned r=conversions_dos_test();printf("CONVERSION %s vectors=%u assertions=%lu failures=%u\n",r?"FAIL":"PASS",vectors,assertions,failures);return r?1:0;}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 OUT.mkdir(parents=True,exist_ok=True);module=ROOT/'src/aspect/conversion_services.asm';units=[]
 for number,(name,start,end,digest)in enumerate(UNITS,1):
  out=OUT/(name+'.bin');subprocess.run(['nasm','-fbin','-DASPECT_CONVERSION_SERVICES_FLAT',f'-DASPECT_CONVERSION_SERVICES_UNIT={number}','-I',str(ROOT/'reconstruction/uart')+'/',str(module),'-o',str(out)],check=True)
  assert len(out.read_bytes())==end-start and sha(out)==digest,(name,sha(out));units.append(dict(name=name,start=start,end=end,bytes=end-start,sha256=digest,flat=out.name))
 (OUT/'host.asm').write_text(ASM);(OUT/'host.c').write_text(C);objects=[]
 for i,p in enumerate((module,OUT/'host.asm')):
  obj=OUT/f'{i:02}.obj';objects.append(str(obj));subprocess.run(['nasm','-fobj','-I',str(ROOT/'reconstruction/uart')+'/',str(p),'-o',str(obj)],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=conversion.map','-fe=CONVERT.EXE',str(OUT/'host.c'),*objects],cwd=OUT,check=True)
 result=dict(binary_sha256=sha(OUT/'CONVERT.EXE'),exact_bytes=312,units=units,original_inputs=[],sources={str(p.relative_to(ROOT)):sha(p)for p in(module,ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve())},generated={n:sha(OUT/n)for n in('host.asm','host.c')},scope='Exact native atoi/atol shared32bit parser, signed/unsigned integer formatting and strcspn stack bitmap. C selfcheck supplies independent integer oracles only; no product service boundaries substituted.')
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':print(json.dumps(build(),indent=2))
