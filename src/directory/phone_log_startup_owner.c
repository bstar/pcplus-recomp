/* Startup only: consume the frozen accepted image after configuration has
 * succeeded, never during a directory preview or settings preflight. */
#include "phone_log_startup.h"
#include "phone_log_queue.h"
#include "../terminal/session_baseline.h"
extern unsigned terminal_option_mask,process_psp;
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux process_psp "process_psp";
unsigned terminal_phone_log_startup_status=0;
unsigned __cdecl phone_log_startup_owner(void)
{
 prm_dos_image image;unsigned status;
 if(terminal_option_mask&16U){
  status=hook_baseline_copy(&image);
  if(status)status=PLS_BASELINE;
  else status=phone_log_startup_configure(image.bytes,sizeof(image.bytes),process_psp);
 }else{
  status=phone_log_queue_configure(0,0);
  if(status)status+=PLS_QUEUE_BASE;
 }
 terminal_phone_log_startup_status=status;
 return status;
}
