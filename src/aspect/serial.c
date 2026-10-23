/* Fixed grammar; hardware ownership lives in serial_backend.asm. */
#include "serial.h"
#include "serial_handoff.h"
#include <dos.h>
#ifdef ASPECT_REGISTER_HANDOFF
#include "register_handoff.h"
#define REGISTER_VERSION(v) ((v)==ASIO_VERSION_REGISTERS)
#define REGISTER_OR(v) || REGISTER_VERSION(v)
#define REGISTER_AND_NOT(v) && !REGISTER_VERSION(v)
#define REGISTER_SIZE(v) REGISTER_VERSION(v)?ASIO_V7_SIZE:
#else
#define REGISTER_OR(v)
#define REGISTER_AND_NOT(v)
#define REGISTER_SIZE(v)
#endif
extern unsigned char uart_rx_buffer[];
extern unsigned uart_rx_read,uart_rx_write,uart_rx_count;
extern unsigned uart_software_flow,uart_rx_mask,uart_tx_paused;
extern unsigned serial_carrier_policy;
extern unsigned char uart_flow_pending;
extern unsigned aspect_serial_handoff_enabled;
extern unsigned __cdecl aspect_serial_backend_close(void);
extern unsigned __cdecl aspect_serial_psp(void);
extern unsigned __cdecl aspect_serial_tx_empty(void);
extern unsigned __cdecl aspect_serial_flow_alive(void);
extern unsigned __cdecl aspect_serial_compile_hold(void);
extern unsigned __cdecl aspect_serial_compile_release(void);
#if defined(ASPECT_RUNTIME_SERIAL)
extern unsigned __cdecl aspect_render_prepare(unsigned,unsigned,unsigned);
extern unsigned __cdecl aspect_render_attach(void);
#endif
static aspect_serial_handoff __far *handoff;
static unsigned char input_translation[256];
static unsigned compile_pause_owned;
#if defined(ASPECT_EXTERNAL_PROCESS)
const unsigned aspect_process_serial_c_guards=1;
#endif
static unsigned input_translation_mode;
static unsigned char directory_record[114];
static unsigned directory_entry;
static unsigned char __far *preload_source;
static unsigned preload_count,preload_read;
static unsigned preload_flow,preload_carrier_policy;
extern unsigned __cdecl directory_accounting_patch(const unsigned char *,unsigned char *,unsigned,unsigned,unsigned,unsigned);
static unsigned record_bounded(const unsigned char __far *p)
{
 static const unsigned offsets[]={0,25,52,61,75,86,95,105};
 static const unsigned sizes[]={25,21,9,9,11,9,9,9};
 unsigned i,j;
 for(i=0;i<8;++i){
  for(j=0;j<sizes[i];++j)if(!p[offsets[i]+j])break;
  if(j==sizes[i])return 0;
 }
 return 1;
}
unsigned __cdecl aspect_serial_directory_entry(void)
{return directory_entry;}
const unsigned char * __cdecl aspect_serial_directory_record(void)
{return directory_entry?directory_record:0;}
/* Internal backend callback: its UART IRQ is masked/IER0, queue already reset.
 * Copy first, publish queue fields, then backend may enable its actual ISR. */
void __cdecl aspect_serial_preload(void)
{
 unsigned i,at=preload_read;
 for(i=0;i<preload_count;++i){uart_rx_buffer[i]=preload_source[at];at=(at+1)&4095;}
 uart_rx_read=(unsigned)uart_rx_buffer;
 uart_rx_write=(unsigned)uart_rx_buffer+(preload_count&4095);
 uart_rx_count=preload_count;
 uart_rx_mask=input_translation_mode==ASIO_XLT_MASK7F?127U:255U;
 uart_tx_paused=preload_flow;
 serial_carrier_policy=preload_carrier_policy;
}
unsigned __cdecl aspect_serial_translate(unsigned byte)
{return input_translation_mode==ASIO_XLT_TABLE?input_translation[byte&255U]:(byte&255U);}
unsigned __cdecl aspect_serial_translation_policy(void)
{return input_translation_mode;}
extern unsigned __cdecl aspect_serial_backend_open(unsigned,unsigned,unsigned,unsigned);
static unsigned hex(unsigned c)
{if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;return 65535U;}
unsigned __cdecl aspect_serial_open(const char *p)
{
 unsigned i,v,divisor=0,lcr=0,flow,segment=0,offset=0,status,parent;
 unsigned long begin,end,address,ring,table=0,record_address=0;
 unsigned mode=0,table_offset=0,guard,descriptor_size=ASIO_SIZE;
 unsigned initial_count=0,initial_read=0,entry=0,record_offset=0;
 unsigned year=0,month=0,day=0,delta=0;
 unsigned render_offset=0,render_segment=0,render_token=0,has_render=0;
 unsigned flow_flags=0;
#ifdef ASPECT_REGISTER_HANDOFF
 unsigned long render_address=0;
#else
 unsigned long render_address;
#endif
 unsigned char __far *mcb;
 aspect_serial_handoff __far *candidate=0;
#if defined(ASPECT_EXTERNAL_PROCESS)
 if(aspect_serial_active==2)return ASPECT_SERIAL_BUSY;
#endif
 if(!p || (unsigned long)(unsigned)p+14UL>65536UL)return ASPECT_SERIAL_ARGUMENT;
 if(p[0]!='/' || (p[1]!='S'&&p[1]!='s') || p[2]<'1'||p[2]>'4'||p[3]!=':'||p[8]!=':'||p[11]!=':' )return ASPECT_SERIAL_ARGUMENT;
 for(i=4;i<8;++i){v=hex((unsigned char)p[i]);if(v>15)return ASPECT_SERIAL_ARGUMENT;divisor=divisor*16+v;}
 for(i=9;i<11;++i){v=hex((unsigned char)p[i]);if(v>15)return ASPECT_SERIAL_ARGUMENT;lcr=lcr*16+v;}
 if(!divisor || (lcr&192) || ((lcr&3)!=2 && (lcr&3)!=3))return ASPECT_SERIAL_ARGUMENT;
 if(p[13]){
  if((unsigned long)(unsigned)p+24UL>65536UL || p[13]!=':' || p[18]!=':' || p[23])return ASPECT_SERIAL_ARGUMENT;
  for(i=14;i<18;++i){v=hex((unsigned char)p[i]);if(v>15)return ASPECT_SERIAL_ARGUMENT;segment=segment*16+v;}
  for(i=19;i<23;++i){v=hex((unsigned char)p[i]);if(v>15)return ASPECT_SERIAL_ARGUMENT;offset=offset*16+v;}
  address=(unsigned long)segment*16UL+offset;
  if((unsigned long)offset+ASIO_SIZE>65536UL || address+ASIO_SIZE>1048576UL)return ASPECT_SERIAL_ARGUMENT;
  parent=*(unsigned __far *)MK_FP(aspect_serial_psp(),0x16);
  if(!parent)return ASPECT_SERIAL_ARGUMENT;
  mcb=(unsigned char __far *)MK_FP(parent-1,0);
  if((mcb[0]!='M'&&mcb[0]!='Z') || *(unsigned __far *)(mcb+1)!=parent)return ASPECT_SERIAL_ARGUMENT;
  begin=(unsigned long)parent*16UL;
  end=begin+(unsigned long)*(unsigned __far *)(mcb+3)*16UL;
  if(end>1048576UL || address<begin || address+ASIO_SIZE>end)return ASPECT_SERIAL_ARGUMENT;
  candidate=(aspect_serial_handoff __far *)MK_FP(segment,offset);
  if(candidate->version==ASIO_VERSION_PRELOAD || candidate->version==ASIO_VERSION_RENDER || candidate->version==ASIO_VERSION_FLOW || candidate->version==ASIO_VERSION_CARRIER REGISTER_OR(candidate->version)){
   descriptor_size=REGISTER_SIZE(candidate->version)candidate->version==ASIO_VERSION_CARRIER?ASIO_V6_SIZE:candidate->version==ASIO_VERSION_FLOW?ASIO_V5_SIZE:candidate->version==ASIO_VERSION_RENDER?ASIO_V4_SIZE:ASIO_V3_SIZE;
   if((unsigned long)offset+descriptor_size>65536UL || address+descriptor_size>end)return ASPECT_SERIAL_ARGUMENT;
  }
  if(candidate->magic!=ASIO_MAGIC || (candidate->version!=ASIO_VERSION && candidate->version!=ASIO_VERSION_TRANSLATION && candidate->version!=ASIO_VERSION_PRELOAD && candidate->version!=ASIO_VERSION_RENDER && candidate->version!=ASIO_VERSION_FLOW && candidate->version!=ASIO_VERSION_CARRIER REGISTER_AND_NOT(candidate->version)) || candidate->size!=descriptor_size ||
   candidate->parent_psp!=parent || !candidate->parent_psp ||
   candidate->capacity!=4096 || candidate->returned ||
   (unsigned long)candidate->ring+4096UL>65536UL)return ASPECT_SERIAL_ARGUMENT;
  guard=candidate->parent_psp^candidate->parent_ds^candidate->ring^ASIO_GUARD;
  if(candidate->version==ASIO_VERSION_PRELOAD || candidate->version==ASIO_VERSION_RENDER || candidate->version==ASIO_VERSION_FLOW || candidate->version==ASIO_VERSION_CARRIER REGISTER_OR(candidate->version)){
   aspect_serial_handoff_v3 __far *v3=(aspect_serial_handoff_v3 __far *)candidate;
   initial_count=candidate->count;initial_read=candidate->status;entry=v3->entry;record_offset=v3->record;
   year=v3->year;month=v3->month;day=v3->day;delta=v3->delta;
   if(initial_count>4096 || initial_read>4095 || (!initial_count && initial_read) ||
      entry>200 || (!entry && record_offset) || (!year && (month||day||delta)) ||
      (year && !entry))return ASPECT_SERIAL_ARGUMENT;
   guard^=initial_count^initial_read^entry^record_offset;
   guard^=year^month^day^delta;
  }else if(candidate->count || candidate->status)return ASPECT_SERIAL_ARGUMENT;
  if(candidate->version==ASIO_VERSION_RENDER || candidate->version==ASIO_VERSION_FLOW || candidate->version==ASIO_VERSION_CARRIER REGISTER_OR(candidate->version)){
   aspect_serial_handoff_v4 __far *v4=(aspect_serial_handoff_v4 __far *)candidate;
   render_offset=v4->render_offset;render_segment=v4->render_segment;render_token=v4->render_token;has_render=1;
   if(!render_token || v4->render_version!=ASPECT_RENDER_CAP_VERSION)return ASPECT_SERIAL_ARGUMENT;
   guard^=render_offset^render_segment^render_token^v4->render_version;
  }
  if(candidate->version==ASIO_VERSION_FLOW || candidate->version==ASIO_VERSION_CARRIER REGISTER_OR(candidate->version)){
   flow_flags=((aspect_serial_handoff_v5 __far *)candidate)->flow_flags;
#ifdef ASPECT_REGISTER_HANDOFF
   if(flow_flags>((candidate->version==ASIO_VERSION_CARRIER || REGISTER_VERSION(candidate->version))?3U:1U))return ASPECT_SERIAL_ARGUMENT;
#else
   if(flow_flags>(candidate->version==ASIO_VERSION_CARRIER?3U:1U))return ASPECT_SERIAL_ARGUMENT;
#endif
   guard^=flow_flags;
  }
#ifdef ASPECT_REGISTER_HANDOFF
  if(REGISTER_VERSION(candidate->version)){
   aspect_serial_handoff_v7 __far *v7=(aspect_serial_handoff_v7 __far *)candidate;
   guard^=v7->register_offset^v7->register_segment^v7->register_bytes^v7->register_token;
  }
#endif
  if(candidate->version==ASIO_VERSION){
   if(candidate->reserved0 || candidate->reserved1)return ASPECT_SERIAL_ARGUMENT;
  }else{
   table_offset=candidate->reserved0;mode=candidate->reserved1;
   if(mode>ASIO_XLT_MASK7F || (mode!=ASIO_XLT_TABLE && table_offset))return ASPECT_SERIAL_ARGUMENT;
   guard^=table_offset^mode;
  }
  if(candidate->guard!=guard)return ASPECT_SERIAL_ARGUMENT;
  ring=(unsigned long)candidate->parent_ds*16UL+candidate->ring;
  if(end>1048576UL || address<begin || address+descriptor_size>end || ring<begin || ring+4096UL>end ||
    (address<ring+4096UL && ring<address+descriptor_size))return ASPECT_SERIAL_ARGUMENT;
  if(mode==ASIO_XLT_TABLE){
   table=(unsigned long)candidate->parent_ds*16UL+table_offset;
   if((unsigned long)table_offset+256UL>65536UL || table<begin || table+256UL>end ||
      table+256UL>1048576UL || (table<address+descriptor_size && address<table+256UL) ||
      (table<ring+4096UL && ring<table+256UL))return ASPECT_SERIAL_ARGUMENT;
  }
  if(entry){
   record_address=(unsigned long)candidate->parent_ds*16UL+record_offset;
   if(!record_offset || (unsigned long)record_offset+114UL>65536UL || record_address<begin ||
      record_address+114UL>end || record_address+114UL>1048576UL ||
      (record_address<address+descriptor_size && address<record_address+114UL) ||
      (record_address<ring+4096UL && ring<record_address+114UL) ||
      (mode==ASIO_XLT_TABLE && record_address<table+256UL && table<record_address+114UL))return ASPECT_SERIAL_ARGUMENT;
   if(!record_bounded((unsigned char __far *)MK_FP(candidate->parent_ds,record_offset)))return ASPECT_SERIAL_ARGUMENT;
  }
  if(has_render){
   render_address=(unsigned long)render_segment*16UL+render_offset;
   if(render_address<begin || render_address>=end || render_address>=1048576UL ||
      (render_address>=address && render_address<address+descriptor_size) ||
      (render_address>=ring && render_address<ring+4096UL) ||
      (mode==ASIO_XLT_TABLE && render_address>=table && render_address<table+256UL) ||
      (entry && render_address>=record_address && render_address<record_address+114UL))return ASPECT_SERIAL_ARGUMENT;
#if !defined(ASPECT_RUNTIME_SERIAL)
   return ASPECT_SERIAL_ARGUMENT; /* Unit UART-only build has no render capability. */
#endif
  }
#ifdef ASPECT_REGISTER_HANDOFF
  if(REGISTER_VERSION(candidate->version) && aspect_register_validate((aspect_serial_handoff_v7 __far *)candidate,
   begin,end,ring,table,record_address,render_address))return ASPECT_SERIAL_ARGUMENT;
#endif
 }
 flow=(unsigned char)p[12];if(flow>='a'&&flow<='z')flow-=32;
 if(flow!='N'&&flow!='S'&&flow!='H'&&flow!='B')return ASPECT_SERIAL_ARGUMENT;
 if((flow_flags&1) && flow!='S' && flow!='B')return ASPECT_SERIAL_ARGUMENT;
 /* Rejected reopen must not change an active owner's effective table. */
 if(aspect_serial_active)return ASPECT_SERIAL_BUSY;
#if defined(ASPECT_RUNTIME_SERIAL)
 if(aspect_render_active())return ASPECT_SERIAL_BUSY;
 if(has_render && aspect_render_prepare(render_offset,render_segment,render_token))return ASPECT_SERIAL_ARGUMENT;
#endif
 for(i=0;i<256;++i)input_translation[i]=mode==ASIO_XLT_TABLE?
  *(unsigned char __far *)MK_FP(candidate->parent_ds,table_offset+i):
  (unsigned char)i;
 input_translation_mode=mode;
 directory_entry=entry;
 for(i=0;i<114;++i)directory_record[i]=entry?
  *(unsigned char __far *)MK_FP(candidate->parent_ds,record_offset+i):0;
 if(year && directory_accounting_patch(directory_record,directory_record,year,month,day,delta))return ASPECT_SERIAL_ARGUMENT;
 preload_count=initial_count;preload_read=initial_read;
 preload_flow=flow_flags&1;preload_carrier_policy=flow_flags&2;
 preload_source=candidate?(unsigned char __far *)MK_FP(candidate->parent_ds,candidate->ring):0;
 status=aspect_serial_backend_open(p[2]-'1',divisor,lcr,flow);
 if(!status){
  compile_pause_owned=0;
  handoff=candidate;aspect_serial_handoff_enabled=candidate!=0;
#ifdef ASPECT_REGISTER_HANDOFF
  aspect_register_attach(candidate && REGISTER_VERSION(candidate->version)?(aspect_serial_handoff_v7 __far *)candidate:0);
#endif
#if defined(ASPECT_RUNTIME_SERIAL)
  if(has_render && aspect_render_attach()){
   aspect_serial_status=ASPECT_SERIAL_STATE;
   aspect_serial_close();return ASPECT_SERIAL_STATE;
  }
#endif
 }
 return status;
}

unsigned __cdecl aspect_serial_close(void)
{
 unsigned status,n,at,count;
 unsigned char __far *destination;
 unsigned long start,now;
#if defined(ASPECT_EXTERNAL_PROCESS)
 if(aspect_serial_active==2)return ASPECT_SERIAL_BUSY;
#endif
 if(!aspect_serial_active)return aspect_serial_status;
 /* Release owned BREAK before attempting the final flow-control drain. */
 aspect_serial_break_release();
 /* Stop upstream before taking the child ISR down. Control flow bypasses
  * peer CTS/XOFF. Advisory36tick bound never repeats accepted data bytes. */
 if(uart_software_flow && aspect_serial_flow_alive())uart_flow_pending=0x13;
 {
  start=aspect_serial_ticks();
  do{aspect_serial_poll();now=aspect_serial_ticks();if(now<start)now+=1573040UL;}
  while((uart_flow_pending || !aspect_serial_tx_empty()) && now-start<36UL);
  if((uart_flow_pending || !aspect_serial_tx_empty()) && !aspect_serial_status)aspect_serial_status=ASPECT_SERIAL_PENDING;
 }
 status=aspect_serial_backend_close();
#ifdef ASPECT_REGISTER_HANDOFF
 if(aspect_register_publish() && !status)status=ASPECT_SERIAL_STATE;
#endif
 compile_pause_owned=0;
 if(handoff){
  n=uart_rx_count;at=uart_rx_read-(unsigned)uart_rx_buffer;
  if(n>4096 || at>=4096){n=0;if(!status)status=ASPECT_SERIAL_STATE;}
  count=n;
  destination=(unsigned char __far *)MK_FP(handoff->parent_ds,handoff->ring);
  for(;n;--n){*destination++=uart_rx_buffer[at];if(++at==4096)at=0;}
  handoff->status=status;handoff->count=count;
  if(handoff->version==ASIO_VERSION_FLOW || handoff->version==ASIO_VERSION_CARRIER REGISTER_OR(handoff->version))
   ((aspect_serial_handoff_v5 __far *)handoff)->flow_flags=preload_carrier_policy|(uart_tx_paused?1U:0U);
  handoff->returned=1;handoff=0;aspect_serial_handoff_enabled=0;
 }
 aspect_serial_status=status;return status;
}
unsigned __cdecl aspect_serial_compile_pause(void)
{
 unsigned status;unsigned long start,now;
 if(!aspect_serial_active)return 0;
 if(compile_pause_owned)return ASPECT_SERIAL_BUSY;
 status=aspect_serial_compile_hold();if(status)return status;compile_pause_owned=1;
 start=aspect_serial_ticks();
 do{
  status=aspect_serial_poll();if(status){aspect_serial_compile_resume();return status;}
  if(!uart_flow_pending&&aspect_serial_tx_empty())return 0;
  now=aspect_serial_ticks();if(now<start)now+=1573040UL;
 }while(now-start<36UL);
 aspect_serial_compile_resume();return ASPECT_SERIAL_PENDING;
}
unsigned __cdecl aspect_serial_compile_resume(void)
{
#if defined(ASPECT_EXTERNAL_PROCESS)
 if(aspect_serial_active==2)return ASPECT_SERIAL_BUSY;
#endif
 if(!compile_pause_owned)return 0;
 compile_pause_owned=0;if(!aspect_serial_active)return 0;
 aspect_serial_compile_release();return aspect_serial_poll();
}
