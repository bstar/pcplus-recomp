#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <io.h>
#include <limits.h>
#include "runtime.h"
#include "script_file_runtime.h"
#include "compiler_heap_snapshot.h"
unsigned runtime_error;
void runtime_set_error(unsigned error){if(!runtime_error)runtime_error=error;}
unsigned test_slot,test_origin,test_count,test_byte,test_integer;
unsigned test_string_at,test_flushes,test_warnings;
long test_position,test_long_value;
char *test_strings[2],*test_buffer;
extern unsigned test_comparison;
extern void script_file_call(unsigned);
static unsigned checks,failures;
static struct {unsigned char before[16];char bytes[81];unsigned char after[16];} guarded;
static struct _heapinfo heap_before[128],heap_after[128],near_before[128],near_after[128];
static unsigned char jft_before[20],jft_after[20];
static const char *phase;
static unsigned cpu_flags(void);
#pragma aux cpu_flags = "pushf" "pop ax" value [ax] modify exact [ax];
static unsigned ds_value(void);
#pragma aux ds_value = "mov ax,ds" value [ax] modify exact [ax];
static unsigned ss_value(void);
#pragma aux ss_value = "mov ax,ss" value [ax] modify exact [ax];
char *test_ascii_lower(char *p){char *s=p;while(*s){if(*s>='A'&&*s<='Z')*s+='a'-'A';++s;}return p;}
static void ck(unsigned okay){++checks;if(!okay){++failures;printf("FAIL %s check%u err%u cmp%u live%u\n",phase,checks,runtime_error,test_comparison,runtime_script_file_live);}}
static unsigned near_snapshot(struct _heapinfo *entries){struct _heapinfo item;unsigned count=0;int status;item._pentry=0;while((status=_nheapwalk(&item))==_HEAPOK)if(item._useflag==_USEDENTRY){ck(count<128);if(count>=128)return count;entries[count++]=item;}ck(status==_HEAPEND||status==_HEAPEMPTY);return count;}
static void jft(unsigned char *out){union REGS r;r.h.ah=0x51;intdos(&r,&r);_fmemcpy(out,MK_FP(r.x.bx,0x18),20);}
static void call(unsigned opcode){unsigned flags=cpu_flags();test_string_at=0;script_file_call(opcode);ck(ds_value()==ss_value());ck((cpu_flags()&0x600)==(flags&0x600));}
static void guard(void){memset(&guarded,0xa5,sizeof(guarded));test_buffer=guarded.bytes;}
static void intact(void){unsigned i;for(i=0;i<16;++i){ck(guarded.before[i]==0xa5);ck(guarded.after[i]==0xa5);}}
static void open_slot(unsigned slot,char *path,char *mode){test_slot=slot;test_strings[0]=path;test_strings[1]=mode;call(5);}
static void close_slot(unsigned slot){test_slot=slot;call(1);}
static void put(unsigned byte){test_byte=byte;call(6);}
static void puts_native(char *s){test_strings[0]=s;call(7);}
static void seek_native(long at,unsigned origin){test_position=at;test_origin=origin;call(9);}
static void tell_native(long expected){test_long_value=0x12345678;call(10);ck(test_long_value==expected);}
static void eof_native(unsigned expected){call(12);ck(test_integer==expected);}
static void finish(void){unsigned i;runtime_script_files_finish();ck(runtime_script_file_live==0);for(i=0;i<6;++i)ck(runtime_script_file_slots[i]==0);}
static void binary(void){unsigned i;unsigned char expected[80];
 phase="binary";ck(runtime_script_files_reset()==0);ck(runtime_script_file_keep_crlf==1);
 open_slot(0,"BINARY.BIN","W+B");ck(test_comparison==0&&runtime_script_file_live==1);
 for(i=0;i<256;++i)put(i);ck(test_comparison==0);tell_native(256L);
 for(i=0;i<80;++i)expected[i]=(unsigned char)(255-i);
 test_strings[0]=(char *)expected;test_count=80;call(11);tell_native(336L);call(2);ck(test_comparison==0);
 seek_native(0L,0);ck(test_comparison==0);for(i=0;i<256;++i){call(3);ck(test_integer==i&&test_comparison==0);}
 guard();test_count=80;test_flushes=0;call(8);ck(test_integer==80&&memcmp(guarded.bytes,expected,80)==0&&guarded.bytes[80]==0);ck(test_flushes==1);intact();
 call(3);ck(test_integer==65535U&&test_comparison==0);eof_native(16);ck(test_comparison==0);
 call(0);eof_native(0);seek_native(0L,0);eof_native(0);tell_native(0L);
 guard();test_count=0;call(8);ck(test_integer==0&&guarded.bytes[0]==0);tell_native(0L);intact();
 seek_native(-1L,0);ck(test_comparison==65535U);close_slot(0);ck(test_comparison==0);finish();
 open_slot(0,"BINARY.BIN","rb");put('X');ck(test_comparison==32);seek_native(0L,0);ck(test_comparison==0);call(3);ck(test_integer==0&&test_comparison==32);call(0);ck(test_comparison==32);eof_native(0);ck(test_comparison==32);seek_native(0L,0);call(3);ck(test_integer==0&&test_comparison==0);close_slot(0);finish();
}
static void lines(void){
 phase="lines";ck(runtime_script_files_reset()==0);open_slot(0,"LINES.BIN","wb");puts_native("A\r\nB\nC\032");close_slot(0);
 open_slot(0,"LINES.BIN","rb");guard();test_flushes=0;call(4);ck(strcmp(guarded.bytes,"A\r\n")==0&&test_flushes==1);intact();
 seek_native(0L,0);runtime_script_file_keep_crlf=0;guard();call(4);ck(strcmp(guarded.bytes,"A")==0);intact();
 guard();call(4);ck(strcmp(guarded.bytes,"B")==0);intact();guard();call(4);ck(strcmp(guarded.bytes,"C")==0);intact();eof_native(16);
 guard();call(4);ck(guarded.bytes[0]==0&&test_comparison==0);intact();close_slot(0);finish();
 open_slot(0,"TEXT.TXT","wt");puts_native("A\nB\nEND");put(26);puts_native("TAIL\n");close_slot(0);
 open_slot(0,"TEXT.TXT","rt");runtime_script_file_keep_crlf=1;guard();call(4);ck(strcmp(guarded.bytes,"A\n")==0);tell_native(3L);
 guard();call(4);ck(strcmp(guarded.bytes,"B\n")==0);guard();call(4);ck(strcmp(guarded.bytes,"END")==0);eof_native(16);close_slot(0);finish();
}
static void modes_and_long_lines(void){unsigned i;
 phase="modes";ck(runtime_script_files_reset()==0);
 open_slot(0,"INVALID.BIN","");ck(test_comparison==1&&runtime_script_file_live==0);
 open_slot(0,"INVALID.BIN","bad");ck(test_comparison==1&&runtime_script_file_live==0);
 open_slot(0,"","rb");ck(test_comparison==1&&runtime_script_file_live==0);
 open_slot(0,"APPEND.BIN","wb");puts_native("first");close_slot(0);
 open_slot(0,"APPEND.BIN","ab");puts_native("second");seek_native(0L,0);ck(test_comparison==0);put('!');close_slot(0);
 open_slot(0,"LONGTXT.BIN","wb");guard();for(i=0;i<80;++i)guarded.bytes[i]='A';guarded.bytes[80]=0;
 test_strings[0]=guarded.bytes;test_count=80;call(11);puts_native("\r\nEND");close_slot(0);intact();
 open_slot(0,"LONGTXT.BIN","rb");runtime_script_file_keep_crlf=0;guard();call(4);ck(strlen(guarded.bytes)==80);for(i=0;i<80;++i)ck(guarded.bytes[i]=='A');intact();
 guard();call(4);ck(guarded.bytes[0]==0);intact();guard();call(4);ck(strcmp(guarded.bytes,"END")==0);eof_native(16);intact();close_slot(0);finish();
}
static void long_seek(void){
 phase="long";ck(runtime_script_files_reset()==0);open_slot(0,"SPARSE.BIN","w+b");seek_native(70000L,0);ck(test_comparison==0);tell_native(70000L);put(65);tell_native(70001L);
 seek_native(-1L,2);ck(test_comparison==0);call(3);ck(test_integer==65);call(3);eof_native(16);call(2);eof_native(16);
 seek_native(-70002L,2);ck(test_comparison==65535U);eof_native(0);tell_native(70001L);
 seek_native(-70002L,1);ck(test_comparison==65535U);tell_native(70001L);seek_native(-1L,1);ck(test_comparison==0);tell_native(70000L);call(3);ck(test_integer==65);close_slot(0);finish();
}
static void failures_and_ownership(void){unsigned i,live;unsigned char descriptor;aspect_script_file_prefix *saved;
 phase="ownership";ck(runtime_script_files_reset()==0);
 open_slot(0,"REPLACE.BIN","wb");puts_native("previous");saved=runtime_script_file_slots[0];
 open_slot(0,"ABSENT\\NO.BIN","rb");ck(test_comparison==1&&runtime_script_file_slots[0]==0&&runtime_script_file_live==0);ck(runtime_script_file_close_calls==1);
 open_slot(0,"REPLACE.BIN","rb");saved=runtime_script_file_slots[0];live=runtime_script_file_live;
 ck(runtime_script_files_reset()==ASPECT_RUN_STATE&&runtime_script_file_slots[0]==saved&&runtime_script_file_live==live);ck(runtime_error==0);
 test_count=81;guard();ck(runtime_script_file_read(guarded.bytes,1,81,saved)==0&&runtime_error==ASPECT_RUN_OPERAND);intact();runtime_error=0;tell_native(0L);close_slot(0);
 ck(runtime_script_file_close(&runtime_script_file_fallback)==-1&&runtime_error==ASPECT_RUN_STATE);runtime_error=0;
 ck(runtime_script_file_getc(0)==-1&&runtime_error==ASPECT_RUN_STATE);runtime_error=0;finish();
 open_slot(0,"BADCL.BIN","wb");puts_native("lost");descriptor=runtime_script_file_slots[0]->descriptor;ck(_dos_close(descriptor)==0);close_slot(0);ck(test_comparison==65535U&&runtime_script_file_live==0&&runtime_script_file_slots[0]==0);ck(runtime_error==0);
 open_slot(0,"BADEND.BIN","wb");puts_native("lost");open_slot(1,"GOODEND.BIN","wb");puts_native("kept");
 descriptor=runtime_script_file_slots[0]->descriptor;ck(_dos_close(descriptor)==0);runtime_error=ASPECT_RUN_CANCELLED;test_comparison=0xbeef;finish();
 ck(runtime_script_file_cleanup_errors==1&&runtime_error==ASPECT_RUN_CANCELLED&&test_comparison==0xbeef);runtime_error=0;finish();ck(runtime_script_file_cleanup_errors==1);
 /* Unused slots must remain NULL, including after a failed replacement. */
 for(i=0;i<6;++i)ck(runtime_script_file_slots[i]==0);
}
static void cycles(void){unsigned cycle,slot,before_count=0,after_count=0,near_count,near_after_count,i;char path[13];
 phase="cycles";ck(runtime_script_files_reset()==0);
 /* Warm every simultaneous CRT FILE owner before the independent heap/JFT baseline. */
 for(slot=0;slot<6;++slot){sprintf(path,"SLOT%u.BIN",slot);open_slot(slot,path,"w+b");put('0'+slot);}
 ck(runtime_script_file_live==6&&runtime_script_file_peak==6);finish();
 ck(compiler_far_heap_snapshot(heap_before,128,&before_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<100;++cycle){
  ck(runtime_script_files_reset()==0);
  for(slot=0;slot<6;++slot){sprintf(path,"SLOT%u.BIN",slot);open_slot(slot,path,"w+b");ck(test_comparison==0);puts_native("cycle");tell_native(5L);}
  ck(runtime_script_file_live==6&&runtime_script_file_peak==6);
  /* This is the finish API boundary, not a claim that VM abort/CHAIN is integrated. */
  finish();ck(runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
 }
 jft(jft_after);ck(memcmp(jft_before,jft_after,20)==0);
 ck(compiler_far_heap_snapshot(heap_after,128,&after_count)==0);ck(before_count==after_count);
 for(i=0;i<before_count&&i<after_count;++i)ck(heap_before[i]._pentry==heap_after[i]._pentry&&heap_before[i]._size==heap_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_after_count==near_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("CYCLES 100 six-slot rounds farheap%u nearheap%u JFT-preserved\n",before_count,near_count);
}
int main(void){
 binary();lines();modes_and_long_lines();long_seek();failures_and_ownership();cycles();phase="final";
 ck(runtime_error==0&&runtime_script_file_live==0&&test_warnings==0);printf("SCRIPT_FILES %u checks %u failures\n",checks,failures);return failures?1:0;
}
