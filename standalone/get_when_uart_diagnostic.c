/* Actual WHEN lease + serviced field + BIOS/UART; native WHEN actions and
 * parent receive/render entry are modeled, not a full interpreter/parent. */
#include "runtime.h"
#include "when_runtime.h"
#include "serial.h"
#include "get_field.h"
#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
unsigned runtime_error,runtime_receive_pattern_count,runtime_wait_gate,runtime_receive_display;
unsigned runtime_when_disconnect_armed,runtime_when_case_sensitive,runtime_when_keyboard_disabled,runtime_when_last_key,runtime_when_pending_key;
unsigned char runtime_when_records[344];
static unsigned checks,attached,window,at,maximum,max_burst,leased,injected,fault,action;
static unsigned long polls,leads;
static unsigned char received[508],output[82];
static get_field_state field;
static void ck(unsigned yes)
{++checks;if(!yes){printf("GET FAIL %u at%u error%u\n",checks,at,runtime_error);exit(1);}}
void runtime_set_error(unsigned error){if(!runtime_error)runtime_error=error;}
unsigned runtime_serial_poll(void){return aspect_serial_poll();}
unsigned aspect_render_prepare(unsigned a,unsigned b,unsigned c){(void)a;(void)b;(void)c;return ASPECT_RUN_STATE;}
unsigned aspect_render_attach(void){return ASPECT_RUN_STATE;}
unsigned aspect_render_active(void){return attached&&aspect_serial_active==1;}
unsigned aspect_render_window_active(void){return window;}
unsigned aspect_render_window_service(void){return ASPECT_RUN_STATE;}
unsigned aspect_render_key(unsigned k){(void)k;return ASPECT_RUN_STATE;}
unsigned aspect_render_confirm(unsigned k){(void)k;return ASPECT_RUN_STATE;}
unsigned runtime_abort_confirm_native(void){return 0;}
unsigned runtime_receive_policy_byte(unsigned a,unsigned b){(void)a;(void)b;runtime_set_error(ASPECT_RUN_STATE);return 0;}
unsigned runtime_receive_character(unsigned display,unsigned capture)
{
 unsigned value;(void)display;(void)capture;
 ck(attached&&leased&&at<508&&runtime_when_transport_poll()==0);
 value=aspect_serial_read();received[at++]=(unsigned char)value;++leads;return value;
}
extern unsigned runtime_when_key_ready(void),runtime_when_read_key(void),runtime_when_confirm_abort(void);
extern void runtime_when_dispatch_key(unsigned);
unsigned runtime_when_native_service(void)
{
 unsigned key=runtime_keyboard_peek(),count=aspect_serial_available();++polls;
 if(count>maximum)maximum=count;
 ck(leased&&runtime_when_key_ready()==0&&runtime_keyboard_peek()==key);
 ck(runtime_when_get_begin()==ASPECT_RUN_STATE&&runtime_when_get_end()==ASPECT_RUN_STATE);
 ck(runtime_when_alarm_begin()==ASPECT_RUN_STATE&&runtime_when_alarm_end()==ASPECT_RUN_STATE);
 ck(runtime_when_transport_poll()==0&&runtime_keyboard_peek()==key);
 if(fault&&injected)runtime_set_error(ASPECT_RUN_IO);
 if(action==1)window=1;
 else if(action==2)runtime_when_defer_begin();
 else if(action==3)runtime_when_monitor_begin();
 else if(action==4)aspect_serial_active=2;
 action=0;
 return 0;
}
static unsigned inject(unsigned key)
{union REGS in,out;in.x.ax=0x0500;in.x.cx=key;int86(0x16,&in,&out);return out.h.al;}
static unsigned expired(unsigned long before)
{unsigned long now=aspect_serial_ticks();if(now<before)now+=1573040UL;return now-before>=90UL;}
static void send(unsigned byte)
{unsigned long before=aspect_serial_ticks();while(aspect_serial_try_write(byte)){ck(!expired(before));ck(!aspect_serial_poll());}}
static void begin(void){ck(runtime_when_get_begin()==0);leased=1;}
static void end(void){ck(runtime_when_get_end()==0);leased=0;}
static void gates(void)
{
 unsigned transition;
 ck(runtime_when_get_end()==ASPECT_RUN_STATE);
 runtime_when_defer_begin();ck(runtime_when_get_begin()==ASPECT_RUN_STATE);runtime_when_defer_end();
 runtime_when_monitor_begin();ck(runtime_when_get_begin()==ASPECT_RUN_STATE);runtime_when_monitor_end();
 window=1;ck(runtime_when_get_begin()==ASPECT_RUN_STATE);window=0;
 ck(runtime_when_alarm_begin()==0&&runtime_when_get_begin()==ASPECT_RUN_STATE&&runtime_when_get_end()==ASPECT_RUN_STATE&&runtime_when_alarm_end()==0);
 begin();ck(runtime_when_get_begin()==ASPECT_RUN_STATE&&runtime_when_alarm_begin()==ASPECT_RUN_STATE);
 ck(!inject(0x011b)&&!inject(0x3b00));ck(runtime_when_transport_poll()==0&&runtime_keyboard_peek()==0x011b);
 runtime_when_reset();ck(runtime_error==ASPECT_RUN_STATE&&runtime_keyboard_peek()==0x011b);runtime_error=0;
 runtime_when_file_reset();ck(runtime_error==ASPECT_RUN_STATE&&runtime_keyboard_peek()==0x011b);runtime_error=0;
 runtime_when_finish();ck(runtime_error==ASPECT_RUN_STATE&&runtime_keyboard_peek()==0x011b);runtime_error=0;
 ck(runtime_when_read_key()==0&&runtime_error==ASPECT_RUN_STATE&&runtime_keyboard_peek()==0x011b);runtime_error=0;
 runtime_when_dispatch_key(65);ck(runtime_error==ASPECT_RUN_STATE&&runtime_keyboard_peek()==0x011b);runtime_error=0;
 ck(runtime_when_confirm_abort()==1&&runtime_error==ASPECT_RUN_STATE&&runtime_keyboard_peek()==0x011b);runtime_error=0;
 runtime_when_defer_begin();ck(runtime_when_get_end()==ASPECT_RUN_STATE&&runtime_when_get_poll()==ASPECT_RUN_STATE);runtime_when_defer_end();runtime_error=0;
 runtime_when_monitor_begin();ck(runtime_when_get_end()==ASPECT_RUN_STATE&&runtime_when_get_poll()==ASPECT_RUN_STATE);runtime_when_monitor_end();runtime_error=0;
 window=1;ck(runtime_when_get_poll()==ASPECT_RUN_STATE);window=0;runtime_error=0;
 end();ck(runtime_keyboard_read()==27&&runtime_keyboard_read()==0x3b00&&!runtime_keyboard_peek());
 for(transition=1;transition<=4;++transition){
  begin();action=transition;
  ck(runtime_when_get_poll()==(transition==4?ASPECT_RUN_SERIAL:ASPECT_RUN_STATE));
  if(transition==1)window=0;
  else if(transition==2)runtime_when_defer_end();
  else if(transition==3)runtime_when_monitor_end();
  else aspect_serial_active=1;
  end();runtime_error=0;
 }
 /* State2 is a controlled admission fault, without changing UART registers. */
 begin();aspect_serial_active=2;ck(runtime_when_get_poll()==ASPECT_RUN_SERIAL);aspect_serial_active=1;end();runtime_error=0;
 ck(runtime_when_get_poll()==ASPECT_RUN_STATE);runtime_error=0;runtime_when_reset();
}
int main(int argc,char **argv)
{
 unsigned port,base,vector,pic,lcr,mcr,ier,dll,dlm,status,key,before,index=0,i,value;
 unsigned long started;FILE *file;void (__interrupt __far *old)(void);
 if(argc!=4)return 99;setvbuf(stdout,0,_IONBF,0);port=argv[1][2]-'0';attached=argv[3][0]=='E';fault=argv[2][0]=='F';
 base=port==1?0x3f8:0x2f8;vector=port==1?12:11;old=_dos_getvect(vector);pic=inp(0x21);lcr=inp(base+3);mcr=inp(base+4);
 outp(base+3,lcr&127);ier=inp(base+1);outp(base+3,lcr|128);dll=inp(base);dlm=inp(base+1);outp(base+3,lcr);
 runtime_when_reset();ck(runtime_when_get_begin()==ASPECT_RUN_SERIAL);while(runtime_keyboard_peek())runtime_keyboard_read();
 outp(base+4,mcr|1);ck(aspect_serial_open(argv[1])==0);gates();runtime_keyboard_mode=attached?0x10:0;
 ck(get_field_begin(&field,(const unsigned char __far *)0,10,0,0,1,0x0607)==GET_FIELD_ACTIVE);memset(output,0xa5,82);
 begin();send('R');started=aspect_serial_ticks();
 while(field.phase==GET_FIELD_ACTIVE){
  ck(!expired(started));before=at;status=runtime_when_get_poll();if(at-before>max_burst)max_burst=at-before;ck(at-before<=64);
  if(status){ck(fault&&injected&&status==ASPECT_RUN_IO&&runtime_keyboard_peek()==0x011b);break;}
  if(!injected && (attached?at:aspect_serial_available())==508){
   if(argv[2][0]=='A'){ck(!inject(0x0231)&&!inject(0x0332)&&!inject(0x1c0d));}
   else{if(argv[2][0]=='C')ck(!inject(0x0837));ck(!inject(0x011b));}
   ck(!inject(0x3b00));injected=1;
  }
  if(fault)continue;
  if(runtime_keyboard_peek()){
   key=runtime_keyboard_read();status=get_field_key(&field,key);ck(status!=GET_FIELD_ARGUMENT&&status!=GET_FIELD_BELL);
  }
 }
 ck(injected&&polls>0);end();
 if(fault){ck(field.phase==GET_FIELD_ACTIVE&&runtime_keyboard_read()==27);runtime_error=0;}
 else if(argv[2][0]=='A'){ck(field.phase==GET_FIELD_ACCEPT&&get_field_commit(&field,output)==GET_FIELD_ACCEPT&&!strcmp((char *)output,"12")&&output[3]==0xa5);}
 else ck(field.phase==GET_FIELD_CANCEL&&field.cursor==1&&get_field_commit(&field,output)==GET_FIELD_ARGUMENT);
 if(argv[2][0]!='A')for(i=0;i<82;++i)ck(output[i]==0xa5);
 ck(runtime_keyboard_peek()==0x3b00&&runtime_keyboard_read()==0x3b00&&!runtime_keyboard_peek());
 if(!attached){ck(!at&&!leads&&!max_burst&&aspect_serial_available()==508);while(aspect_serial_available())received[at++]=(unsigned char)aspect_serial_read();}
 else ck(leads==508&&max_burst>0&&max_burst<=64);
 ck(at==508&&!aspect_serial_available());for(i=0;i<512;++i){value=i&255;if(value==17||value==19)continue;ck(received[index++]==value);}
 ck(index==508);file=fopen("RX.BIN","wb");ck(file&&fwrite(received,1,508,file)==508&&fclose(file)==0);
 send('P');started=aspect_serial_ticks();while(aspect_serial_available()<6){ck(!expired(started)&&!aspect_serial_poll());}
 for(i=0;i<6;++i)ck(aspect_serial_read()=="READY!"[i]);send('F');
 ck(aspect_serial_close()==0&&_dos_getvect(vector)==old&&inp(0x21)==pic&&inp(base+4)==(mcr|1));
 outp(base+3,lcr&127);ck(inp(base+1)==ier);outp(base+3,lcr|128);ck(inp(base)==dll&&inp(base+1)==dlm);outp(base+3,lcr);outp(base+4,mcr);
 ck(inp(base+3)==lcr&&inp(base+4)==mcr);runtime_when_finish();ck(!runtime_error&&!leased);
 printf("GET UART COM%u %c %c %c %u checks %lu polls %lu receive %u burst\n",port,argv[1][12],argv[2][0],argv[3][0],checks,polls,leads,max_burst);return 0;
}
