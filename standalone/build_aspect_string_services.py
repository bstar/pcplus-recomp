#!/usr/bin/env python3
"""Source-only exact ASPECT/CRT service diagnostic; generated numeric/address fixtures."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-string-services'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[
('strcmp',0x9476,0x94a1,0x1200,'45ac38cf728603e2a3b30bb4ea992beacca4e11bae5aa88fd6ed1fd36131eb33'),
('lower',0x9be8,0x9c06,0x1200,'dbe38e79a0d78e3ad4b8279fd547d719c1b311ec290b1c1f4ca297ce4c982295'),
('fill',0x9736,0x9763,0x1200,'1c23fb851d661af60c24b3dca83a45c6f7cb1b80220ca08cb086cbc5ce4c82ab'),
('byte_operand',0xdde3,0xddee,55728,'95052d3aff7f9bc0ec4bc26b671bc464cc93d68c46026b1b830335c5698b3609'),
('index_operand',0xde1c,0xde27,55728,'21f855061127c834f5079f1a3889a4bfb113d0b7cb2411b09da7c502d485c81f'),
('store_integer',0xde3a,0xde4d,55728,'dee3f1af38239aa5c1cdfa9a51c09030bc96280eef29dd310a0a099ad344ab78'),
('status',0xda0c,0xda10,55728,'327919a00dffc737a400d66154d1d9fb6452441dbb16d463a62539136809cec8'),
('success',0xda28,0xda32,55728,'b72088d091c1de77e63fcd44dac9661192acab52b95250aa7575c6e669b8c036')]
REUSED=[('program_strlen','reconstruction/program_exec/strlen.asm',0x8d18,0x8d33,'PROGRAM_EXEC_OMF'),('program_strncmp','reconstruction/program_exec/strncmp.asm',0x9c06,0x9c40,'PROGRAM_EXEC_OMF'),('directory_dial_append_original','reconstruction/directory_dial/append.asm',0x9852,0x9887,'DIRECTORY_DIAL_OMF'),('directory_dial_upper_original','reconstruction/directory_dial/uppercase.asm',0x9128,0x9146,'DIRECTORY_DIAL_OMF')]
ASM=r'''
BITS16
CPU8086
SEGMENT _TEXT public class=CODE use16
global _service_call
extern _model_return,_bounded_calls,_seen_min,_seen_max,_address_calls,_integer_dest
extern aspect_string_strcmp,aspect_string_lower,aspect_string_fill
extern aspect_string_byte_operand,aspect_string_index_operand,aspect_string_store_integer
extern aspect_string_status,aspect_string_success
extern program_strlen,program_strncmp,directory_dial_append_original,directory_dial_upper_original
_service_call:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 cld
 mov bx,[bp+4]
 shl bx,1
 call word [cs:operations+bx]
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
operations: dw compare,lower,fill,opbyte,index,store,status,success,length,ncompare,append,upper
compare:
 push word [bp+8]
 push word [bp+6]
 call aspect_string_strcmp
 add sp,4
 ret
lower:
 push word [bp+6]
 call aspect_string_lower
 add sp,2
 ret
fill:
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call aspect_string_fill
 add sp,6
 ret
opbyte: call aspect_string_byte_operand
 ret
index: call aspect_string_index_operand
 ret
store:
 push word [bp+6]
 call aspect_string_store_integer
 ret
status: call aspect_string_status
 ret
success: call aspect_string_success
 ret
length:
 push word [bp+6]
 call program_strlen
 add sp,2
 ret
ncompare:
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call program_strncmp
 add sp,6
 ret
append:
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call directory_dial_append_original
 add sp,6
 ret
upper:
 push word [bp+6]
 call directory_dial_upper_original
 add sp,2
 ret
global aspect_string_bounded_integer,aspect_expr_integer_address
aspect_string_bounded_integer:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [_seen_max],ax
 mov ax,[bp+6]
 mov [_seen_min],ax
 inc word [_bounded_calls]
 mov ax,[_model_return]
 pop bp
 ret4
aspect_expr_integer_address:
 inc word [_address_calls]
 mov ax,_integer_dest
 ret
SEGMENT _DATA public class=DATA use16
global aspect_string_compare_result,_comparison
aspect_string_compare_result:
_comparison: dw 0
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
GROUP DGROUP _DATA _BSS STACK
'''.replace('BITS16','BITS 16').replace('CPU8086','CPU 8086').replace(' ret4',' ret 4')
C=r'''
#include <stdio.h>
#include <string.h>
unsigned __cdecl service_call(unsigned op,unsigned a,unsigned b,unsigned c);
unsigned long assertions;unsigned failures,vectors;
unsigned model_return,bounded_calls,seen_min,seen_max,address_calls;
extern unsigned comparison;
unsigned integer_before,integer_dest,integer_after;
unsigned char fixture_buffer[384],fixture_left[64],fixture_right[64];
static void ck(unsigned yes){++assertions;if(!yes)++failures;}
static unsigned expected(const unsigned char *a,const unsigned char *b)
{while(*a==*b && *a){++a;++b;}return *a<*b?0xffff:*a>*b?1:0;}
unsigned __cdecl services_dos_test(void)
{
 unsigned i,j,k,v,count,alignment,result;unsigned char a,b;
 static const unsigned char values[]={0,1,0x1a,0x7f,0x80,0xfe,0xff};
 static const unsigned counts[]={0,1,2,3,7,8,15,16,31,32,79,80,127,128};
 assertions=failures=vectors=0;
 for(i=0;i<7;++i)for(j=0;j<7;++j){
  fixture_left[0]=values[i];fixture_left[1]=0;fixture_right[0]=values[j];fixture_right[1]=0;
  result=service_call(0,(unsigned)fixture_left,(unsigned)fixture_right,0);ck(result==expected(fixture_left,fixture_right));++vectors;
 }
 strcpy((char*)fixture_left,"equal");strcpy((char*)fixture_right,"equal");fixture_left[6]=0xff;fixture_right[6]=1;
 ck(service_call(0,(unsigned)fixture_left,(unsigned)fixture_right,0)==0);++vectors;
 strcpy((char*)fixture_right,"equalsuffix");ck(service_call(0,(unsigned)fixture_left,(unsigned)fixture_right,0)==0xffff);++vectors;
 ck(service_call(0,(unsigned)fixture_right,(unsigned)fixture_left,0)==1);++vectors;
 for(i=1;i<256;++i)fixture_buffer[i-1]=(unsigned char)i;fixture_buffer[255]=0;fixture_buffer[256]=0x5a;
 ck(service_call(1,(unsigned)fixture_buffer,0,0)==(unsigned)fixture_buffer);
 for(i=1;i<256;++i)ck(fixture_buffer[i-1]==(i>='A'&&i<='Z'?i+32:i));ck(!fixture_buffer[255]&&fixture_buffer[256]==0x5a);++vectors;
 for(v=0;v<7;++v)for(k=0;k<14;++k)for(alignment=0;alignment<2;++alignment){
  memset(fixture_buffer,0xa5,sizeof(fixture_buffer));count=counts[k];
  ck(service_call(2,(unsigned)fixture_buffer+8+alignment,values[v],count)==(unsigned)fixture_buffer+8+alignment);
  for(i=0;i<sizeof(fixture_buffer);++i)ck(fixture_buffer[i]==(i>=8+alignment && i<8+alignment+count?values[v]:0xa5));++vectors;
 }
 for(i=0;i<2;++i)for(j=0;j<7;++j){
  model_return=j==6?0xffff:j==5?256:j==4?255:j==3?80:j==2?79:j;
  bounded_calls=seen_min=seen_max=0;
  ck(service_call(3+i,0,0,0)==model_return && bounded_calls==1 && seen_min==0 && seen_max==(i?79:255));++vectors;
 }
 for(i=0;i<7;++i){
  v=i==6?0xffff:i==5?0x8000:i==4?0x7fff:values[i];integer_before=0xabcd;integer_dest=0;integer_after=0xdcba;address_calls=0;
  ck(service_call(5,v,0,0)==v && integer_dest==v && integer_before==0xabcd && integer_after==0xdcba && address_calls==1);++vectors;
  comparison=v;ck(service_call(6,0,0,0)==v);ck(service_call(7,0,0,0)==(v==0));++vectors;
 }
 strcpy((char*)fixture_left,"near");fixture_left[5]=0xff;ck(service_call(8,(unsigned)fixture_left,0,0)==4);++vectors;
 for(count=0;count<=5;++count){
  strcpy((char*)fixture_left,"A\200Z");strcpy((char*)fixture_right,"A\177Z");
  a=fixture_left[count<3?count:3];b=fixture_right[count<3?count:3];(void)a;(void)b;
  result=count<2?0:1;ck(service_call(9,(unsigned)fixture_left,(unsigned)fixture_right,count)==result);++vectors;
 }
 for(count=0;count<=5;++count){
  memset(fixture_buffer,0xa5,sizeof(fixture_buffer));strcpy((char*)fixture_buffer,"D");strcpy((char*)fixture_left,"abc");
  ck(service_call(10,(unsigned)fixture_buffer,(unsigned)fixture_left,count)==(unsigned)fixture_buffer);
  for(i=0;i<(count<3?count:3);++i)ck(fixture_buffer[i+1]=='a'+i);
  ck(fixture_buffer[(count<3?count:3)+1]==0 && fixture_buffer[(count<3?count:3)+2]==0xa5);++vectors;
 }
 for(i=1;i<256;++i)fixture_buffer[i-1]=(unsigned char)i;fixture_buffer[255]=0;
 ck(service_call(11,(unsigned)fixture_buffer,0,0)==(unsigned)fixture_buffer);
 for(i=1;i<256;++i)ck(fixture_buffer[i-1]==(i>='a'&&i<='z'?i-32:i));++vectors;
 return failures;
}
int main(void){unsigned r=services_dos_test();printf("SERVICES %s vectors=%u assertions=%lu failures=%u\n",r?"FAIL":"PASS",vectors,assertions,failures);return r?1:0;}
'''
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 OUT.mkdir(parents=True,exist_ok=True);module=ROOT/'src/aspect/string_services.asm';units=[]
 for number,(name,start,end,base,sha) in enumerate(UNITS,1):
  out=OUT/(name+'.bin');subprocess.run(['nasm','-fbin','-DASPECT_STRING_SERVICES_FLAT',f'-DASPECT_STRING_SERVICES_UNIT={number}','-I',str(ROOT/'reconstruction/uart')+'/',str(module),'-o',str(out)],check=True)
  assert len(out.read_bytes())==end-start and digest(out)==sha,(name,digest(out),sha)
  units.append(dict(name=name,start=start,end=end,file_base=base,bytes=end-start,sha256=sha,flat=out.name))
 reused_units=[]
 for name,path,start,end,_ in REUSED:
  out=OUT/(name+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/path),'-o',str(out)],check=True)
  assert len(out.read_bytes())==end-start
  reused_units.append(dict(name=name,start=start,end=end,file_base=0x1200,bytes=end-start,sha256=digest(out),flat=out.name))
 (OUT/'host.asm').write_text(ASM);(OUT/'host.c').write_text(C)
 sources=[module]+[ROOT/r[1]for r in REUSED];objects=[]
 for i,path in enumerate(sources+[OUT/'host.asm']):
  obj=OUT/f'{i:02}.obj';objects.append(str(obj));subprocess.run(['nasm','-fobj','-DPROGRAM_EXEC_OMF','-DDIRECTORY_DIAL_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=services.map','-fe=SERVICES.EXE',str(OUT/'host.c'),*objects],cwd=OUT,check=True)
 sourcepaths=sources+[ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
 result=dict(binary_sha256=digest(OUT/'SERVICES.EXE'),exact_new_bytes=173,reused_bytes=sum(e-s for _,_,s,e,_ in REUSED),units=units,reused_units=reused_units,sources={str(p.relative_to(ROOT)):digest(p)for p in sourcepaths},generated={'host.asm':digest(OUT/'host.asm'),'host.c':digest(OUT/'host.c')},original_inputs=[],scope='Exact native near CRT/service unit with modeled numeric-bound and integer-address callbacks only; no expression parser, file/device/UI or floating-point substitute. Inputs own bounded NUL-terminated buffers; callbacks verify forwarded limits, not native numeric-parser validation.')
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':print(json.dumps(build(),indent=2))
