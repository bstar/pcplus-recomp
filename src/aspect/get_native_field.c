#include <string.h>
#include "runtime.h"
#include "get_runtime.h"
#include "get_native_field.h"
extern unsigned __cdecl runtime_get_numeric_filter(void),runtime_get_string_filter(void);
extern void __cdecl runtime_get_field_abort(void);
#ifdef ASPECT_GET_BANK
/* Keep bounded near copies inside the GET code bank. CRT headers declare
 * register-call functions even in a cdecl build; a near CRT call cannot cross
 * this bank's CS. DS=SS makes both stack spans ordinary near pointers. */
static void copy_text(unsigned char *to,const unsigned char *from,unsigned n)
{unsigned i;for(i=0;i<n;++i)to[i]=from[i];}
#else
#define copy_text(to,from,n) memcpy(to,from,n)
#endif
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
  copy_text(seed,(const unsigned char *)initial,n+1);source=seed;
 }
 if(runtime_get_anchor_active()){
  n=runtime_get_anchor_info(0);status=runtime_get_anchor_info(1);
  if((n&0xff00U)!=0xf000U || (status&0xff00U)!=0xf000U || (((status&255)<<8)|(n&255))!=start){fail(ASPECT_RUN_STATE);return 65535U;}
  status=runtime_get_field_configure(attribute,width,numeric,masked,source);
 }else {
#ifdef ASPECT_GET_BANK
  /* The full VM must reserve its anchor before operands; never create a
   * replacement lease after discovering a missing mandatory context. */
  status=ASPECT_RUN_STATE;
#else
  status=runtime_get_field_begin(start,attribute,width,numeric,masked,source);
#endif
 }
 if(status){fail(status);return 65535U;}
 while(runtime_get_field_phase()==GET_FIELD_ACTIVE){
  status=runtime_get_field_poll();if(status){fail(status);return 65535U;}
 }
 phase=runtime_get_field_phase();result=runtime_get_field_result();
 status=runtime_get_field_end(0);if(status){fail(status);return 65535U;}
 if(phase==GET_FIELD_ACCEPT){
  status=runtime_get_field_commit(text);if(status){fail(status);return 65535U;}
#ifdef ASPECT_GET_BANK
  for(n=0;n<81 && text[n];++n){}
  copy_text((unsigned char *)output,text,n+1);
#else
  memcpy((void *)output,text,strlen((char *)text)+1);
#endif
 }
 return result;
}
