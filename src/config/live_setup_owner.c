#include "live_setup_owner.h"
#include "transfer_import.h"
extern transfer_import_settings terminal_transfer_preferences;
#include <string.h>
#ifdef TERMINAL_MOUSE
extern unsigned __cdecl terminal_mouse_offer(const unsigned char *,unsigned);
extern unsigned __cdecl terminal_mouse_commit(void);
extern void __cdecl terminal_mouse_discard(void);
#endif
/* Register-ABI DOS canonicalizer and explicit cdecl native-expansion adapter.
 * Both are declared named resident services in config_abi.inc. */
extern unsigned capture_fs_canonical(const char *,char *);
extern unsigned __cdecl live_modem_expand(const unsigned char *,unsigned char *,unsigned,unsigned);
typedef char result_abi[sizeof(live_setup_result)==8?1:-1];
typedef struct setup_owner {
 unsigned bound,pending,has_context,option_mask,transfer_ready;
 unsigned source_baud_low,source_baud_high,source_clipboard_separator;
 unsigned offered_clipboard_separator;
 unsigned offered_mask,offered_baud_low,offered_baud_high;
 char path[64],canonical[128];
 directory_live_context context;
 unsigned char target[64];
 live_configuration_plan active,stage;
 prm_dos_image image;
} setup_owner;
static setup_owner owner;
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned external(const void *p,unsigned n)
{return extent(p,n) && separate(p,n,&owner,sizeof(owner));}
static unsigned string_size(const char *p,unsigned cap)
{unsigned i;if(!extent(p,cap))return 0;for(i=0;i<cap;++i)if(!p[i])return i+1;return 0;}
static unsigned same(const char *a,const char *b,unsigned cap)
{
 unsigned i,x,y;
 for(i=0;i<cap;++i){x=(unsigned char)a[i];y=(unsigned char)b[i];
  if(x>='a' && x<='z')x-=32;if(y>='a' && y<='z')y-=32;
  if(x!=y)return 0;if(!x)return 1;}
 return 0;
}
unsigned __cdecl live_setup_bind(const char *path,
 const directory_live_context *context,const terminal_import_settings *source)
{
 char canonical[128];unsigned size;
 if(!external(path,64) || !external(source,sizeof(*source)) ||
  (context && !external(context,sizeof(*context))))return LIVE_SETUP_ARGUMENT;
 owner.bound=owner.pending=owner.offered_mask=owner.transfer_ready=0;
#ifdef TERMINAL_MOUSE
 terminal_mouse_discard();
#endif
 if(source->clipboard_separator>255)return LIVE_SETUP_ARGUMENT;
 size=string_size(path,64);if(size<2)return LIVE_SETUP_ARGUMENT;
 if(context && !directory_live_context_matches(context,path,context->directory_path,
  context->selection.entry_number,context->codes))return LIVE_SETUP_IDENTITY;
 memset(canonical,0,sizeof(canonical));
 if(capture_fs_canonical(path,canonical) || string_size(canonical,128)<2)return LIVE_SETUP_IDENTITY;
 memset(owner.path,0,64);memcpy(owner.path,path,size);
 memcpy(owner.canonical,canonical,128);owner.has_context=context!=0;
 if(context)memcpy(&owner.context,context,sizeof(*context));
 owner.source_baud_low=source->baud_low;owner.source_baud_high=source->baud_high;
 owner.source_clipboard_separator=owner.offered_clipboard_separator=source->clipboard_separator;
 owner.bound=1;return LIVE_SETUP_OK;
}
unsigned __cdecl live_setup_begin(const char *path,
 const directory_live_context *context,const live_configuration_plan *active,
 unsigned option_mask,const unsigned char *target)
{
 char canonical[128];
 if(!external(path,64) || !external(active,sizeof(*active)) || !external(target,64) ||
  (context && !external(context,sizeof(*context))))return LIVE_SETUP_ARGUMENT;
 if(owner.bound!=1)return LIVE_SETUP_UNBOUND;
 if(owner.pending==1)return LIVE_SETUP_STATE;
 if(string_size(path,64)<2 || !same(path,owner.path,64) ||
  (context!=0)!=owner.has_context || ((option_mask&64)!=0)!=owner.has_context ||
  !(option_mask&16) || !string_size((const char *)target,64))return LIVE_SETUP_IDENTITY;
 if(context && memcmp(context,&owner.context,sizeof(*context)))return LIVE_SETUP_IDENTITY;
 memset(canonical,0,sizeof(canonical));
 if(capture_fs_canonical(path,canonical) || !same(canonical,owner.canonical,128))return LIVE_SETUP_IDENTITY;
 memcpy(&owner.active,active,sizeof(*active));memcpy(owner.target,target,64);
 owner.option_mask=option_mask;owner.offered_mask=owner.transfer_ready=0;
#ifdef TERMINAL_MOUSE
 terminal_mouse_discard();
#endif
 owner.offered_clipboard_separator=owner.source_clipboard_separator;owner.pending=1;return LIVE_SETUP_OK;
}
static unsigned command_valid(const live_configuration_plan *plan)
{
 unsigned char buffer[129];unsigned i;
 const unsigned char *commands[5];unsigned caps[5];
 if(!(owner.option_mask&96) || (owner.has_context && plan->directory.dialing_mode==1))return 1;
 commands[0]=plan->modem.initialization;caps[0]=47;
 commands[1]=plan->modem.hangup;caps[1]=25;
 commands[2]=plan->modem.dial_prefix;caps[2]=25;
 commands[3]=owner.target;caps[3]=64;
 commands[4]=plan->modem.dial_suffix;caps[4]=25;
 /* Each expansion cannot exceed its input. The concatenated dial command
  * fits24+63+24=111 bytes in the existing129-byte destination. */
 for(i=0;i<5;++i)if(live_modem_expand(commands[i],buffer,caps[i],129))return 0;
 return 1;
}
unsigned __cdecl live_setup_finish(live_configuration_plan *destination,live_setup_result *result)
{return live_setup_finish_policy(destination,result,0);}
unsigned __cdecl live_setup_finish_policy(live_configuration_plan *destination,
 live_setup_result *result,unsigned permitted_link_mask)
{
 transfer_import_settings transfer;
 live_configuration_result decoded;prm_dos_result io;unsigned mask,status,deferred,saved_clipboard_separator;
 if((permitted_link_mask&~(31U|LIVE_CHANGE_TRANSLATION)) || !external(destination,sizeof(*destination)) || !external(result,sizeof(*result)) ||
  !separate(destination,sizeof(*destination),result,sizeof(*result)))return LIVE_SETUP_ARGUMENT;
 memset(result,0,sizeof(*result));
 if(owner.bound!=1 || owner.pending!=1){result->status=LIVE_SETUP_STATE;return result->status;}
 owner.pending=owner.transfer_ready=0;
#ifdef TERMINAL_MOUSE
 terminal_mouse_discard();
#endif
 status=prm_dos_load(owner.canonical,&owner.image,&io);
 if(status){result->status=LIVE_SETUP_IO;result->source_status=status;return result->status;}
 mask=owner.option_mask&15;
 /* Directory accounting updates a different record baseline. Compare against
  * the frozen logical selection, never replace the active accounting record. */
 if(owner.has_context){
  status=directory_live_decode(&owner.image,&owner.context.selection,owner.context.codes,
   &owner.stage.serial,&owner.stage.modem,&owner.stage.directory,0);
  if(status){result->status=LIVE_SETUP_DECODE;result->source_status=status;return result->status;}
  memcpy(&owner.active.directory,&owner.stage.directory,sizeof(owner.stage.directory));
 }
 status=live_configuration_decode(&owner.image,owner.has_context?&owner.context.selection:0,
  owner.has_context?owner.context.codes:0,mask,&owner.active,&owner.stage,&decoded);
 if(status){result->status=LIVE_SETUP_DECODE;result->source_status=status;return result->status;}
 /* A negotiated rate is not an implicit request to restore the PRM's old
  * source rate on every unrelated save. Pending deliberate rate edits retain
  * their deferred classification across repeated editor invocations. */
 if(!(mask&2) && !((permitted_link_mask&LIVE_CHANGE_PORT) && (owner.stage.change_mask&LIVE_CHANGE_PORT)) &&
  owner.stage.serial.baud_low==owner.source_baud_low &&
  owner.stage.serial.baud_high==owner.source_baud_high){
  status=live_configuration_decode(&owner.image,owner.has_context?&owner.context.selection:0,
   owner.has_context?owner.context.codes:0,mask|2,&owner.active,&owner.stage,&decoded);
  if(status){result->status=LIVE_SETUP_DECODE;result->source_status=status;return result->status;}
 }
 if(transfer_import_decode(&owner.image,&transfer)){result->status=LIVE_SETUP_DECODE;result->source_status=14;return result->status;}
 saved_clipboard_separator=owner.stage.serial.clipboard_separator;
 /* Session R is independent of the saved file. A cancel/no-op or unrelated
  * save must not restore its old stored separator. Adopt only a file edit. */
 if(owner.stage.serial.clipboard_separator==owner.source_clipboard_separator){
  owner.stage.serial.clipboard_separator=owner.active.serial.clipboard_separator;
  owner.stage.change_mask&=~LIVE_CHANGE_CLIPBOARD;
 }
 if(!command_valid(&owner.stage)){result->status=LIVE_SETUP_COMMAND;return result->status;}
#ifdef TERMINAL_MOUSE
 status=terminal_mouse_offer(owner.image.bytes,sizeof(owner.image.bytes));
 if(status==15){result->status=LIVE_SETUP_DECODE;result->source_status=15;return result->status;}
 owner.stage.change_mask|=status;
#endif
 /* Explicit /X fixes the effective table mode, after raw PRM validation.
  * Other mode changes require explicit permission and a foreground handoff. */
 if(owner.option_mask&16384U){
  owner.stage.serial.translation_mode=owner.active.serial.translation_mode;
  owner.stage.change_mask&=~LIVE_CHANGE_TRANSLATION;
 }
 if((owner.stage.change_mask&LIVE_CHANGE_PORT) && !(permitted_link_mask&LIVE_CHANGE_PORT))permitted_link_mask&=~31U;
 deferred=owner.stage.change_mask&(((LIVE_CHANGE_TRANSPORT|LIVE_CHANGE_PROFILE|LIVE_CHANGE_TRANSLATION)&~permitted_link_mask)|LIVE_CHANGE_DIRECTORY|LIVE_CHANGE_TARGET);
 if(memcmp(&transfer,&terminal_transfer_preferences,sizeof(transfer)))owner.stage.change_mask|=8192U;
 owner.offered_clipboard_separator=saved_clipboard_separator;
 owner.offered_mask=owner.stage.change_mask;
 owner.offered_baud_low=owner.stage.serial.baud_low;owner.offered_baud_high=owner.stage.serial.baud_high;
 if(!(permitted_link_mask&LIVE_CHANGE_PORT)){
  owner.stage.serial.port_number=owner.active.serial.port_number;
  owner.stage.serial.io_base=owner.active.serial.io_base;
  owner.stage.serial.irq=owner.active.serial.irq;
 }
 if(!(permitted_link_mask&LIVE_CHANGE_BAUD)){
  owner.stage.serial.baud_low=owner.active.serial.baud_low;owner.stage.serial.baud_high=owner.active.serial.baud_high;
 }
 if(!(permitted_link_mask&LIVE_CHANGE_LINE)){
  owner.stage.serial.parity=owner.active.serial.parity;owner.stage.serial.data_bits=owner.active.serial.data_bits;owner.stage.serial.stop_bits=owner.active.serial.stop_bits;
 }
 if(!(permitted_link_mask&LIVE_CHANGE_FLOW)){
  owner.stage.serial.software_flow=owner.active.serial.software_flow;owner.stage.serial.hardware_flow=owner.active.serial.hardware_flow;
 }
 if(!(permitted_link_mask&LIVE_CHANGE_PROFILE))owner.stage.serial.terminal_id=owner.active.serial.terminal_id;
 if(!(permitted_link_mask&LIVE_CHANGE_TRANSLATION))owner.stage.serial.translation_mode=owner.active.serial.translation_mode;
 memcpy(&owner.stage.directory,&owner.active.directory,sizeof(owner.stage.directory));
 result->deferred_mask=deferred;result->applied_mask=owner.stage.change_mask&~deferred;
 memcpy(destination,&owner.stage,sizeof(*destination));owner.transfer_ready=1;return LIVE_SETUP_OK;
}
unsigned __cdecl live_setup_abort(unsigned unused)
{(void)unused;owner.pending=owner.offered_mask=owner.transfer_ready=0;owner.offered_clipboard_separator=owner.source_clipboard_separator;
#ifdef TERMINAL_MOUSE
 terminal_mouse_discard();
#endif
 return LIVE_SETUP_OK;}
unsigned __cdecl live_setup_acknowledge(unsigned committed_baud_mask)
{
 if(committed_baud_mask!=0 && committed_baud_mask!=LIVE_CHANGE_BAUD)return LIVE_SETUP_ARGUMENT;
 if(owner.bound!=1)return LIVE_SETUP_UNBOUND;
 if(committed_baud_mask && !(owner.offered_mask&LIVE_CHANGE_BAUD))return LIVE_SETUP_STATE;
#ifdef TERMINAL_MOUSE
 if(terminal_mouse_commit())return LIVE_SETUP_STATE;
#endif
 if(committed_baud_mask){owner.source_baud_low=owner.offered_baud_low;owner.source_baud_high=owner.offered_baud_high;}
 owner.source_clipboard_separator=owner.offered_clipboard_separator;
 owner.offered_mask=owner.transfer_ready=0;return LIVE_SETUP_OK;
}

unsigned __cdecl live_setup_transfer_settings(transfer_import_settings *destination)
{
 if(!external(destination,sizeof(*destination)))return LIVE_SETUP_ARGUMENT;
 if(owner.bound!=1 || owner.pending || owner.transfer_ready!=1)return LIVE_SETUP_STATE;
 return transfer_import_decode(&owner.image,destination)?LIVE_SETUP_DECODE:LIVE_SETUP_OK;
}
