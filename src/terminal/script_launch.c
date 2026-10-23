/* Maintained direct Script child argument validation, not native scheduling.
 * No DOS, UART or script execution here. DS=SS, bounded near buffers. */
#include "../config/resource_path.h"
#include "../aspect/serial_handoff.h"
#include <dos.h>
#ifdef TERMINAL_REGISTER_HANDOFF
#include "register_owner.h"
#endif
extern aspect_serial_handoff script_handoff;
extern unsigned script_divisor,script_lcr;
extern unsigned script_port_index,script_soft_flow,script_hard_flow;
extern unsigned script_parent_ring;
extern unsigned script_directory_entry,script_directory_record;
extern unsigned script_directory_year,script_directory_month,script_directory_day,script_directory_delta;
extern unsigned script_render_offset,script_render_segment,script_render_token,script_render_version;
extern unsigned script_flow_flags;
extern unsigned char connection_enabled,connection_carrier_seen;
extern unsigned terminal_directory_mode;
#pragma aux connection_enabled "connection_enabled";
#pragma aux connection_carrier_seen "connection_carrier_seen";
#pragma aux terminal_directory_mode "terminal_directory_mode";
static char digit(unsigned value){return value<10?(char)(value+'0'):(char)(value-10+'A');}
static char *hexword(char *p,unsigned n){*p++=digit(n>>12);*p++=digit((n>>8)&15);*p++=digit((n>>4)&15);*p++=digit(n&15);return p;}
static unsigned span(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned folded(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned device(const char *p,unsigned n)
{
 unsigned a=folded(p[0]),b=n>1?folded(p[1]):0,c=n>2?folded(p[2]):0;
 if(n==3 && ((a=='C'&&b=='O'&&c=='N')||(a=='P'&&b=='R'&&c=='N')||
 (a=='A'&&b=='U'&&c=='X')||(a=='N'&&b=='U'&&c=='L')))return 1;
 return n==4 && ((a=='C'&&b=='O'&&c=='M')||(a=='L'&&b=='P'&&c=='T')) && p[3]>='1' && p[3]<='9';
}
unsigned __cdecl terminal_script_prepare(unsigned psp,char *executable,char *tail)
{
 unsigned i=1,start=1,base=0,extension=0,dot=0,c,status,ds,translation;char *p;
#ifdef TERMINAL_REGISTER_HANDOFF
 unsigned long register_descriptor;
#endif
 if(!span(executable,64)||!span(tail,96)||!apart(executable,64,tail,96)||tail[0]!=' ')return 1;
 /* Optional drive and root; every following component is a strict DOS83 name.
  * Reject shell syntax, whitespace, traversal and device aliases even though
  * direct EXEC does not invoke a command interpreter. */
 if(((tail[i]>='A'&&tail[i]<='Z')||(tail[i]>='a'&&tail[i]<='z'))&&tail[i+1]==':')i+=2;
 if(tail[i]=='\\')++i;start=i;
 for(;i<65;++i){
  c=(unsigned char)tail[i];
  if(!c || c=='\\'){
   if(!base || (dot&&!extension) || device(tail+start,base))return 1;
   if(!c){
    status=resource_program_path(psp,"ASPECT.EXE",executable);if(status)return 2;
    if(script_port_index>3 || !script_divisor || (script_lcr&192))return 1;
    ds=FP_SEG((void __far *)&script_handoff);
    /* Match the actual main-loop policy: table only when enabled; mode2 is
     * disabled-table plus ISR7-bit mask. Reject inconsistent live settings. */
    /* Resident prepare has validated/staged the actual live policy in these
     * existing descriptor words before crossing the CONFIG_CODE bridge. */
    translation=script_handoff.reserved1;if(translation>2)return 1;
    if(connection_enabled && terminal_directory_mode!=1 && connection_carrier_seen)script_flow_flags|=2;
    script_handoff.magic=ASIO_MAGIC;script_handoff.version=ASIO_VERSION_CARRIER;script_handoff.size=ASIO_V6_SIZE;
    script_handoff.parent_psp=psp;script_handoff.parent_ds=ds;
    script_handoff.ring=(unsigned)script_parent_ring;script_handoff.capacity=4096;
    script_handoff.returned=0;
    script_handoff.guard=psp^ds^(unsigned)script_parent_ring^ASIO_GUARD^
     script_handoff.reserved0^script_handoff.reserved1^script_handoff.count^
     script_handoff.status^script_directory_entry^script_directory_record^
     script_directory_year^script_directory_month^script_directory_day^script_directory_delta^
     script_render_offset^script_render_segment^script_render_token^script_render_version^script_flow_flags;
#ifdef TERMINAL_REGISTER_HANDOFF
    register_descriptor=terminal_register_prepare(&script_handoff);
    if(!register_descriptor)return 3;
#endif
    p=tail+i;*p++=' ';*p++='/';*p++='S';*p++='1'+script_port_index;*p++=':';
    p=hexword(p,script_divisor);*p++=':';*p++=digit(script_lcr>>4);*p++=digit(script_lcr&15);*p++=':';
    *p++=script_soft_flow?(script_hard_flow?'B':'S'):script_hard_flow?'H':'N';*p++=':';
#ifdef TERMINAL_REGISTER_HANDOFF
    p=hexword(p,(unsigned)(register_descriptor>>16));*p++=':';p=hexword(p,(unsigned)register_descriptor);*p=0;
#else
    p=hexword(p,ds);*p++=':';p=hexword(p,(unsigned)&script_handoff);*p=0;
#endif
    return 0;
   }
   start=i+1;base=extension=dot=0;continue;
  }
  if(c=='.'){if(!base||dot)return 1;dot=1;continue;}
  c=folded(c);
  if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-'))return 1;
  if(dot){if(++extension>3)return 1;}else if(++base>8)return 1;
 }
 return 1;
}
