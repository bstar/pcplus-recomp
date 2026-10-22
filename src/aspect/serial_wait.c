/* Maintained invocation policy; no UART, DOS, allocation or CRT calls here. */
#include "serial_runtime.h"
unsigned runtime_serial_tx_wait_ticks=30U*18U;
#if defined(NATIVE_PROGRAM_FAR)
#pragma code_seg("PROGRAMCODE")
unsigned __far runtime_serial_wait_configure(const char *text)
#else
unsigned runtime_serial_wait_configure(const char *text)
#endif
{
 unsigned i,value=0;
 if(!text){runtime_serial_tx_wait_ticks=30U*18U;return 0;}
 for(i=0;text[i];++i){
  if(i==4 || text[i]<'0' || text[i]>'9')return 1;
  value=value*10U+(unsigned)(text[i]-'0');
 }
 if(!i || !value || value>3600U)return 1;
 runtime_serial_tx_wait_ticks=value*18U;return 0;
}
