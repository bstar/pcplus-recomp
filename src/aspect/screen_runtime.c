/* Wire adapters for the recovered local screen handlers. Compiled in the
 * handler's code bank; only declared FAR gates enter the resident client. */
#include "screen_runtime.h"
#include "runtime.h"
#ifdef ASPECT_SCREEN_PARENT
#include "resident_render.h"
#endif
extern void __far __cdecl screen_runtime_failure(unsigned);
static unsigned request(unsigned operation,unsigned value)
{
#ifdef ASPECT_SCREEN_PARENT
 return aspect_render_screen_scalar(operation,value);
#else
 (void)operation;(void)value;return ASPECT_RUN_UNSUPPORTED;
#endif
}
static void failed(unsigned result)
{
 /* The resident FAR gate runs the ordinary external/GET/alarm unwind chain.
  * The native near longjmp must never execute while CS is this far bank. */
 screen_runtime_failure(result && result<=ASPECT_RUN_SERIAL?result:ASPECT_RUN_STATE);
}
static void status(unsigned result)
{if(result)failed(result);}
void __cdecl runtime_screen_enter(void)
{
 unsigned staged[6],i,low,high;
 for(i=0;i<6;++i){
  low=request(32,i);
  if((low&0xff00U)!=0xf000U){failed(low);return;}
  high=request(32,i|0x100U);
  if((high&0xff00U)!=0xf000U){failed(high);return;}
  staged[i]=(low&255U)|((high&255U)<<8);
 }
 for(i=0;i<6;++i)runtime_screen_values[i]=staged[i];
}
static unsigned primitive(unsigned kind,unsigned count,const unsigned *args)
{
 unsigned i,result;
 status(request(33,kind));
 for(i=0;i<count;++i)status(request(34,args[i]));
 result=request(35,0);
 if(kind==5){
  if((result&0xff00U)!=0xf000U){failed(result);return 0;}
  return result&255U;
 }
 status(result);return 0;
}
void __cdecl runtime_screen_scroll(unsigned attr,unsigned bottom,unsigned top,unsigned count)
{unsigned args[4];args[0]=attr;args[1]=bottom;args[2]=top;args[3]=count;primitive(0,4,args);}
void __cdecl runtime_screen_box(unsigned attr,unsigned bottom,unsigned top)
{unsigned args[3];args[0]=attr;args[1]=bottom;args[2]=top;primitive(1,3,args);}
unsigned __cdecl runtime_screen_reset_attribute(void)
{primitive(2,1,runtime_screen_values);return runtime_screen_values[0];}
void __cdecl runtime_screen_clear(void){primitive(3,0,0);}
void __cdecl runtime_screen_locate(unsigned row,unsigned column)
{unsigned args[2];args[0]=row;args[1]=column;primitive(4,2,args);}
unsigned __cdecl runtime_screen_read(unsigned offset){return primitive(5,1,&offset);}
void __cdecl runtime_screen_write(unsigned offset,unsigned value)
{unsigned args[2];args[0]=offset;args[1]=value;primitive(6,2,args);}
void __cdecl runtime_screen_home(void){primitive(7,0,0);}
