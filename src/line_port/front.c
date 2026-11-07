/* Persistent front state lives in code, never in the nearly full DGROUP. */
#include "front.h"
#include "session.h"
#include "plan.h"
#include "persist.h"
#define CAPTURE_FIXED_RESERVATION
#include "../capture/capture_file.h"
#include <dos.h>
typedef unsigned word;typedef unsigned char byte;
#define TEXT __based(__segname("_CODE"))
extern word terminal_port_number,terminal_baud_low,terminal_baud_high;
extern word terminal_parity,terminal_data_bits,terminal_stop_bits,uart_port_rbr,uart_irq_indices;
extern word terminal_program_active,terminal_program_pending,terminal_program_kind;
extern word terminal_quit,terminal_exit_code,redisplay_active,command_menu_active,ui_window_rows;
extern word line_port_port;extern terminal_import_settings terminal_configuration_values;
#pragma aux terminal_port_number "terminal_port_number";
#pragma aux terminal_baud_low "terminal_baud_low";
#pragma aux terminal_baud_high "terminal_baud_high";
#pragma aux terminal_parity "terminal_parity";
#pragma aux terminal_data_bits "terminal_data_bits";
#pragma aux terminal_stop_bits "terminal_stop_bits";
#pragma aux uart_port_rbr "uart_port_rbr";
#pragma aux uart_irq_indices "uart_irq_indices";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_program_pending "terminal_program_pending";
#pragma aux terminal_program_kind "terminal_program_kind";
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux ui_window_rows "ui_window_rows";
#pragma aux line_port_port "line_port_port";
#pragma aux terminal_configuration_values "terminal_configuration_values";
extern word __far __cdecl recording_ui_ready(void);
extern word __far __cdecl line_port_queue(void);
extern word __far __cdecl line_port_reopen(void);
extern word __far __cdecl hook_prepare_link(void);
extern word __far __cdecl hook_port_check(const terminal_import_settings *);
extern word __far __cdecl hook_port_move(const terminal_import_settings *);
extern word __far __cdecl line_file_frozen(char *);
extern word __far __cdecl line_file_read(const char *,prm_dos_image *,prm_dos_result *);
extern word __far __cdecl line_file_store(const char *,const byte *,const byte *,directory_replace_result *);
extern word __far __cdecl line_port_setup_saved_ack(word,word);
typedef struct front_state {
 word cookie,phase,notice,claimed,uncertain,saved;
 word normal,bold,title;
 char path[64];byte expected[10],ports[16];
 terminal_import_settings actual;
 line_port_session session;
 line_port_plan plan;
 directory_replace_result storage;
} front_state;
front_state TEXT line_port_front_storage={0x4c50};
typedef char front_layout[sizeof(front_state)==256?1:-1];
#define S line_port_front_storage
static const char TEXT busy[]="Line/Port unavailable. Finish the active operation. Esc returns.";
static const char TEXT failed[]="Line/Port could not apply. Esc returns; reopen Alt-P to try again.";
static const char TEXT saved_failed[]="Settings saved, but not applied. Esc returns.";
static const char TEXT recovery[]="PRM recovery required (PCPSTG.$$$ / PCPBAK.$$$). Esc exits to DOS.";
static const char TEXT unsupported[]="COM5 through COM8 are unavailable. Choose COM1 through COM4.";
static const char TEXT geometry[]="Line/Port requires 80x25 text mode. Esc returns.";
static void copy(void __far *to,const void __far *from,word n)
{byte __far *d=to;const byte __far *s=from;while(n--)*d++=*s++;}
static void current(terminal_import_settings *p)
{
 *p=terminal_configuration_values;p->port_number=terminal_port_number;
 p->baud_low=terminal_baud_low;p->baud_high=terminal_baud_high;
 p->parity=terminal_parity;p->data_bits=terminal_data_bits;p->stop_bits=terminal_stop_bits;
 p->io_base=uart_port_rbr;p->irq=uart_irq_indices;
}
static void release(void)
{if(S.claimed && !S.uncertain){
 if(capture_file_unclaim(&line_port_port)){S.uncertain=1;S.notice=4;}else S.claimed=0;
 }}
static void text(word __far *f,word at,const char __far *s)
{while(*s && at<2000)f[at++]=0x0f00|(byte)*s++;}
static void draw(word __far *frame)
{
 line_port_session edit;word r,c,at,value;const char __far *notice=0;
 copy(&edit,&S.session,sizeof(edit));
 if(line_port_view(&edit.selected,frame,2000))return;
 for(r=2;r<=19;++r)for(c=18;c<=76;++c){
  at=r*80+c;value=frame[at]>>8;
  frame[at]=(frame[at]&255)|((value==11?S.bold:S.normal)<<8);
 }
 for(c=0;c<80;++c)frame[1920+c]=(frame[1920+c]&255)|(S.title<<8);
 if(S.notice==2)notice=busy;
 else if(S.notice==3){if(S.saved)notice=saved_failed;else notice=failed;}
 else if(S.notice==4)notice=recovery;
 else if(S.notice==5)notice=unsupported;
 else if(S.notice==6)notice=geometry;
 if(notice){for(c=0;c<80;++c)frame[20*80+c]=0x0720;text(frame,20*80+1,notice);}
}
static void begin(void)
{
 line_port_session edit;line_port_values values;
 terminal_import_settings actual;prm_dos_image image;prm_dos_result io;
 char tail[68],path[64];word i,status;
 for(i=0;i<sizeof(edit);++i)((byte *)&edit)[i]=0;
 values.port=0;values.baud=5;values.parity=0;values.stop=1;values.bits=8;
 if(S.uncertain){S.phase=1;S.notice=4;return;}
 S.phase=1;S.notice=S.saved=0;S.normal=7;S.bold=11;S.title=113;
 line_port_session_begin(&edit,&values);copy(&S.session,&edit,sizeof(edit));
 if(ui_window_rows!=25){S.notice=6;return;}
 if(!recording_ui_ready() || line_file_frozen(tail)){S.notice=2;return;}
 for(i=0;i<64;++i)path[i]=tail[i+1];path[63]=0;
 if(capture_file_claim(path,&line_port_port)){S.notice=2;return;}S.claimed=1;
 status=line_file_read(path,&image,&io);
 if(status){S.notice=3;if(io.close_error){S.uncertain=1;S.notice=4;}release();return;}
 if(image.bytes[0x3e5] || image.bytes[0x3e7] || image.bytes[0x3e9]){S.notice=3;release();return;}
 current(&actual);if(line_port_from_serial(&actual,&values)){S.notice=3;release();return;}
 for(i=0;i<sizeof(edit);++i)((byte *)&edit)[i]=0;
 if(line_port_session_begin(&edit,&values)){S.notice=3;release();return;}
 copy(&S.path,path,64);copy(&S.actual,&actual,sizeof(actual));copy(&S.session,&edit,sizeof(edit));
 copy(&S.expected,image.bytes,10);copy(&S.ports,image.bytes+0x174,8);copy((byte __far *)&S.ports+8,image.bytes+0x184,8);
 S.normal=image.bytes[0x3e4];S.bold=image.bytes[0x3e6];S.title=image.bytes[0x3e8];
}
word __far __cdecl line_port_front_cursor(void)
{return S.phase==1?0x1243:0xffff;}
word __far __cdecl line_port_front_event(word event,word key,unsigned short __far *frame)
{
 line_port_session edit;line_port_values values;line_port_plan proposal;
 terminal_import_settings actual;prm_dos_image image;word i,status,events,wants_save;
 if(event==4){release();S.phase=0;return 0;}
 if(event==0){if(S.phase!=4)begin();else S.phase=1;draw((word __far *)frame);return 1;}
 if(event==2){if(S.phase==1)draw((word __far *)frame);return 1;}
 if(event==3)return 2;
 if(event!=1 || S.phase!=1)return 1;
 if(S.notice && S.notice!=5){
  if((key&255)==27){
   if(S.uncertain){terminal_exit_code=14;terminal_quit=1;}
   release();S.phase=0;return 0;
  }return 1;
 }
 copy(&edit,&S.session,sizeof(edit));status=line_port_session_key(&edit,key,&events);
 copy(&S.session,&edit,sizeof(edit));S.notice=status==LINE_PORT_UNSUPPORTED?5:0;
 if(edit.phase!=LINE_PORT_REQUEST){draw((word __far *)frame);return 1;}
 if(!recording_ui_ready()){edit.phase=LINE_PORT_EDIT;edit.notice=0;copy(&S.session,&edit,sizeof(edit));S.notice=2;draw((word __far *)frame);return 1;}
 if(line_port_session_request(&edit,&values,&wants_save)){S.notice=3;draw((word __far *)frame);return 1;}
 for(i=0;i<sizeof(image);++i)image.bytes[i]=0;copy(image.bytes+0x174,&S.ports,8);copy(image.bytes+0x184,(const byte __far *)&S.ports+8,8);
 copy(&actual,&S.actual,sizeof(actual));
 if(line_port_plan_make(&actual,&values,&image,&proposal)){S.notice=3;draw((word __far *)frame);return 1;}
 copy(&S.plan,&proposal,sizeof(proposal));
 if(line_port_queue()){S.notice=2;draw((word __far *)frame);return 1;}
 terminal_program_kind=12;S.phase=2;return 0;
}
word __far __cdecl line_port_front_run(void)
{
 line_port_plan proposal;line_port_session edit;terminal_import_settings actual;
 directory_replace_result result;char path[64];byte expected[10];word status=0,wants_save,i;
 if(S.phase!=2)return 1;
 copy(&proposal,&S.plan,sizeof(proposal));copy(&edit,&S.session,sizeof(edit));
 copy(path,&S.path,64);copy(expected,&S.expected,10);
 current(&actual);
 if(actual.port_number!=S.actual.port_number || actual.baud_low!=S.actual.baud_low ||
 actual.baud_high!=S.actual.baud_high || actual.parity!=S.actual.parity || actual.data_bits!=S.actual.data_bits ||
 actual.stop_bits!=S.actual.stop_bits || actual.io_base!=S.actual.io_base || actual.irq!=S.actual.irq)status=1;
 if(!status && proposal.change_mask)status=hook_prepare_link();
 if(!status && (proposal.change_mask&1))status=hook_port_check(&proposal.serial);
 wants_save=edit.save;
 if(!status && wants_save){
  for(i=0;i<sizeof(result);++i)((byte *)&result)[i]=0;
  status=line_file_store(path,expected,proposal.prefix,&result);copy(&S.storage,&result,sizeof(result));
  S.saved=result.installed;
  if(status){
   S.uncertain=result.close_error || result.stage_exists || result.original_in_backup || result.rollback_error;
   line_port_session_saved(&edit,status,S.uncertain);
  }else{line_port_session_saved(&edit,0,0);S.saved=1;}
 }
 if(!status && (proposal.change_mask&1))status=hook_port_move(&proposal.serial);
 if(!status){
  terminal_port_number=proposal.serial.port_number;
  terminal_baud_low=proposal.serial.baud_low;terminal_baud_high=proposal.serial.baud_high;
  terminal_parity=proposal.serial.parity;terminal_data_bits=proposal.serial.data_bits;terminal_stop_bits=proposal.serial.stop_bits;
  /* Runtime flow/profile and unrelated policy remain unchanged. */
  terminal_configuration_values.port_number=proposal.serial.port_number;
  terminal_configuration_values.baud_low=proposal.serial.baud_low;terminal_configuration_values.baud_high=proposal.serial.baud_high;
  terminal_configuration_values.parity=proposal.serial.parity;terminal_configuration_values.data_bits=proposal.serial.data_bits;
  terminal_configuration_values.stop_bits=proposal.serial.stop_bits;terminal_configuration_values.io_base=proposal.serial.io_base;
  terminal_configuration_values.irq=proposal.serial.irq;
  if(S.saved)status=line_port_setup_saved_ack(proposal.serial.baud_low,proposal.serial.baud_high);
 }
 if(!status){line_port_session_applied(&edit,0);S.phase=0;release();}
 else{S.notice=S.uncertain?4:3;S.phase=4;if(!S.uncertain)release();}
 copy(&S.session,&edit,sizeof(edit));(void)i;return status;
}
void __far __cdecl line_port_front_poll(void)
{
 if(S.phase==2 && !terminal_program_pending && !terminal_program_active){S.phase=4;S.notice=3;release();}
 if(S.phase==4 && !terminal_program_pending && !terminal_program_active && !redisplay_active && !command_menu_active)
  line_port_reopen();
}
