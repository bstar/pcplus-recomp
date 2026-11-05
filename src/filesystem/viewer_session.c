#include "viewer_session.h"
#include "viewer_decode.h"
#include "viewer_file.h"
#include "viewer_file_backend.h"
#include <dos.h>
typedef unsigned word;
typedef unsigned char byte;
typedef struct viewer_session_state {
 word cookie,phase,busy,active,owned,width,rows,capacity,count,at,pending,eof;
 word error,file_status,decode_status;
 byte __far *page;
 unsigned long current,target,first,last,start,read_position;
 viewer_decode_state decode;
 byte input[256];
 unsigned long offsets[64];
} viewer_session_state;
/* Watcom must reload banked fields after updates (not reuse a preincrement
 * DWord when assigning target/current or testing cache eviction). Decoder
 * byte processing retains its own nonvolatile bounded view of decode/input. */
volatile viewer_session_state __based(__segname("_CODE")) viewer_session_storage={0x5653};
typedef char state_layout[sizeof(viewer_session_state)==596?1:-1];
typedef char snapshot_layout[sizeof(viewer_session_snapshot)==50?1:-1];
#define S viewer_session_storage
static unsigned long address(const void __far *p)
{return ((unsigned long)FP_SEG(p)<<4)+FP_OFF(p);}
static word safe(const void __far *p,word n)
{
 unsigned long a=address(p),b=address((const void __far *)&S);
 return p&&n&&n-1<=0xffffU-FP_OFF(p)&&a<=0xfffffUL-(n-1)&&
        (a+n<=b||b+sizeof(S)<=a);
}
static word enter(void)
{
 if(S.cookie!=0x5653)return VS_STATE;
 if(S.busy)return VS_BUSY;
 if(S.phase==VS_UNCERTAIN)return VS_RECOVERY;
 return VS_OK;
}
static word fail(word status)
{if(!S.error)S.error=status;S.phase=VS_FAILED;return status;}
static word init_page(unsigned long offset)
{
 S.start=offset;
 S.decode_status=viewer_decode_init((viewer_decode_state __far *)&S.decode,S.page,S.capacity,S.width,S.rows,offset);
 if(S.decode_status!=VIEWER_MORE)return fail(VS_DECODE);
 return VS_OK;
}
static word checkpoint(unsigned long page,unsigned long offset)
{
 word slot=(word)page&63;
 if(page>=S.first&&page<=S.last){
  if(S.offsets[slot]!=offset)return fail(VS_INVARIANT);
 }else if(page==S.last+1){
  S.offsets[slot]=offset;S.last=page;
  if(S.last-S.first>=64)S.first=S.last-63;
 }else return fail(VS_INVARIANT);
 return VS_OK;
}
static word complete(void)
{
 word result;
 if(S.decode_status==VIEWER_PAGE){
  if(S.current==0xffffffffUL||S.decode.position<=S.start)return fail(VS_INVARIANT);
  result=checkpoint(S.current+1,S.decode.position);if(result)return result;
 }else if(S.decode_status!=VIEWER_EOF)return fail(VS_DECODE);
 if(S.current<S.target){
  if(S.decode_status==VIEWER_EOF)return fail(VS_INVARIANT);
  S.current++;return init_page(S.decode.position);
 }
 if(S.current!=S.target)return fail(VS_INVARIANT);
 S.phase=VS_READY;return VS_OK;
}
unsigned __far __cdecl viewer_session_begin(const char *path,void *token,
 byte __far *page,word capacity,word width,word rows)
{
 viewer_file_snapshot file;word result=enter(),size;
 if(result)return result;
 if(S.active)return VS_BUSY;
 if(!token||!width||width>132||!rows||rows>49)return VS_ARGUMENT;
 size=width*rows;
 if(capacity<size||!safe(page,size)||!safe((const void __far *)path,64)||
    !viewer_admit_validate(path))return VS_ARGUMENT;
 result=viewer_file_inspect(&file);if(result||file.phase==VF_UNCERTAIN)return VS_RECOVERY;
 if(file.handle!=0xffff||file.claimed)return VS_BUSY;
 S.busy=1;S.active=1;S.owned=0;S.width=width;S.rows=rows;S.capacity=capacity;S.page=page;
 S.count=S.at=S.pending=S.eof=S.error=S.file_status=S.decode_status=0;
 S.current=S.target=S.first=S.last=S.start=S.read_position=0;S.decode.position=0;S.offsets[0]=0;
 S.phase=VS_LOADING;
 S.file_status=viewer_file_open(path,token);
 if(S.file_status){
  result=viewer_file_inspect(&file);
  if(result){S.owned=1;S.error=VS_RECOVERY;S.phase=VS_UNCERTAIN;}
  else{
   S.owned=file.claimed||file.handle!=0xffff;
   fail(VS_IO);if(file.phase==VF_UNCERTAIN)S.phase=VS_UNCERTAIN;
  }
  S.busy=0;return S.phase==VS_UNCERTAIN?VS_RECOVERY:S.error;
 }
 S.owned=1;result=init_page(0);S.busy=0;return result;
}
unsigned __far __cdecl viewer_session_step(void)
{
 word result=enter(),actual=0,used=0;
 if(result)return result;
 if(!S.active||S.phase!=VS_LOADING||!S.owned)return VS_STATE;
 S.busy=1;
 if(S.pending){
  S.file_status=viewer_file_seek(S.start);
  if(S.file_status)result=fail(VS_IO);
  else{S.pending=S.count=S.at=S.eof=0;S.read_position=S.start;result=init_page(S.start);}
 }else if(S.at<S.count){
  S.decode_status=viewer_decode_feed((viewer_decode_state __far *)&S.decode,
   ((const byte __far *)S.input)+S.at,S.count-S.at,&used);
  if(used>S.count-S.at)result=fail(VS_INVARIANT);
  else{
   S.at+=used;
   if(S.decode_status==VIEWER_PAGE||S.decode_status==VIEWER_EOF)result=complete();
   else if(S.decode_status!=VIEWER_MORE||!used)result=fail(VS_DECODE);
  }
 }else if(S.eof){
  S.decode_status=viewer_decode_finish((viewer_decode_state __far *)&S.decode);result=complete();
 }else{
  S.file_status=viewer_file_read((byte __far *)S.input,256,&actual);
  if(S.file_status)result=fail(VS_IO);
  else if(actual>256)result=fail(VS_INVARIANT);
  else{S.count=actual;S.at=0;S.read_position+=actual;if(!actual)S.eof=1;}
 }
 S.busy=0;return result;
}
unsigned __far __cdecl viewer_session_move(word direction)
{
 unsigned long wanted;word result=enter();
 if(result)return result;
 if(direction>VS_NEXT)return VS_ARGUMENT;
 if(!S.active||S.phase!=VS_READY)return S.phase==VS_LOADING?VS_BUSY:VS_STATE;
 if(direction==VS_NEXT){
  if(S.decode_status==VIEWER_EOF)return VS_END;
  if(S.current==0xffffffffUL)return VS_INVARIANT;
  S.busy=1;S.current++;S.target=S.current;S.phase=VS_LOADING;
  result=init_page(S.decode.position);S.busy=0;return result;
 }
 if(direction==VS_PREVIOUS&&!S.current)return VS_TOP;
 wanted=direction==VS_HOME?0:S.current-1;
 S.target=wanted;
 if(wanted>=S.first&&wanted<=S.last){S.current=wanted;S.start=S.offsets[(word)wanted&63];}
 else{S.current=0;S.start=0;S.first=S.last=0;S.offsets[0]=0;}
 S.pending=1;S.phase=VS_LOADING;return VS_OK;
}
unsigned __far __cdecl viewer_session_stop(void)
{
 viewer_file_snapshot file;word result=enter();
 if(result)return result;
 if(S.owned){
  S.busy=1;result=viewer_file_close();if(result&&!S.file_status)S.file_status=result;
  if(viewer_file_inspect(&file)||file.phase==VF_UNCERTAIN||file.claimed||file.handle!=0xffff){
   if(!S.error)S.error=VS_IO;S.phase=VS_UNCERTAIN;S.busy=0;return VS_RECOVERY;
  }
  S.owned=0;S.busy=0;if(result&&!S.error)S.error=VS_IO;
 }
 S.active=0;S.phase=VS_CLOSED;return S.error;
}
unsigned __far __cdecl viewer_session_inspect(viewer_session_snapshot *out)
{
 if(S.cookie!=0x5653)return VS_STATE;
 if(S.busy)return VS_BUSY;
 if(!safe((void __far *)out,sizeof(*out)))return VS_ARGUMENT;
 out->phase=S.phase;out->error=S.error;out->file_status=S.file_status;out->decode_status=S.decode_status;
 out->owned=S.owned;out->pending_seek=S.pending;out->buffered=S.count;out->consumed=S.at;
 out->eof=S.eof;out->width=S.width;out->rows=S.rows;
 out->page=S.current;out->target=S.target;out->start=S.start;out->next=S.decode.position;
 out->read_position=S.read_position;out->cache_first=S.first;out->cache_last=S.last;
 return VS_OK;
}
