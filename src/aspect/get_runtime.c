#if !defined(ASPECT_GET_VM) || !defined(ASPECT_GET_SERVICE) || !defined(ASPECT_GET_DISPLAY)
#error GET runtime requires native checkpoint, keyboard lease and display RPC
#endif
#include "get_runtime.h"
#include "get_checkpoint.h"
#include "resident_render.h"
#include "when_runtime.h"
#include "runtime.h"
/* Far static storage preserves the crowded ordinary data/stack group. There
 * are no borrowed callback contexts or destination pointers to free on abort. */
typedef struct {
 unsigned active,busy,keys,display,generation,completed,attribute,position,shape,configured;
 get_field_state field;
 unsigned char render[GET_FIELD_BUFFER];
} get_runtime_state;
typedef char get_runtime_layout[sizeof(get_runtime_state)==206?1:-1];
extern get_runtime_state __far runtime_get_field_storage;
#define held runtime_get_field_storage
static unsigned native_context(void)
{return runtime_get_native_active()==1 && held.generation==runtime_get_native_generation();}
static unsigned retired(void)
{return !(aspect_render_field_state()&(ASPECT_FIELD_OWNED|ASPECT_FIELD_WAIT));}
static unsigned paint(void)
{
 unsigned i,result;
 if(get_field_render(&held.field,held.render)==GET_FIELD_ARGUMENT)return ASPECT_RUN_STATE;
 result=aspect_render_field(1,(held.attribute<<8)|held.field.width);if(result)return result;
 for(i=0;i<held.field.width;++i){
  result=aspect_render_field(2,(i<<8)|held.render[i]);if(result)return result;
 }
 return aspect_render_field(3,(held.field.insert<<8)|held.field.cursor);
}
static unsigned release(unsigned error,unsigned unwind)
{
 unsigned result=0,other;
 if(held.display){
  result=aspect_render_field(5,error);
  if(!retired())return result?result:ASPECT_RUN_STATE;
  held.display=0;
 }
 if(held.keys){
  other=unwind?runtime_when_get_unwind():runtime_when_get_end();
  if(other)return result?result:other;
  held.keys=0;
 }
 held.active=0;
 held.completed=!error && !result && held.configured && held.field.phase==GET_FIELD_ACCEPT;
 if(!held.completed)held.field.cookie=0;
 return result;
}
unsigned runtime_get_anchor_begin(unsigned start)
{
 unsigned result,lo,hi;
 if(held.active || held.busy || held.completed || aspect_render_field_state())return ASPECT_RUN_STATE;
 if(runtime_get_native_active()!=1 || !runtime_get_native_generation())return ASPECT_RUN_STATE;
 if(!aspect_render_active())return ASPECT_RUN_UNSUPPORTED;
 held.position=65535U;held.generation=runtime_get_native_generation();held.completed=held.keys=held.display=held.configured=0;
 held.field.cookie=0;held.busy=1;
 result=runtime_when_get_begin();if(result){held.busy=0;return result;}
 held.active=held.keys=1;
 result=aspect_render_field(0,start);held.display=!retired();
 if(!result){
  lo=aspect_render_field(4,3);hi=aspect_render_field(4,4);
  if((lo&0xff00U)!=0xf000U || (hi&0xff00U)!=0xf000U)result=ASPECT_RUN_STATE;
  else held.shape=((hi&255)<<8)|(lo&255);
 }
 if(result)release(1,0);
 held.busy=0;return result;
}
unsigned runtime_get_anchor_active(void){return held.active && !held.configured;}
unsigned runtime_get_anchor_info(unsigned selector)
{
 if(!held.active || held.busy || !native_context())return ASPECT_RUN_STATE;
 if(selector>10)return ASPECT_RUN_OPERAND;
 return aspect_render_field(4,selector);
}
unsigned runtime_get_field_configure(unsigned attribute,unsigned width,unsigned numeric,unsigned masked,const unsigned char __far *initial)
{
 unsigned result;
 if(!held.active || held.configured || held.busy || !native_context())return ASPECT_RUN_STATE;
 if(!width || width>80 || attribute>255 || numeric>1 || masked>1)return ASPECT_RUN_OPERAND;
 held.busy=1;held.attribute=attribute;
 result=get_field_begin(&held.field,initial,width,numeric,masked,!(held.shape&0x2000),held.shape)==GET_FIELD_ACTIVE?0:ASPECT_RUN_OPERAND;
 if(!result){held.configured=1;result=paint();}
 if(result)release(1,0);
 held.busy=0;return result;
}
unsigned runtime_get_field_begin(unsigned start,unsigned attribute,unsigned width,unsigned numeric,unsigned masked,const unsigned char __far *initial)
{
 unsigned result;
 if(!width || width>80 || attribute>255 || numeric>1 || masked>1)return ASPECT_RUN_OPERAND;
 result=runtime_get_anchor_begin(start);if(result)return result;
 return runtime_get_field_configure(attribute,width,numeric,masked,initial);
}
unsigned runtime_get_field_phase(void)
{return (held.active && held.configured) || held.completed?held.field.phase:GET_FIELD_ARGUMENT;}
unsigned runtime_get_field_result(void)
{return ((held.active && held.configured) || held.completed) && held.field.phase!=GET_FIELD_ACTIVE?held.field.result:65535U;}
unsigned runtime_get_field_active(void){return held.active;}
unsigned runtime_get_field_poll(void)
{
 unsigned result,key,changed=0;
 if(!held.active || !held.configured || held.busy || !native_context() || held.field.phase!=GET_FIELD_ACTIVE)return ASPECT_RUN_STATE;
 held.busy=1;result=runtime_when_get_poll();
 if(!result && runtime_keyboard_peek()){
  key=runtime_keyboard_read();changed=1;result=get_field_key(&held.field,key);
  if(result==GET_FIELD_BELL){runtime_console_emit_byte(7);result=runtime_error;}
  else result=result==GET_FIELD_ARGUMENT?ASPECT_RUN_STATE:0;
 }
 if(!result && (changed || (aspect_render_field_state()&ASPECT_FIELD_DIRTY)))result=paint();
 held.busy=0;return result;
}
unsigned runtime_get_field_position(void)
{return native_context()?held.position:65535U;}
unsigned runtime_get_field_end(unsigned error)
{
 unsigned result,lo,hi;
 if(error>1)return ASPECT_RUN_OPERAND;
 if(!held.active || held.busy || !native_context() || (!error && (!held.configured || held.field.phase==GET_FIELD_ACTIVE)))return ASPECT_RUN_STATE;
 held.busy=1;
 if(!error){
  lo=aspect_render_field(4,9);hi=aspect_render_field(4,10);
  if((lo&0xff00U)!=0xf000U || (hi&0xff00U)!=0xf000U){held.busy=0;return ASPECT_RUN_STATE;}
  held.position=((hi&255)<<8)|(lo&255);
 }
 result=release(error,0);held.busy=0;return result;
}
unsigned runtime_get_field_commit(unsigned char __far *target)
{
 if(held.active || held.busy || !held.completed || !native_context())return ASPECT_RUN_STATE;
 if(get_field_commit(&held.field,target)!=GET_FIELD_ACCEPT)return ASPECT_RUN_OPERAND;
 held.completed=0;held.field.cookie=0;return 0;
}
unsigned runtime_get_field_discard(void)
{
 if(held.active || held.busy)return ASPECT_RUN_STATE;
 held.completed=0;held.field.cookie=0;return 0;
}
unsigned runtime_get_field_recover(void)
{
 unsigned result;
 if(!held.active && !held.completed)return 0;
 if(runtime_get_native_active() || !runtime_get_native_aborted() || held.generation!=runtime_get_native_generation())return ASPECT_RUN_STATE;
 /* The matched checkpoint has restored its caller; this busy frame is gone. */
 held.busy=1;
 result=release(1,1);held.busy=0;return result;
}
