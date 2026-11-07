/* Exercise the actual WHEN C ownership gates around real BIOS/UART/PIT I/O.
 * Native WHEN action bodies and resident renderer are modeled here; this is
 * not VM/parent acceptance. The included diagnostic owns the independent wire. */
#define alarm_dos_run leased_run
#define alarm_dos_recover leased_recover
#define main io_main
#include "alarm_dos_uart_diagnostic.c"
#undef main
#undef alarm_dos_run
#undef alarm_dos_recover
#include "runtime.h"
extern unsigned __cdecl alarm_dos_run(unsigned,unsigned,unsigned long,
 unsigned (__cdecl *)(void *),void *);
extern unsigned __cdecl alarm_dos_recover(void);
unsigned runtime_error,runtime_receive_pattern_count,runtime_wait_gate;
unsigned runtime_receive_display,runtime_when_disconnect_armed,runtime_when_case_sensitive;
unsigned runtime_when_keyboard_disabled,runtime_when_last_key,runtime_when_pending_key;
unsigned char runtime_when_records[344];
static unsigned leased,model_attached,max_burst;
static unsigned long receive_leads;
static unsigned long native_polls,transport_polls;
static unsigned (__cdecl *io_service)(void *);
static void *io_cookie;
void runtime_set_error(unsigned error){if(!runtime_error)runtime_error=error;}
unsigned runtime_serial_poll(void){return aspect_serial_poll();}
unsigned aspect_render_prepare(unsigned a,unsigned b,unsigned c)
{(void)a;(void)b;(void)c;return ASPECT_RUN_STATE;}
unsigned aspect_render_attach(void){return ASPECT_RUN_STATE;}
unsigned aspect_render_active(void){return model_attached&&aspect_serial_active==1;}
unsigned aspect_render_window_active(void){return 0;}
unsigned aspect_render_window_service(void){return ASPECT_RUN_STATE;}
unsigned aspect_render_key(unsigned key){(void)key;return ASPECT_RUN_STATE;}
unsigned aspect_render_confirm(unsigned kind){(void)kind;return ASPECT_RUN_STATE;}
unsigned runtime_abort_confirm_native(void){return 0;}
unsigned runtime_receive_character(unsigned display,unsigned capture)
{
 unsigned byte,count;(void)display;(void)capture;
 /* Model only the renderer/receive entry. The real UART supplies each byte;
  * native translation, WHEN actions and parent parser are not linked here. */
 if(!model_attached || at>=508 || runtime_when_transport_poll()){
  runtime_set_error(ASPECT_RUN_STATE);return 0;
 }
 count=aspect_serial_available();if(count>maximum)maximum=count;
 byte=aspect_serial_read();received[at++]=(unsigned char)byte;++receive_leads;return byte;
}
unsigned runtime_receive_policy_byte(unsigned display,unsigned capture)
{(void)display;(void)capture;runtime_set_error(ASPECT_RUN_STATE);return 0;}
extern unsigned runtime_when_key_ready(void);
unsigned runtime_when_native_service(void)
{
 unsigned key=runtime_keyboard_peek();++native_polls;
 if(runtime_when_key_ready()!=0 || runtime_keyboard_peek()!=key ||
    runtime_when_alarm_begin()!=ASPECT_RUN_STATE || runtime_when_alarm_end()!=ASPECT_RUN_STATE)ck(0);
 ++transport_polls;if(runtime_when_transport_poll()!=0 || runtime_keyboard_peek()!=key)ck(0);
 return 0;
}
static unsigned __cdecl leased_service(void *unused)
{
 unsigned result,before=at,burst;(void)unused;result=runtime_when_alarm_poll();
 burst=at-before;if(burst>max_burst)max_burst=burst;
 if(burst>64 || (!model_attached&&burst))ck(0);
 if(result)return result;
 return io_service(io_cookie);
}
unsigned __cdecl leased_run(unsigned duration,unsigned enabled,unsigned long polls,
 unsigned (__cdecl *callback)(void *),void *cookie)
{
 unsigned result;
 ck(!leased&&runtime_when_alarm_begin()==0);leased=1;
 ck(runtime_when_alarm_begin()==ASPECT_RUN_STATE);
 io_service=callback;io_cookie=cookie;
 result=alarm_dos_run(duration,enabled,polls,leased_service,0);
 if(!alarm_dos_active()){ck(runtime_when_alarm_end()==0);leased=0;}
 return result;
}
unsigned __cdecl leased_recover(void)
{
 unsigned result=alarm_dos_recover();
 if(leased&&!alarm_dos_active()){ck(runtime_when_alarm_end()==0);leased=0;}
 return result;
}
int main(int argc,char **argv)
{
 int status;FILE *record;
 model_attached=argc==4&&argv[3][0]=='E';
 runtime_when_reset();ck(runtime_when_alarm_end()==ASPECT_RUN_STATE);
 runtime_when_defer_begin();ck(runtime_when_alarm_begin()==ASPECT_RUN_STATE);runtime_when_defer_end();
 runtime_when_monitor_begin();ck(runtime_when_alarm_begin()==ASPECT_RUN_STATE);runtime_when_monitor_end();
 status=io_main(argc,argv);
 ck(!leased&&runtime_error==0&&native_polls>0&&native_polls==transport_polls);
 ck(runtime_when_alarm_end()==ASPECT_RUN_STATE);
 if(model_attached)ck(receive_leads>0&&max_burst>0&&max_burst<=64);
 else ck(receive_leads==0&&max_burst==0);
 record=fopen("WHEN.TXT","w");ck(record!=0);
 fprintf(record,"WHEN %u %lu %lu %u\n",model_attached,native_polls,receive_leads,max_burst);ck(fclose(record)==0);
 return status;
}
