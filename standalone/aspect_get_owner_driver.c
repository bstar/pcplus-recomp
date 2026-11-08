/* GET owner composition against independent original observations.
 * UI and floating service are modeled; integer CRT/readers are recovered code. */
#include <stdio.h>
#include <string.h>
#include <setjmp.h>
#include <stdlib.h>
#include <malloc.h>
#include <dos.h>
#include "get_field.h"
#ifdef ASPECT_GET_SERVICED
#include "get_runtime.h"
#ifdef ASPECT_GET_CONTEXT
#include "get_context.h"
extern void owner_serviced_origin(unsigned);
#endif
extern void owner_serviced_prepare(void),owner_serviced_finish(void);
extern unsigned runtime_get_native_field_inner(unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned);
#define owner_field runtime_get_native_field
#endif
#ifdef ASPECT_GET_CHECKPOINT
#include "get_checkpoint.h"
extern void owner_abort_native(void),owner_checkpoint_foreign(unsigned);
extern unsigned owner_checkpoint_guards(void),owner_checkpoint_abi(void),owner_checkpoint_flags(void),owner_checkpoint_foreign_stack(void);
static unsigned checkpoint_fault;
#endif
extern void owner_call(void);
extern unsigned owner_numeric_filter(void),owner_string_filter(void);
extern unsigned owner_lookahead,owner_scratch_pointer,owner_row,owner_column,owner_attribute,owner_wrap,owner_rows,owner_columns,owner_origin,owner_failure,owner_keys_disabled,owner_float_pointer,owner_file,owner_frame;
extern unsigned owner_integer_a[10],owner_integer_b[128],owner_check_range,owner_exit_state,owner_pending_near,owner_string_pointer,owner_string_index;
extern unsigned long owner_longs[128],owner_globals[128],owner_pending_far;
extern unsigned char owner_float_result[8],owner_floats[1024],owner_strings[810],owner_string_scratch[891];
static unsigned char stream[16],scratch[82],frames[256],before[81],expected[81],opaque[8]={1,0x23,0x45,0x67,0x89,0xab,0xcd,0xef};
static unsigned key_words[128],key_count,key_index,confirm_value,field_calls,field_width,field_callback,bells,position,position_calls,float_calls,confirm_calls,cancel_calls,error_code;
#ifdef ASPECT_GET_SERVICED
unsigned owner_serviced_peek(void){return key_index<key_count?key_words[key_index]:0;}
unsigned owner_serviced_read(void){if(key_index==key_count)exit(35);return key_words[key_index++];}
void owner_serviced_error(unsigned value){error_code=value;}
#endif
static char float_text[82],expected_float[82];
static struct {unsigned char *pointer;int count;} synthetic_file;
#ifndef ASPECT_GET_SERVICED
static get_field_state field;
#endif
#ifndef ASPECT_GET_CHECKPOINT
static jmp_buf owner_jump;
#endif
void owner_error(unsigned code){error_code=code;
#ifdef ASPECT_GET_CHECKPOINT
 owner_abort_native();exit(31);
#else
 longjmp(owner_jump,1);
#endif
}
void owner_unexpected(void){owner_error(0xfffe);}
unsigned owner_read_byte(void)
{if(synthetic_file.count<=0)owner_unexpected();--synthetic_file.count;return *synthetic_file.pointer++;}
unsigned owner_read_word(void){unsigned lo=owner_read_byte();return lo|(owner_read_byte()<<8);}
unsigned owner_cursor(void){return position;}
void owner_position(unsigned row,unsigned column){
#ifdef ASPECT_GET_CHECKPOINT
 if(checkpoint_fault==2)owner_error(9);
#endif
 position=(row<<8)|column;++position_calls;}
unsigned owner_confirm(void){++confirm_calls;
#ifdef ASPECT_GET_CHECKPOINT
 if(checkpoint_fault==3)owner_error(9);
#endif
 return confirm_value;}
void owner_cancel(void){++cancel_calls;
#ifdef ASPECT_GET_CHECKPOINT
 owner_abort_native();exit(32);
#else
 longjmp(owner_jump,2);
#endif
}
void owner_bell(void){++bells;}
void owner_float(unsigned selector)
{
 if(selector!=5)owner_unexpected();++float_calls;
 strcpy(float_text,(char *)owner_float_pointer);memcpy(owner_float_result,opaque,8);
}
unsigned owner_field(unsigned callback,unsigned masked,unsigned width,unsigned initial,unsigned output,unsigned attribute,unsigned start)
{
 unsigned status;
#ifndef ASPECT_GET_SERVICED
 unsigned key;unsigned char text[82];
#endif
#ifdef ASPECT_GET_CHECKPOINT
 if(owner_checkpoint_foreign_stack() || runtime_get_native_active()!=1 || runtime_get_native()!=GET_NATIVE_BUSY || runtime_get_native_active()!=1)owner_unexpected();
#endif
#ifdef ASPECT_GET_CONTEXT
 if(runtime_get_context_policy(1)!=10)owner_unexpected();
#endif
 ++field_calls;field_width=width;field_callback=callback==owner_numeric_filter();
 if(attribute!=13 || callback!=(field_callback?owner_numeric_filter():owner_string_filter()) || initial)owner_unexpected();
#ifdef ASPECT_GET_SERVICED
 status=runtime_get_native_field_inner(callback,masked,width,initial,output,attribute,start);
 position=runtime_get_field_position();return status;
#else
 if(get_field_begin(&field,(const unsigned char __far *)0,width,field_callback,masked,1,0x0607))owner_unexpected();
 while(field.phase==GET_FIELD_ACTIVE){
#ifdef ASPECT_GET_CHECKPOINT
  if(checkpoint_fault==1 && key_index==1)owner_error(9);
#endif
  if(key_index==key_count)owner_unexpected();key=key_words[key_index++];
  status=get_field_key(&field,key);if(status==GET_FIELD_BELL)++bells;else if(status==GET_FIELD_ARGUMENT)owner_unexpected();
 }
 position=start+field.cursor;
 if(field.phase==GET_FIELD_ACCEPT){
  if(get_field_commit(&field,text)!=GET_FIELD_ACCEPT)owner_unexpected();strcpy((char *)output,(char *)text);
 }
 return field.result;
#endif
}
static unsigned word(FILE *f){unsigned value;if(fread(&value,2,1,f)!=1)exit(30);return value;}
static void bytes(FILE *f,void *buffer,unsigned count){if(fread(buffer,1,count,f)!=count)exit(30);}
static unsigned ds(void);
#pragma aux ds = "mov ax,ds" value [ax] modify [];
static unsigned ss(void);
#pragma aux ss = "mov ax,ss" value [ax] modify [];
static unsigned cs(void);
#pragma aux cs = "mov ax,cs" value [ax] modify [];
int main(void)
{
 FILE *f=fopen("CASES.BIN","rb");unsigned count,index,token,size,n,i,stream_size,expected_error,expected_return,expected_failure,expected_calls,expected_width,expected_numeric,expected_bells,expected_position_calls,expected_position,expected_confirm,expected_cancel,expected_float_calls,jump;
 unsigned char __far *far_string;void __far *destination;
 if(!f || ds()!=ss() || FP_SEG(get_field_key)==cs())return 1;far_string=_fmalloc(82);if(!far_string)return 2;
#ifdef ASPECT_GET_CHECKPOINT
 if(owner_checkpoint_guards() || runtime_get_native_active() || runtime_get_native_aborted())return 13;
#endif
 if(word(f)!=0x474f)return 3;count=word(f);
 for(index=0;index<count;++index){
  token=word(f);owner_row=word(f);owner_column=word(f);owner_wrap=word(f);owner_keys_disabled=word(f);confirm_value=word(f);
  stream_size=word(f);if(stream_size>16)return 4;bytes(f,stream,stream_size);
  key_count=word(f);if(key_count>128)return 5;for(i=0;i<key_count;++i)key_words[i]=word(f);
  size=word(f);if(size>81)return 6;bytes(f,before,size);bytes(f,expected,size);
  expected_error=word(f);expected_return=word(f);expected_failure=word(f);expected_calls=word(f);expected_width=word(f);expected_numeric=word(f);expected_bells=word(f);expected_position_calls=word(f);expected_position=word(f);expected_confirm=word(f);expected_cancel=word(f);expected_float_calls=word(f);
  n=word(f);if(n>81)return 7;bytes(f,expected_float,n);expected_float[n]=0;
  memset(owner_strings,0,810);memset(owner_integer_a,0,20);memset(owner_integer_b,0,256);memset(owner_longs,0,512);memset(owner_floats,0,1024);memset(owner_string_scratch,0,891);memset(frames,0,256);
  owner_lookahead=owner_failure=owner_origin=owner_exit_state=owner_pending_near=owner_string_index=owner_string_pointer=0;owner_pending_far=0;
  owner_attribute=13;owner_rows=25;owner_columns=80;owner_check_range=1;owner_frame=(unsigned)(frames+128);owner_scratch_pointer=(unsigned)scratch;
  memcpy(scratch,"123\0",4);memset(scratch+4,0xa5,78);owner_globals[0]=(unsigned long)far_string;
  if(token==100)destination=owner_strings;
  else if(token>=160)destination=frames+152;
  else if(token>=150)destination=frames+104;
  else if(token%10==0)destination=far_string;
  else if(token%10==1)destination=owner_integer_b;
  else if(token%10==2)destination=owner_longs;
  else destination=owner_floats;
  _fmemcpy(destination,before,size);
  synthetic_file.pointer=stream;synthetic_file.count=stream_size;owner_file=(unsigned)&synthetic_file;
  key_index=field_calls=field_width=field_callback=bells=position_calls=float_calls=confirm_calls=cancel_calls=error_code=0;position=(owner_row<<8)|owner_column;float_text[0]=0;
#ifdef ASPECT_GET_CHECKPOINT
#ifdef ASPECT_GET_SERVICED
  owner_serviced_prepare();
#ifdef ASPECT_GET_CONTEXT
  if(!index){
   if(runtime_get_context_policy(2)!=7)return 40;
   owner_call();
   if(!runtime_get_native_aborted() || error_code!=10 || synthetic_file.count!=stream_size || key_index || field_calls)return 41;
   owner_serviced_finish();error_code=0;owner_serviced_origin(52);owner_serviced_prepare();
   owner_call();owner_serviced_finish();
   if(runtime_get_native_aborted() || error_code || position!=0x0639 || _fmemcmp(destination,expected,size) || synthetic_file.count || key_index!=key_count)return 42;
   owner_serviced_origin(0);_fmemcpy(destination,before,size);
   synthetic_file.pointer=stream;synthetic_file.count=stream_size;key_index=field_calls=field_width=field_callback=bells=position_calls=float_calls=confirm_calls=cancel_calls=error_code=0;owner_lookahead=owner_failure=0;
   position=(owner_row<<8)|owner_column;owner_serviced_prepare();
  }
#endif
#endif
  if(runtime_get_native_active())return 11;
  owner_checkpoint_foreign(index&3);owner_call();jump=runtime_get_native_aborted();
#ifdef ASPECT_GET_SERVICED
  if(jump && runtime_get_field_recover()){printf("FAIL serviced cleanup %u\n",index);return 36;}
  owner_serviced_finish();
#ifdef ASPECT_GET_CONTEXT
  if(owner_row==23 && !owner_wrap)expected_width=5;
  if(owner_row>=24 || (owner_row==23 && owner_wrap)){
#else
  if(owner_row>=23){
#endif
   if(error_code!=7 || !jump || key_index || position_calls || _fmemcmp(destination,before,size) || synthetic_file.count!=
#ifdef ASPECT_GET_CONTEXT
     (owner_row>=24?stream_size:0)
#else
     0
#endif
    ){printf("FAIL serviced view %u err%u jump%u key%u pos%u file%u\n",index,error_code,jump,key_index,position_calls,synthetic_file.count);return 37;}
   continue;
  }
#endif
  if(owner_checkpoint_abi() || (owner_checkpoint_flags()&0x0600)!=0x0200){printf("FAIL native ABI %u ABI%u flags%u\n",index,owner_checkpoint_abi(),owner_checkpoint_flags());return 14;}
  if(runtime_get_native_active())return 12;
#else
  jump=setjmp(owner_jump);if(!jump)owner_call();
#endif
  if(error_code!=expected_error || (!jump)!=expected_return || owner_failure!=expected_failure || field_calls!=expected_calls || (field_calls && (field_width!=expected_width || field_callback!=expected_numeric)) || bells!=expected_bells || position_calls!=expected_position_calls || (position_calls && position!=expected_position) || confirm_calls!=expected_confirm || cancel_calls!=expected_cancel || float_calls!=expected_float_calls || strcmp(float_text,expected_float) || _fmemcmp(destination,expected,size) || ds()!=ss()){
   printf("FAIL owner %u err=%u/%u return=%u/%u failure=%u/%u field=%u/%u width=%u/%u bells=%u/%u\r\n",index,error_code,expected_error,!jump,expected_return,owner_failure,expected_failure,field_calls,expected_calls,field_width,expected_width,bells,expected_bells);return 8;
  }
  if(synthetic_file.count || key_index!=key_count)return 9;
 }
 if(fgetc(f)!=EOF || fclose(f))return 10;_ffree(far_string);
#ifdef ASPECT_GET_CHECKPOINT
#ifndef ASPECT_GET_SERVICED
 /* Authored faults inside the field, after field acceptance before typed
  * conversion, and inside abort confirmation. Destination cannot be committed
  * by an abandoned owner, even if its scratch field accepted first. */
 for(index=1;index<=3;++index)for(n=0;n<4;++n){
  checkpoint_fault=index;owner_checkpoint_foreign(n);
  stream[0]=141;stream[1]=0;stream[2]=1;stream[3]=171;stream[4]=10;stream[5]=0;
  synthetic_file.pointer=stream;synthetic_file.count=6;
  owner_row=5;owner_column=0;owner_origin=owner_lookahead=owner_failure=owner_exit_state=owner_keys_disabled=0;
  key_words[0]=index==3?27:'4';key_words[1]='2';key_words[2]=13;
  key_count=index==3?1:3;key_index=0;confirm_value=1;error_code=0;
  owner_integer_b[0]=0xbeef;strcpy((char *)scratch,"123");
  owner_call();
  if(error_code!=9 || runtime_get_native_aborted()!=1 || runtime_get_native_active() || owner_integer_b[0]!=0xbeef || owner_checkpoint_abi() || (owner_checkpoint_flags()&0x0600)!=0x0200){printf("FAIL checkpoint fault %u mode%u err%u aborted%u active%u dest%u ABI%u flags%u\n",index,n,error_code,runtime_get_native_aborted(),runtime_get_native_active(),owner_integer_b[0],owner_checkpoint_abi(),owner_checkpoint_flags());return 15;}
  if(field.phase!=(index==1?GET_FIELD_ACTIVE:index==2?GET_FIELD_ACCEPT:GET_FIELD_CANCEL)){printf("FAIL checkpoint phase %u mode%u phase%u\n",index,n,field.phase);return 16;}
  if(index==2 && strcmp((char *)scratch,"42")){printf("FAIL checkpoint scratch %s\n",scratch);return 17;}
  /* Same process is reusable after every restored native stack. */
  checkpoint_fault=0;synthetic_file.pointer=stream;synthetic_file.count=6;
  key_words[0]='4';key_count=3;key_index=error_code=0;owner_lookahead=0;
  owner_call();
  if(error_code || runtime_get_native_aborted() || runtime_get_native_active() || owner_integer_b[0]!=42 || owner_checkpoint_abi() || (owner_checkpoint_flags()&0x0600)!=0x0200){printf("FAIL checkpoint retry %u mode%u err%u aborted%u active%u dest%u ABI%u flags%u\n",index,n,error_code,runtime_get_native_aborted(),runtime_get_native_active(),owner_integer_b[0],owner_checkpoint_abi(),owner_checkpoint_flags());return 18;}
 }
#endif
#ifdef ASPECT_GET_SERVICED
#ifdef ASPECT_GET_CONTEXT
 printf("PASS CONTEXT GET OWNER 142 cases;137 native matches;1 view-rebased clip;4 protected-view refusals; shared scratch; origin52\r\n");return 0;
#else
 printf("PASS SERVICED GET OWNER %u cases;137 native matches;5 protected-view refusals; actual field/WHEN/client; opaque float boundary\r\n",count);return 0;
#endif
#else
 printf("PASS GET CHECKPOINT %u cases;12 injected faults/retries; recovered owner/readers/integer CRT; native abort restored DS=SS\r\n",count);return 0;
#endif
#else
 printf("PASS GET OWNER %u cases; recovered readers/field/integer CRT; opaque float boundary; DS=SS\r\n",count);return 0;
#endif
}
