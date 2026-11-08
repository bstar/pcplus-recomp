#include <string.h>
#include "runtime.h"
#include "get_runtime.h"
#include "get_native_field.h"
extern unsigned __cdecl runtime_get_numeric_filter(void),runtime_get_string_filter(void);
extern void __cdecl runtime_get_field_abort(void);
static void fail(unsigned status)
{runtime_set_error(status);runtime_get_field_abort();}
unsigned __cdecl runtime_get_native_field(unsigned callback,unsigned masked,unsigned width,unsigned initial,unsigned output,unsigned attribute,unsigned start)
{
 unsigned status,numeric,result,phase,n;unsigned char text[GET_FIELD_BUFFER],seed[GET_FIELD_BUFFER];
 const unsigned char __far *source=0;
 if(callback==runtime_get_numeric_filter())numeric=1;
 else if(callback==runtime_get_string_filter())numeric=0;
 else {fail(ASPECT_RUN_OPERAND);return 65535U;}
 if(!output || (unsigned long)output+81UL>65536UL ||
    (initial && (unsigned long)initial+81UL>65536UL)){
  fail(ASPECT_RUN_OPERAND);return 65535U;
 }
 if(initial){
  for(n=0;n<81 && ((const unsigned char *)initial)[n];++n){}
  if(n==81){fail(ASPECT_RUN_OPERAND);return 65535U;}
  memcpy(seed,(const void *)initial,n+1);source=seed;
 }
 if(runtime_get_anchor_active()){
  n=runtime_get_anchor_info(0);status=runtime_get_anchor_info(1);
  if((n&0xff00U)!=0xf000U || (status&0xff00U)!=0xf000U || (((status&255)<<8)|(n&255))!=start){fail(ASPECT_RUN_STATE);return 65535U;}
  status=runtime_get_field_configure(attribute,width,numeric,masked,source);
 }else status=runtime_get_field_begin(start,attribute,width,numeric,masked,source);
 if(status){fail(status);return 65535U;}
 while(runtime_get_field_phase()==GET_FIELD_ACTIVE){
  status=runtime_get_field_poll();if(status){fail(status);return 65535U;}
 }
 phase=runtime_get_field_phase();result=runtime_get_field_result();
 status=runtime_get_field_end(0);if(status){fail(status);return 65535U;}
 if(phase==GET_FIELD_ACCEPT){
  status=runtime_get_field_commit(text);if(status){fail(status);return 65535U;}
  memcpy((void *)output,text,strlen((char *)text)+1);
 }
 return result;
}
