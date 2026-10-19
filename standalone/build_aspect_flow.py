#!/usr/bin/env python3
"""Build source-owned native ASPECT control-flow/operand objects and DOS diagnostic."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-flow'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[(1,'locals',0xd1f2,0xd20d),(2,'seek',0xd27d,0xd2a0),
       (3,'calls',0xd2d6,0xd372),(4,'readers',0xe129,0xe199)]
ENTRIES={'reserve_locals':0xd1f2,'gate_decrement':0xd27d,'gate_increment':0xd282,
         'seek':0xd287,'call':0xd2d6,'push_frame':0xd2f9,'call_operand':0xd307,
         'call_framed':0xd310,'return':0xd317,'return_framed':0xd339,
         'jump':0xd349,'cleanup_locals':0xd352,'read_word':0xe129,'read_dword':0xe176}
FILE_BASE=109184-0xd0d0
BACKENDS={'fseek':0x853a,'ftell':0x8ed8,'refill':0x9094,'fread':0x845a,'exit':0x4eb5,'error':0x4efb}
DATA={'stream':0x4b02,'wait_gate':0xe382,'depth':0xe37a,'frame':0xe13a,
      'local_count':0xe320,'locals':0xe2fc,'stack_pointer':0xe13c}
STACK_START,STACK_END,COPY,COPY_END=0xd0d0,0xd195,0x85b4,0x85fc
BASE,LENGTH=0x9062,0x3aca

ASM=r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
'''
ASM+='\n'.join('extern aspect_flow_'+name for name in ENTRIES)+'\n'
ASM+=r'''
extern _model_refill,_model_fread,_model_fseek,_model_ftell,_model_exit,_record_error
global _run_flow
_run_flow:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov word [_aborted],0
 mov [saved_sp],sp
 mov bx,sp
 mov word [bx-10],0xa5a5
 mov word [bx-8],0xa5a5
 mov si,0x1111
 mov di,0x2222
 mov bx,[bp+4]
 shl bx,1
 call word [cs:operations+bx]
 mov [_result_low],ax
 mov [_result_high],dx
 cmp sp,[saved_sp]
 jne run_bad
 cmp si,0x1111
 jne run_bad
 cmp di,0x2222
 je run_done
run_bad:
 inc word [_abi_bad]
 jmp short run_done
run_aborted:
 mov word [_aborted],1
 mov sp,[saved_sp]
run_done:
 pop es
 pop di
 pop si
 pop bp
 ret
operations: dw '''+','.join('op_'+name for name in ENTRIES)+ '\n'
for name in ENTRIES:
    ASM+='op_'+name+':\n'
    if name in ('seek','call'):
        ASM+=' push word [bp+8]\n push word [bp+6]\n'
    ASM+=' call aspect_flow_'+name+'\n ret\n'
ASM+=r'''
global aspect_flow_refill,aspect_flow_fread,aspect_flow_fseek,aspect_flow_ftell,aspect_flow_exit
aspect_flow_refill: jmp _model_refill
aspect_flow_fread: jmp _model_fread
aspect_flow_fseek: jmp _model_fseek
aspect_flow_ftell: jmp _model_ftell
aspect_flow_exit: jmp _model_exit
global aspect_flow_error,aspect_stack_error
aspect_flow_error:
aspect_stack_error:
 push bp
 mov bp,sp
 push word [bp+4]
 call _record_error
 pop bx
 cmp word [_error_returns],0
 je run_aborted
 pop bp
 ret 2
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global aspect_flow_stream,aspect_flow_wait_gate,aspect_flow_depth,aspect_flow_frame
 global aspect_flow_local_count,aspect_flow_locals
 global aspect_stack_pointer,aspect_stack_arena
 global _stream_token,_wait_gate,_depth,_frame,_local_count,_locals,_pointer,_arena_storage
 global _result_low,_result_high,_aborted,_abi_bad,_error_returns
extern _file_record
aspect_flow_stream:
_stream_token: dw _file_record
aspect_flow_wait_gate:
_wait_gate: dw 0
aspect_flow_depth:
_depth: dw 0
aspect_flow_frame:
_frame: dw 0
aspect_flow_local_count:
_local_count: dw 0
aspect_flow_locals:
_locals: times 18 dw 0
aspect_stack_pointer:
_pointer: dw 0
_result_low: dw 0
_result_high: dw 0
_aborted: dw 0
_abi_bad: dw 0
_error_returns: dw 0
saved_sp: dw 0
_arena_storage: times 4 db 0
aspect_stack_arena: times 0x3aca+128 db 0
'''

C=r'''
#include <stdio.h>
#include <string.h>
extern unsigned stream_token,wait_gate,depth,frame,local_count,locals[18],pointer;
extern unsigned result_low,result_high,aborted,abi_bad,error_returns;
extern unsigned char arena_storage[4+0x3aca+128];
#define arena (arena_storage+4)
extern void run_flow(unsigned op,unsigned low,unsigned high);
/* The fixture provides only modeled CRT calls; no real FILE object or disk IO. */
struct record {unsigned pointer;int remaining;unsigned reserved,flags;} file_record;
static unsigned char data[256];
static unsigned file_length,head,fseek_failure,ftell_failure,exits,errors,refills,reads,seeks,tells;
static unsigned last_origin,last_error;static unsigned long last_seek;
static unsigned long checks;static unsigned failures;
static void ck(unsigned condition){++checks;if(!condition){++failures;printf("FAIL %lu\n",checks);}}
static unsigned position(void){return head-(file_record.remaining>0?file_record.remaining:0);}
unsigned model_refill(unsigned token){
 ++refills;ck(token==stream_token);
 if(head>=file_length){file_record.flags|=0x10;return 0xffff;}
 file_record.remaining=0;file_record.pointer=(unsigned)(data+head+1);return data[head++];
}
unsigned model_fread(unsigned dest,unsigned size,unsigned count,unsigned token){
 unsigned n,i,pos=position();++reads;ck(size==4 && count==1 && token==stream_token);
 n=file_length-pos;if(n>size*count)n=size*count;
 for(i=0;i<n;++i)((unsigned char *)dest)[i]=data[pos+i];
 head=pos+n;file_record.remaining=0;file_record.pointer=(unsigned)(data+head);
 if(n<size*count)file_record.flags|=0x10;
 return n/size;
}
unsigned model_fseek(unsigned token,unsigned low,unsigned high,unsigned origin){
 ++seeks;ck(token==stream_token);last_origin=origin;last_seek=((unsigned long)high<<16)|low;
 if(fseek_failure || high || low>file_length)return 0xffff;
 head=low;file_record.remaining=0;file_record.pointer=(unsigned)(data+head);file_record.flags=0;
 return 0;
}
unsigned long model_ftell(unsigned token){++tells;ck(token==stream_token);return ftell_failure?0xffffffffUL:(unsigned long)position();}
void model_exit(void){++exits;}
void record_error(unsigned code){++errors;last_error=code;ck(code==105);}
static void reset(unsigned length){unsigned i;
 memset(arena,0xa5,0x3aca+128);memset(locals,0,sizeof(locals));
 for(i=0;i<256;++i)data[i]=(unsigned char)(i*73+19);
 file_length=length;head=0;file_record.pointer=(unsigned)data;file_record.remaining=0;file_record.flags=0;
 wait_gate=depth=local_count=0;frame=0x2468;pointer=(unsigned)arena;
 result_low=result_high=aborted=abi_bad=error_returns=0;
 fseek_failure=ftell_failure=exits=errors=refills=reads=seeks=tells=last_origin=last_error=0;last_seek=0;
}
static void call(unsigned op,unsigned low,unsigned high){run_flow(op,low,high);ck(!abi_bad);}
static void put32(unsigned where,unsigned long value){memcpy(data+where,&value,4);}
int main(void){unsigned n,i;unsigned long value;FILE *f;
 reset(128);call(OP_gate_decrement,0,0);ck(wait_gate==0xffff);call(OP_gate_increment,0,0);ck(wait_gate==0);
 wait_gate=0xffff;call(OP_gate_increment,0,0);ck(wait_gate==0);call(OP_gate_decrement,0,0);ck(wait_gate==0xffff);
 for(n=0;n<=2;++n){reset(2);file_record.remaining=n;head=n;call(OP_read_word,0,0);ck(result_low==((unsigned)data[1]<<8|data[0]));ck(refills==2-n);ck(position()==2);}
 reset(0);call(OP_read_word,0,0);ck(result_low==0xffff && refills==2);
 reset(1);call(OP_read_word,0,0);ck(result_low==(0xff00|data[0]) && refills==2);
 for(n=0;n<=4;++n){reset(n);value=0xa5a5a5a5UL;memcpy(&value,data,n);call(OP_read_dword,0,0);ck(result_low==(unsigned)value && result_high==(unsigned)(value>>16));ck(reads==1 && position()==n);}
 reset(128);call(OP_seek,17,0);ck(position()==17 && last_seek==17 && last_origin==0);ck(depth==0 && pointer==(unsigned)arena);
 call(OP_call,40,0);ck(depth==1 && pointer==(unsigned)arena+4 && position()==40);ck(*((unsigned long *)arena)==17);
 call(OP_call,60,0);ck(depth==2 && pointer==(unsigned)arena+8 && position()==60);ck(*((unsigned long *)(arena+4))==40);
 call(OP_return,0,0);ck(depth==1 && pointer==(unsigned)arena+4 && position()==40);
 call(OP_return,0,0);ck(depth==0 && pointer==(unsigned)arena && position()==17);
 call(OP_return,0,0);ck(exits==1 && position()==17);
 reset(128);put32(0,40);call(OP_call_framed,0,0);
 ck(depth==1 && pointer==(unsigned)arena+6 && frame==(unsigned)arena+6 && position()==40);
 ck(*((unsigned long *)arena)==4 && *((unsigned *)(arena+4))==0x2468);
 data[40]=17;data[41]=0;call(OP_reserve_locals,0,0);ck(pointer==(unsigned)arena+23 && !errors);
 call(OP_return_framed,0,0);ck(pointer==(unsigned)arena && frame==0x2468 && depth==0 && position()==4);
 reset(128);put32(0,31);call(OP_jump,0,0);ck(position()==31 && depth==0 && pointer==(unsigned)arena && reads==1);
 reset(128);call(OP_push_frame,0,0);ck(frame==(unsigned)arena+2 && *((unsigned *)arena)==0x2468);
 reset(128);depth=2;local_count=3;locals[0]=9;locals[2]=3;locals[6]=8;locals[8]=2;locals[12]=7;locals[14]=4;
 call(OP_cleanup_locals,0,0);ck(local_count==1 && locals[0]==0 && locals[6]==8 && locals[12]==0);
 ck(locals[2]==3 && locals[8]==2 && locals[14]==4);
 call(OP_cleanup_locals,0,0);ck(local_count==0xffff); /* Native scans inactive records again. */
 reset(128);fseek_failure=1;call(OP_call,40,0);ck(depth==1 && pointer==(unsigned)arena+4 && position()==0 && seeks==1);
 reset(128);ftell_failure=1;call(OP_call,40,0);ck(*((unsigned long *)arena)==0xffffffffUL && depth==1 && position()==40);
 reset(128);depth=0xffff;call(OP_call,40,0);ck(depth==0 && pointer==(unsigned)arena+4);
 for(i=0;i<2;++i){reset(2);data[0]=1;data[1]=0;pointer=(unsigned)arena+0x3aca;error_returns=i;
  call(OP_reserve_locals,0,0);ck(pointer==(unsigned)arena+0x3aca+1 && errors==1 && last_error==105 && aborted==!i);
 }
 for(n=0;n<64;++n){reset(128);put32(0,n);call(OP_call_operand,0,0);ck(position()==n && depth==1 && *((unsigned long *)arena)==4);call(OP_return,0,0);ck(position()==4 && !depth);}
 f=fopen("DONE.TXT","w");if(!f)return 2;
 fprintf(f,"ASPECT_FLOW %lu checks %u failures\n",checks,failures);fclose(f);
 printf("ASPECT_FLOW %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'src/aspect/control_flow.asm';stack=ROOT/'src/aspect/value_stack.asm';move=ROOT/'reconstruction/erase/move_bytes.asm'
    inc='-I'+str(ROOT/'reconstruction/uart')+'/'
    for unit,name,start,end in UNITS:
        subprocess.run(['nasm','-f','bin','-DASPECT_FLOW_FLAT',f'-DASPECT_FLOW_UNIT={unit}',inc,str(source),'-o',str(OUT/(name+'.bin'))],check=True)
        assert len((OUT/(name+'.bin')).read_bytes())==end-start
    subprocess.run(['nasm','-f','obj',inc,str(source),'-o',str(OUT/'flow.obj')],check=True)
    for fmt,defs,target in [('bin',['-DASPECT_STACK_FLAT'],'stack.bin'),('obj',[],'stack.obj')]:
        subprocess.run(['nasm','-f',fmt,*defs,inc,str(stack),'-o',str(OUT/target)],check=True)
    for fmt,defs,target in [('bin',[],'copy.bin'),('obj',['-DERASE_OMF'],'copy.obj')]:
        subprocess.run(['nasm','-f',fmt,*defs,inc,str(move),'-o',str(OUT/target)],check=True)
    (OUT/'callbacks.asm').write_text(ASM)
    definitions='\n'.join(f'#define OP_{name} {i}' for i,name in enumerate(ENTRIES))+'\n'
    (OUT/'diagnostic.c').write_text(definitions+C)
    subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=FLOW.map','-fe=FLOW.EXE',
                    str(OUT/'diagnostic.c'),str(OUT/'flow.obj'),str(OUT/'stack.obj'),str(OUT/'copy.obj'),str(OUT/'callbacks.obj')],cwd=OUT,check=True)
    inputs=[source,stack,move,ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
    report=dict(binary_sha256=sha((OUT/'FLOW.EXE').read_bytes()),original_inputs=[],
                units=[dict(name=name,start=start,end_exclusive=end,source_file_start=FILE_BASE+start,
                            bytes=end-start,sha256=sha((OUT/(name+'.bin')).read_bytes())) for _,name,start,end in UNITS],
                sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in inputs},
                scope='Recovered native flow/operand routines with actual typed stack/copy. Source-owned modeled CRT/error/exit callbacks; no full loader/VM or checked IO claim.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
