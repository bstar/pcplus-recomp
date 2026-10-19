/* Fixed grammar; hardware ownership lives in serial_backend.asm. */
#include "serial.h"
#include "serial_handoff.h"
#include <dos.h>
extern unsigned char uart_rx_buffer[];
extern unsigned uart_rx_read,uart_rx_count;
extern unsigned uart_software_flow;
extern unsigned char uart_flow_pending;
extern unsigned aspect_serial_handoff_enabled;
extern unsigned __cdecl aspect_serial_backend_close(void);
extern unsigned __cdecl aspect_serial_psp(void);
extern unsigned __cdecl aspect_serial_tx_empty(void);
static aspect_serial_handoff __far *handoff;
extern unsigned __cdecl aspect_serial_backend_open(unsigned,unsigned,unsigned,unsigned);
static unsigned hex(unsigned c)
{if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;return 65535U;}
unsigned __cdecl aspect_serial_open(const char *p)
{
 unsigned i,v,divisor=0,lcr=0,flow,segment=0,offset=0,status,parent;
 unsigned long begin,end,address,ring;
 unsigned char __far *mcb;
 aspect_serial_handoff __far *candidate=0;
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
  if(candidate->magic!=ASIO_MAGIC || candidate->version!=ASIO_VERSION || candidate->size!=ASIO_SIZE ||
   candidate->parent_psp!=parent || !candidate->parent_psp ||
   candidate->capacity!=4096 || candidate->count || candidate->status || candidate->returned || candidate->reserved0 || candidate->reserved1 ||
   candidate->guard!=(candidate->parent_psp^candidate->parent_ds^candidate->ring^ASIO_GUARD) ||
   (unsigned long)candidate->ring+4096UL>65536UL)return ASPECT_SERIAL_ARGUMENT;
  ring=(unsigned long)candidate->parent_ds*16UL+candidate->ring;
  if(end>1048576UL || address<begin || address+ASIO_SIZE>end || ring<begin || ring+4096UL>end ||
    (address<ring+4096UL && ring<address+ASIO_SIZE))return ASPECT_SERIAL_ARGUMENT;
 }
 flow=(unsigned char)p[12];if(flow>='a'&&flow<='z')flow-=32;
 if(flow!='N'&&flow!='S'&&flow!='H'&&flow!='B')return ASPECT_SERIAL_ARGUMENT;
 status=aspect_serial_backend_open(p[2]-'1',divisor,lcr,flow);
 if(!status){handoff=candidate;aspect_serial_handoff_enabled=candidate!=0;}
 return status;
}

unsigned __cdecl aspect_serial_close(void)
{
 unsigned status,n,at,count;
 unsigned char __far *destination;
 unsigned long start,now;
 if(!aspect_serial_active)return aspect_serial_status;
 /* Stop upstream before taking the child ISR down. Control flow bypasses
  * peer CTS/XOFF. Advisory36tick bound never repeats accepted data bytes. */
 if(uart_software_flow)uart_flow_pending=0x13;
 {
  start=aspect_serial_ticks();
  do{aspect_serial_poll();now=aspect_serial_ticks();if(now<start)now+=1573040UL;}
  while((uart_flow_pending || !aspect_serial_tx_empty()) && now-start<36UL);
  if((uart_flow_pending || !aspect_serial_tx_empty()) && !aspect_serial_status)aspect_serial_status=ASPECT_SERIAL_PENDING;
 }
 status=aspect_serial_backend_close();
 if(handoff){
  n=uart_rx_count;at=uart_rx_read-(unsigned)uart_rx_buffer;
  if(n>4096 || at>=4096){n=0;if(!status)status=ASPECT_SERIAL_STATE;}
  count=n;
  destination=(unsigned char __far *)MK_FP(handoff->parent_ds,handoff->ring);
  for(;n;--n){*destination++=uart_rx_buffer[at];if(++at==4096)at=0;}
  handoff->status=status;handoff->count=count;
  handoff->returned=1;handoff=0;aspect_serial_handoff_enabled=0;
 }
 aspect_serial_status=status;return status;
}
