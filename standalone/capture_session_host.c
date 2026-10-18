/* Independently compiled processed-text owner; synthetic DOS files/kernel only. */
#include "capture_session.h"
#include "capture_fs.h"
#include <stdio.h>
#include <string.h>
#include <dos.h>
#ifndef CS_FAULT
#include <direct.h>
#endif
unsigned terminal_sink_398a_enabled,terminal_sink_398c_disabled;
static unsigned cases,failures;
static void check(int yes,const char *name)
{++cases;printf("%s %s\n",yes?"PASS":"FAIL",name);if(!yes)++failures;}
static unsigned feed(unsigned ch,unsigned count)
{unsigned i;for(i=0;i<count;++i)if(capture_session_put(ch,0xaaaa)!=(ch&255))break;return i==count;}
#ifdef CS_FAULT
static unsigned fault,exists,owned,opens,writes,closes,attrs,seeks,ops;
static unsigned long position,size;
static unsigned char data[4096];
static char last_path[64];
/* Existing session fault model uses one synthetic current directory. Absolute
 * identity and cross-owner aliases are checked by the dedicated owner suite. */
unsigned capture_fs_canonical(const char *path,char *out)
{++ops;strcpy(out,"C:\\");strcat(out,path);return 0;}
unsigned capture_fs_attributes(const char *path,unsigned *attributes)
{++ops;++attrs;strcpy(last_path,!strncmp(path,"C:\\",3)?path+3:path);*attributes=fault==9?1:0;if(fault==1)return 5;return exists?0:2;}
unsigned capture_fs_create(const char *path,int *handle)
{
 ++ops;++opens;strcpy(last_path,!strncmp(path,"C:\\",3)?path+3:path);
 if(fault==2){exists=1;memcpy(data,"raced",5);size=5;return 80;}
 if(exists)return 80;exists=owned=1;size=position=0;*handle=7;return 0;
}
unsigned capture_fs_open_append(const char *path,int *handle)
{++ops;++opens;strcpy(last_path,!strncmp(path,"C:\\",3)?path+3:path);if(fault==10)return 5;if(!exists)return 2;owned=1;*handle=7;position=0;return 0;}
unsigned capture_fs_seek_end(int handle,unsigned long *value)
{++ops;++seeks;if(handle!=7 || !owned)return 6;if(fault==8)return 25;position=size;*value=position;return 0;}
unsigned capture_fs_write(int handle,const void *source,unsigned count,unsigned *written)
{
 ++ops;++writes;if(handle!=7 || !owned)return 6;*written=count;
 if(fault==3 || fault==4 || fault==6 || fault==7)*written=3;
 if(position+*written<=sizeof(data))memcpy(data+(unsigned)position,source,*written);
 position+=*written;if(size<position)size=position;
 return fault==4 || fault==6?112:0;
}
unsigned capture_fs_close(int handle)
{++ops;++closes;if(handle!=7 || !owned)return 6;if(fault==5 || fault==6 || fault==8)return 6;owned=0;return 0;}
static void model(unsigned mode,unsigned present)
{
 if(capture_file_result.handle_open || capture_file_result.handle_uncertain){check(0,"fixture attempted to orphan product handle");return;}
 fault=mode;exists=present;size=position=0;owned=0;memset(data,0,sizeof(data));
 if(present){memcpy(data,"OLD",3);size=3;}
}
static void guards(void)
{
 unsigned before;capture_file_snapshot snapshot;
 struct SREGS s;char __far *end;char saved;
 snapshot=capture_file_result;before=ops;
 check(capture_session_begin(0,0)==CF_ARGUMENT && capture_session_begin((char *)&capture_file_result,0)==CF_ARGUMENT && !memcmp(&snapshot,&capture_file_result,sizeof(snapshot)) && ops==before && !terminal_sink_398a_enabled,"null and empty backend snapshot aliases reject before default fallback IO");
 /* Deliberate VM-only segment-end sentinel: save/restore the byte, so the
  * nonterminated near string requires a wrapping second read and must reject. */
 segread(&s);end=(char __far *)MK_FP(s.ds,0xffff);saved=*end;*end='A';
 check(capture_session_begin((char *)0xffff,0)==CF_ARGUMENT && ops==before,"near segment-end unterminated path rejects before filesystem IO");*end=saved;
 model(1,0);before=opens;check(capture_session_begin("DENIED.LOG",0)==CF_INSPECT && capture_session_notice==CS_DENIED && !capture_session_failed && !terminal_sink_398a_enabled && opens==before,"only true missing-file may fall back to exclusive NEW");
 model(2,0);before=closes;check(capture_session_begin("RACE.LOG",0)==CF_CONFLICT && capture_session_notice==CS_DENIED && !capture_session_failed && !owned && size==5 && !memcmp(data,"raced",5) && closes==before,"NEW race preserves competing target and never acquires or closes handle");
 model(9,1);before=closes;check(capture_session_begin("READONLY.LOG",0)==CF_ARGUMENT && !capture_file_result.handle_open && !capture_session_failed && capture_session_notice==CS_DENIED && capture_session_stop()==CF_OK && capture_session_shutdown()==CF_OK && closes==before && size==3 && !memcmp(data,"OLD",3),"readonly denied begin remains nonsticky across stop and shutdown without close");
 model(10,1);before=closes;check(capture_session_begin("OPENFAIL.LOG",0)==CF_OPEN && capture_file_result.dos_error==5 && !capture_file_result.handle_open && !capture_session_failed && capture_session_stop()==CF_OK && capture_session_shutdown()==CF_OK && closes==before && size==3 && !memcmp(data,"OLD",3),"DOS open error without owned handle remains nonsticky across stop and shutdown");
 model(0,0);check(capture_session_begin("NEW.LOG",0)==CF_OK && capture_file_result.mode==CF_NEW && !strcmp(last_path,"NEW.LOG"),"missing APPEND probe falls back to NEW exclusively");check(capture_session_stop()==CF_OK,"successful new session closes after denied attempts");
 model(0,1);before=opens;check(capture_session_begin("OLD.LOG",0)==CF_OK && capture_file_result.mode==CF_APPEND && capture_file_result.start_size==3 && opens==before+1 && position==3,"existing file uses one write-only seek-END handle");
 snapshot=capture_file_result;before=ops;check(capture_session_begin("OTHER.LOG",5)==CF_BUSY && !memcmp(&snapshot,&capture_file_result,sizeof(snapshot)) && ops==before,"active repeat begin leaves sink and source handle unchanged");
 check(capture_session_put('A',0xffff)=='A' && capture_session_pause()==CF_OK && terminal_sink_398a_enabled && terminal_sink_398c_disabled && capture_session_notice==CS_HOLD && size==4 && data[3]=='A' && !capture_session_buffered,"pause flushes before disabling processed output");before=ops;check(capture_session_put('X',0)==0xffff && capture_session_begin("OTHER.LOG",0)==CF_BUSY && ops==before,"paused sink cannot write or reopen");
 check(capture_session_pause()==CF_OK && !terminal_sink_398c_disabled && capture_session_notice==CS_OPEN && capture_session_stop()==CF_OK && !terminal_sink_398a_enabled && !terminal_sink_398c_disabled && capture_session_notice==CS_CLOSED,"resume then stop clears both native sink flags");
 model(0,0);check(capture_session_begin("",0)==CF_OK && !strcmp(last_path,"PCPLUS.LOG") && capture_session_put(0x10a,0)==10 && capture_session_stop()==CF_OK && size==2 && data[0]==13 && data[1]==10,"explicit empty default and fputc low-byte LF policy");
}
static void fail_case(unsigned mode)
{
 unsigned before,stored;capture_file_snapshot snapshot;
 model(mode==9?3:mode==10?4:mode,mode==8);before=closes;
 if(mode==8){
  check(capture_session_begin("FAULT.LOG",0)==CF_CLOSE && capture_session_failed==CF_CLOSE && capture_file_result.first_status==CF_SEEK && capture_file_result.dos_error==25,"seek primary plus ambiguous cleanup close retained by session");
 }else{
  check(capture_session_begin("FAULT.LOG",0)==CF_OK,"fault session starts");
  if(mode==9){check(feed('A',4) && capture_session_pause()==CF_WRITE && capture_session_buffered==4,"pause flush fault preserves error and disables sink instead of entering HOLD");}
  else if(mode==10){check(feed('A',4),"timer fault buffers data");capture_session_poll(18);check(capture_session_failed==CF_WRITE && capture_session_notice==CS_ERROR,"18tick poll latches foreground write failure");}
  else if(mode==5){check(capture_session_put('Q',0)=='Q' && capture_session_stop()==CF_CLOSE && capture_session_failed==CF_CLOSE && size==1,"checked close failure becomes sticky session failure");}
  else if(mode==7){check(feed('A',255) && capture_session_buffered==255 && capture_session_put(13,0)==0xffff && capture_session_buffered==256,"CR at exact256 boundary reports flush failure rather than successful character");}
  else {check(feed('A',255) && capture_session_buffered==255 && capture_session_put(10,0)==0xffff && capture_session_buffered==255,"LF at255 flush failure never appends its CR or LF");}
 }
 check(capture_session_failed==(mode==5 || mode==8?CF_CLOSE:CF_WRITE) && capture_file_result.first_status==(mode==8?CF_SEEK:mode==5?CF_CLOSE:CF_WRITE) && capture_file_result.dos_error==(mode==8?25:mode==5?6:mode==4 || mode==6 || mode==10?112:0),"session primary status and DOS error exactly match injected fault");
 check(capture_file_result.written==(mode==8?0UL:mode==5?1UL:3UL) && size==(mode==8?3UL:mode==5?1UL:3UL) && !memcmp(data,mode==8?"OLD":mode==5?"Q":"AAA",(unsigned)size),"fault records exact physical prefix and written count without fabricated bytes");
 check(closes==before+1 && !terminal_sink_398a_enabled && !terminal_sink_398c_disabled && capture_session_notice==CS_ERROR && capture_session_failed,"failed sink disables both flags and closes physical handle exactly once");
 snapshot=capture_file_result;before=ops;stored=(unsigned)size;
 check(capture_session_put(13,0)==0xffff && capture_session_flush()==CF_OK && capture_session_pause()==CF_OK && ops==before && size==stored && capture_session_notice==CS_ERROR,"disabled failed session never retries buffered bytes or masks error notice");
 check(capture_session_shutdown()==capture_session_failed && closes==snapshot.close_calls && capture_session_failed && capture_file_result.first_status==snapshot.first_status,"shutdown retains first fatal status and cannot physically close twice");
 if(mode==5 || mode==6 || mode==8){
  snapshot=capture_file_result;before=ops;
  check(capture_session_begin("NEXT.LOG",0)==CF_RECOVERY && capture_session_shutdown()==capture_session_failed && !memcmp(&snapshot,&capture_file_result,sizeof(snapshot)) && ops==before && owned,"ambiguous session close survives rebegin and shutdown without DOS retry");
 }else{
  unsigned failed=capture_session_failed;before=ops;check(capture_session_stop()==CF_OK && capture_session_failed==failed && capture_session_shutdown()==failed && ops==before,"resolved failed stop is idempotent while shutdown retains sticky fatal without IO");
  model(0,0);check(capture_session_begin("NEXT.LOG",100)==CF_OK && !capture_session_buffered && capture_session_put('Z',0)=='Z' && capture_session_stop()==CF_OK && size==1 && data[0]=='Z' && capture_session_failed==failed && capture_session_shutdown()==failed,"new resolved file discards stale buffered suffix but preserves sticky failure history");
 }
}
#else
static void normal(void)
{
 unsigned before;FILE *f;
 check(capture_session_begin("TEXT.LOG",100)==CF_OK && terminal_sink_398a_enabled && !terminal_sink_398c_disabled && capture_session_notice==CS_OPEN,"new processed session opens");
 check(capture_session_put('A',0)=='A' && capture_session_put(10,0)==10 && capture_session_put(13,0)==13 && capture_session_put(0,0)==0 && capture_session_put(255,0)==255 && capture_session_put(127,0)==127 && capture_session_put(0x10a,0)==10,"processed sink translates low-byte LF and preserves CR NUL FF DEL");
 check(capture_session_stop()==CF_OK && capture_file_result.written==9 && capture_file_result.close_calls==1 && capture_session_notice==CS_CLOSED,"stop flushes exact processed bytes and closes once");
 check(capture_session_begin("TEXT.LOG",200)==CF_OK && capture_file_result.start_size==9 && capture_file_result.mode==CF_APPEND,"existing processed file appends");
 check(capture_session_put('B',0)=='B' && capture_session_put(10,0)==10 && capture_session_pause()==CF_OK && terminal_sink_398a_enabled && terminal_sink_398c_disabled && capture_file_result.written==3,"pause flushes CRLF before hold");before=capture_file_result.write_calls;check(capture_session_put('X',0)==0xffff && capture_session_buffered==0 && capture_file_result.write_calls==before,"hold rejects data without buffering or writing");
 check(capture_session_pause()==CF_OK && capture_session_put('C',0)=='C' && capture_session_stop()==CF_OK && !terminal_sink_398a_enabled && !terminal_sink_398c_disabled,"resume and stop restore native flag state");
 check(capture_session_begin("BOUND.LOG",0)==CF_OK && feed('x',255) && capture_session_put(10,0)==10 && capture_session_buffered==2 && capture_file_result.written==255,"LF at255 flushes old prefix then buffers atomic CRLF");
 check(feed('y',254) && capture_session_buffered==0 && capture_file_result.written==511 && capture_file_result.write_calls==2 && capture_session_stop()==CF_OK,"exact256 boundary flushes without extra zero write");
 check(capture_session_begin("TIMED.LOG",100)==CF_OK,"timed processed sink opens");capture_session_poll(110);capture_session_put('T',0);capture_session_poll(127);
 check(capture_session_buffered==1 && !capture_file_result.written,"pending timer starts at observed character time and does not flush at17ticks");capture_session_poll(128);
 check(!capture_session_buffered && capture_file_result.written==1 && capture_file_result.write_calls==1,"18ticks flush pending processed bytes");capture_session_put('U',0);capture_session_poll(129);check(capture_session_buffered==1 && capture_session_stop()==CF_OK,"new pending interval resets after flush and stop writes remainder");
 check(capture_session_begin("CLOCK.LOG",0x1800a8UL)==CF_OK && capture_session_put('M',0)=='M',"midnight timer starts before BIOS rollover");capture_session_poll(9);
 check(capture_session_buffered==1 && !capture_file_result.written,"midnight elapsed17 does not flush");capture_session_poll(10);
 check(!capture_session_buffered && capture_file_result.written==1 && capture_session_stop()==CF_OK,"midnight elapsed18 flushes");
 check(capture_session_begin("",1)==CF_OK && capture_session_put(13,0)==13 && capture_session_stop()==CF_OK && !strcmp(capture_file_result.path,"PCPLUS.LOG"),"explicit empty path selects owned default without character filtering");
 f=fopen("READONLY.LOG","wb");check(f && fwrite("KEEP",1,4,f)==4 && !fclose(f) && !_dos_setfileattr("READONLY.LOG",_A_RDONLY),"prepare actual readonly denied-open fixture");
 check(capture_session_begin("READONLY.LOG",5)==CF_ARGUMENT && !capture_file_result.handle_open && !capture_session_failed && capture_session_notice==CS_DENIED,"actual readonly begin is denied without owning handle or sticky fatal");
 check(capture_session_stop()==CF_OK && capture_session_shutdown()==CF_OK && !capture_session_failed,"actual readonly denial stays nonsticky through stop and shutdown");
 check(capture_session_shutdown()==CF_OK && !capture_session_failed,"successful repeated shutdown remains clean");
}
#endif
int main(int argc,char **argv)
{
 unsigned before_notice;
 terminal_sink_398a_enabled=terminal_sink_398c_disabled=0xa5a5;
 capture_session_notice=capture_session_failed=capture_session_buffered=0xa5a5;
 memset(&capture_file_result,0xa5,sizeof(capture_file_result));before_notice=capture_session_notice;
 check(capture_session_begin("EARLY.LOG",0)==CF_STATE && capture_session_put(10,0)==0xffff && capture_session_flush()==CF_STATE && capture_session_stop()==CF_STATE && capture_session_pause()==CF_STATE,"uninitialized session APIs reject dirty BSS");
 capture_session_poll(123);check(capture_session_notice==before_notice && capture_session_shutdown()==CF_STATE,"uninitialized poll and shutdown do not read dirty failure as status");
 check(capture_session_initialize()==CF_OK && !terminal_sink_398a_enabled && !terminal_sink_398c_disabled && !capture_session_notice && !capture_session_failed && !capture_session_buffered,"session DATA cookie initializes dirty sink state exactly once");
#ifdef CS_FAULT
 if(argc>1){unsigned mode=argv[1][0]=='S'?3:argv[1][0]=='W'?4:argv[1][0]=='C'?5:argv[1][0]=='X'?6:argv[1][0]=='R'?7:argv[1][0]=='P'?9:argv[1][0]=='T'?10:8;fail_case(mode);}else guards();
#else
 (void)argc;(void)argv;normal();
#endif
 printf("CASES %u\n",cases);return failures?1:0;
}
