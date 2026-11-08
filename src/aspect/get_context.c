#include "get_context.h"
#include "get_runtime.h"
#include "get_checkpoint.h"
#include "runtime.h"
unsigned runtime_get_row,runtime_get_column,runtime_get_attribute;
unsigned runtime_get_columns,runtime_get_rows,runtime_get_origin,runtime_get_wrap;
static unsigned policy_ready;
unsigned runtime_get_context_policy(unsigned wrap)
{
 if(runtime_get_native_active() || runtime_get_field_active())return ASPECT_RUN_STATE;
 policy_ready=0;if(wrap>1)return ASPECT_RUN_OPERAND;
 runtime_get_wrap=wrap;policy_ready=1;return 0;
}
unsigned __cdecl runtime_get_context_enter(void)
{
 unsigned result,i,values[7];static const unsigned selectors[7]={0,1,2,5,6,7,8};
 if(!policy_ready){runtime_set_error(ASPECT_RUN_STATE);return ASPECT_RUN_STATE;}
 policy_ready=0;
 result=runtime_get_anchor_begin(65535U);if(result){runtime_set_error(result);return result;}
 for(i=0;i<7;++i){
  values[i]=runtime_get_anchor_info(selectors[i]);
  if((values[i]&0xff00U)!=0xf000U){runtime_set_error(ASPECT_RUN_STATE);return ASPECT_RUN_STATE;}
  values[i]&=255;
 }
 if(!values[3] || !values[4] || values[0]>=values[3] || values[1]>=values[4]){
  runtime_set_error(ASPECT_RUN_STATE);return ASPECT_RUN_STATE;
 }
 runtime_get_column=values[0];runtime_get_row=values[1];runtime_get_attribute=values[2];
 runtime_get_columns=values[3];runtime_get_rows=values[4];runtime_get_origin=values[5]|(values[6]<<8);
 return 0;
}
unsigned __cdecl runtime_get_context_leave(void)
{
 unsigned status=0;
 /* Width0 never calls the editor: retire its invisible anchor explicitly. */
 if(runtime_get_anchor_active())status=runtime_get_field_end(1);
 else if(runtime_get_field_active())status=ASPECT_RUN_STATE;
 if(status)runtime_set_error(status);
 return status;
}
