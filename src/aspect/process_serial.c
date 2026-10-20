#include "process_serial.h"
#if !defined(ASPECT_EXTERNAL_PROCESS)
#error This component requires the suspended-phase serial API guards
#endif
extern unsigned __cdecl aspect_process_serial_detach(void);
extern unsigned __cdecl aspect_process_serial_restore(unsigned force);
extern unsigned __cdecl aspect_process_serial_clock_ready(void);
extern const unsigned aspect_process_serial_c_guards;
unsigned __cdecl aspect_process_serial_pause(void)
{
 unsigned status;
 if(aspect_process_serial_detached||aspect_serial_active==2)return ASPECT_SERIAL_BUSY;
 if(!aspect_serial_active)return 0;
 if(aspect_process_serial_c_guards!=1||aspect_process_serial_clock_ready())return ASPECT_SERIAL_STATE;
 status=aspect_serial_compile_pause();if(status)return status;
 status=aspect_process_serial_detach();
 if(status)aspect_serial_compile_resume();
 return status;
}
unsigned __cdecl aspect_process_serial_resume(void)
{
 unsigned status,flow;unsigned long start,now;
 if(!aspect_process_serial_detached)return 0;
 if(aspect_process_serial_clock_ready()){
  status=aspect_process_serial_restore(1);
  if(aspect_process_serial_detached)return status;
  /* IRQ0 cannot advance the BIOS deadline. Restore our port without waiting,
   * leave the unrelated PIC bit to its owner and report the invalid clock. */
  aspect_serial_status=ASPECT_SERIAL_STATE;aspect_serial_compile_resume();return ASPECT_SERIAL_STATE;
 }
 start=aspect_serial_ticks();
 do{
  status=aspect_process_serial_restore(0);if(status!=ASPECT_SERIAL_PENDING)break;
  now=aspect_serial_ticks();if(now<start)now+=1573040UL;
 }while(now-start<36UL);
 if(status==ASPECT_SERIAL_PENDING)status=aspect_process_serial_restore(1);
 /* A rejected IF0/state call retains ownership for a valid retry. Never
  * retire the flow token while hardware is still in the suspended phase. */
 if(aspect_process_serial_detached)return status;
 flow=aspect_serial_compile_resume();return status?status:flow;
}
