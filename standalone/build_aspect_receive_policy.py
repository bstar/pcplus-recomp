#!/usr/bin/env python3
"""Build reused native receive/XLT policy with explicit service callbacks."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-receive-policy'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[(1,0x4c3c,0x4c4f,0x1200),(2,0x4c74,0x4cb4,0x1200)]
ENTRIES=dict(displayed=0x4c3c,read=0x4c74)
ASM=r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_receive_policy_displayed,aspect_receive_policy_read
extern _policy_raw,_policy_delayed,_policy_pattern,_policy_emit
global _run_policy
_run_policy:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov [saved_sp],sp
 mov [saved_bp],bp
 mov si,0x1357
 mov di,0x2468
 cmp word [bp+4],0
 jne .displayed
 push word [bp+8]
 push word [bp+6]
 call aspect_receive_policy_read
 jmp .checked
.displayed:
 push word [bp+6]
 call aspect_receive_policy_displayed
.checked:
 mov [_result],ax
 cmp sp,[saved_sp]
 jne .bad
 cmp bp,[saved_bp]
 jne .bad
 cmp si,0x1357
 jne .bad
 cmp di,0x2468
 je .done
.bad:
 inc word [_abi_bad]
 mov sp,[saved_sp]
 mov bp,[saved_bp]
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
global aspect_receive_policy_raw,aspect_receive_policy_delayed
aspect_receive_policy_raw: jmp _policy_raw
aspect_receive_policy_delayed: jmp _policy_delayed
global aspect_receive_policy_pattern_byte,aspect_receive_policy_emit_byte
aspect_receive_policy_pattern_byte:
 push bp
 mov bp,sp
 push word [bp+4]
 call _policy_pattern
 pop bx
 mov ax,0xa55a
 pop bp
 ret 2
aspect_receive_policy_emit_byte:
 push bp
 mov bp,sp
 push word [bp+4]
 call _policy_emit
 pop bx
 mov ax,0xb00b
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
saved_sp: dw 0
saved_bp: dw 0
global _result,_abi_bad
_result: dw 0
_abi_bad: dw 0
global aspect_receive_policy_table,_policy_table
aspect_receive_policy_table:
_policy_table: times 256 db 0
; Controlled diagnostic neighbors, not part of the production256-byte table.
 db 0xa6,0x5a
global aspect_receive_policy_display,_policy_display
aspect_receive_policy_display:
_policy_display: dw 0
global aspect_receive_policy_pattern_count,_policy_pattern_count
aspect_receive_policy_pattern_count:
_policy_pattern_count: dw 0
'''
C=r'''
#include <stdio.h>
#include <string.h>
extern unsigned result,abi_bad,policy_display,policy_pattern_count;
extern unsigned char policy_table[258];
extern void run_policy(unsigned operation,unsigned first,unsigned second);
static unsigned raw_value,delayed_value,trace_length,trace_values[4];
static unsigned long checks,failures;static unsigned char trace[4];
static void ck(int ok){++checks;if(!ok){++failures;if(failures<8)printf("FAIL %lu\n",checks);}}
static void record(unsigned char kind,unsigned value){ck(trace_length<4);if(trace_length<4){trace[trace_length]=kind;trace_values[trace_length++]=value;}}
unsigned policy_raw(void){record('R',raw_value);return raw_value;}
unsigned policy_delayed(void){record('D',delayed_value);return delayed_value;}
void policy_pattern(unsigned value){record('P',value);}
void policy_emit(unsigned value){record('E',value);}
static void setup(unsigned kind){unsigned i;for(i=0;i<256;++i)policy_table[i]=(unsigned char)(kind==0?i:kind==1?(i*17+3):kind==2?(i^0xa5):0);policy_table[256]=0xa6;policy_table[257]=0x5a;}
static void verify(unsigned op,unsigned echo,unsigned delayed,unsigned monitor,unsigned value,unsigned mapped){unsigned i=0;
 trace_length=0;raw_value=delayed_value=value;policy_pattern_count=monitor;policy_display=echo;
 run_policy(op,op?delayed:echo,delayed);
 if((abi_bad||result!=mapped||trace_values[0]!=value)&&failures<8)printf("CASE op%u e%u d%u p%u v%u m%u got%u abi%u trace%u/%u,%u/%u,%u/%u\n",op,echo,delayed,monitor,value,mapped,result,abi_bad,trace[0],trace_values[0],trace[1],trace_values[1],trace[2],trace_values[2]);
 ck(!abi_bad&&result==mapped);ck(trace_length>=1&&trace[0]==(delayed?'D':'R')&&trace_values[0]==value);i=1;
 if(!(value&0x8000)){if(monitor){ck(i<trace_length&&trace[i]=='P'&&trace_values[i]==mapped);++i;}if(echo){ck(i<trace_length&&trace[i]=='E'&&trace_values[i]==mapped);++i;}}
 ck(trace_length==i&&raw_value==value&&delayed_value==value);
}
int main(void){unsigned value,kind,op,echo,delayed,monitor,i;unsigned char snapshot[256];FILE *f;
 for(kind=0;kind<4;++kind){setup(kind);memcpy(snapshot,policy_table,256);
  for(value=0;value<256;++value)for(op=0;op<2;++op)for(echo=0;echo<3;++echo)for(delayed=0;delayed<3;++delayed)for(monitor=0;monitor<3;++monitor){
   verify(op,echo==2?0xffff:echo,delayed==2?0xffff:delayed,monitor==2?0xffff:monitor,value,policy_table[value]);ck(!memcmp(snapshot,policy_table,256));
  }
 }
 setup(1);
 for(i=0;i<5;++i){static const unsigned negative[]={0xffff,0xfffe,0x8000,0x8001,0xabcd};for(op=0;op<2;++op)for(delayed=0;delayed<2;++delayed)verify(op,1,delayed,1,negative[i],negative[i]);}
 /* Unchecked non-byte positive input reads the controlled table neighbors. */
 verify(0,1,0,1,256,0xa6);verify(1,1,1,1,257,0x5a);
 /* Raw and delayed selection use distinct source results in this case. */
 trace_length=0;raw_value=17;delayed_value=23;policy_pattern_count=policy_display=0;run_policy(0,0,0);ck(result==policy_table[17]&&trace[0]=='R');trace_length=0;run_policy(0,0,1);ck(result==policy_table[23]&&trace[0]=='D');
 f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_RECEIVE_POLICY %lu checks %lu failures\n",checks,failures);fclose(f);printf("ASPECT_RECEIVE_POLICY %lu checks %lu failures\n",checks,failures);return failures?1:0;
}
'''

def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 OUT.mkdir(parents=True,exist_ok=True);source=ROOT/'src/aspect/receive_policy.asm';shared=ROOT/'reconstruction/translation/receive.asm';encodings=ROOT/'reconstruction/uart/encodings.inc';inc='-I'+str(encodings.parent)+'/'
 subprocess.run(['nasm','-f','obj',inc,str(source),'-o',str(OUT/'policy.obj')],check=True)
 units=[]
 for u,a,b,base in UNITS:
  target=OUT/f'policy{u}.bin';subprocess.run(['nasm','-f','bin',inc,'-DASPECT_RECEIVE_POLICY_FLAT',f'-DASPECT_RECEIVE_POLICY_UNIT={u}',str(source),'-o',str(target)],check=True);assert target.stat().st_size==b-a
  units.append(dict(name=target.name,start=a,end_exclusive=b,file_base=base,sha256=sha(target.read_bytes()),reused=u==2))
 (OUT/'callbacks.asm').write_text(ASM);(OUT/'diagnostic.c').write_text(C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=POLICY.map','-fe=POLICY.EXE',str(OUT/'diagnostic.c'),str(OUT/'policy.obj'),str(OUT/'callbacks.obj')],cwd=OUT,check=True)
 sources=[source,shared,encodings,Path(__file__).resolve()]
 report=dict(original_inputs=[],native_policy_bytes=sum(b-a for _,a,b,_ in UNITS),reused_native_bytes=sum(u['end_exclusive']-u['start'] for u in units if u['reused']),units=units,
  binary_sha256=sha((OUT/'POLICY.EXE').read_bytes()),sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},scope='Actual4C3C adapter and reused4C74 policy. Raw/delayed reads, pattern monitor and console renderer are explicit component callbacks. Fixture tables exercise one translation and preserve callback ordering; no live UART, event engine or native renderer acceptance claim.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
