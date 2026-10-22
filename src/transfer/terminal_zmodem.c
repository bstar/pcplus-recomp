/* Live ZMODEM adapter. All session/work state belongs to the exclusive native
 * transfer arena; only UI summary words and the far callback table are near.
 * Compile with the engine/codec in CONFIG_CODE, DS=SS unchanged. */
#include "zmodem.h"
#include "ymodem.h"
#include "batch_upload.h"
#include "batch_download.h"
#include "upload_file.h"
#include "download_compare.h"
#include <stddef.h>
#include <string.h>
#include <dos.h>
extern char terminal_transfer_filename[64];
extern unsigned char terminal_transfer_ui_visible;
extern unsigned terminal_transfer_fault,terminal_transfer_cleanup_status;
extern unsigned terminal_zmodem_receive_credit;
unsigned terminal_zmodem_kbytes;
unsigned long terminal_zmodem_files;
typedef struct live_zmodem {
 zm_session session;
 unsigned long observed,files;
} live_zmodem;
typedef char fits_arena[sizeof(live_zmodem)<=10240?1:-1];
/* The transfer UI already owns/saves the bottom two rows. Keep this bounded
 * presentation in CONFIG_CODE: no extra resident code or persistent buffer.
 * A trailing '~' marks a remote name wider than its 46-column field. */
static void name_text(unsigned __far *video,const char *text,unsigned count)
{
 unsigned i;unsigned char c;
 for(i=0;i<count;++i){
  c=*text;if(c)++text;
  video[i]=0x1f00 | (c ? (c<32 || c==127 ? '?' : c) : ' ');
 }
}
static void received_name(live_zmodem *p,const batch_header_result *header,unsigned skip)
{
 unsigned __far *video;unsigned i;
 if(!terminal_transfer_ui_visible)return;
 video=MK_FP(0xb800,3840);
 name_text(video,"Remote: ",8);
 name_text(video+8,p->session.name,46);
 /* Only consult the next byte when the bounded prefix had no terminator. */
 for(i=0;i<46 && p->session.name[i];++i){}
 if(i==46 && p->session.name[46])video[53]=0x1f7e;
 name_text(video+54,skip?"  Skip: ":"  Save: ",8);
 name_text(video+62,header->name,12);
 for(i=74;i<80;++i)video[i]=0x1f20;
}
static void progress(live_zmodem *p)
{
 unsigned long kb=p->session.position>>10;
 unsigned advanced=p->session.position>p->observed || p->session.files>p->files;
 terminal_zmodem_kbytes=kb>65535UL?65535:(unsigned)kb;
 terminal_zmodem_files=p->session.files;
 /* Observe a rewind without calling it progress. Later confirmed forward
  * replay is live activity; the engine separately bounds repeated rewinds. */
 p->observed=p->session.position;p->files=p->session.files;
 if(advanced)ymodem_io_progress();
}
unsigned ZM_FAR __cdecl terminal_zmodem_input(void *ctx,unsigned seconds)
{
 unsigned value,chunk;live_zmodem *p=ctx;progress(p);
 /* The shared UART adapter caps each read at30 seconds. Honor longer
  * carrier allowances in serviced pieces, retaining fault/cancel checks and
  * the independent accepted-progress watchdog. Zero remains a genuine poll. */
 for(;;){
  chunk=seconds>30?30:seconds;
  value=ymodem_io_read(chunk);
  if(ymodem_io_poll())return terminal_transfer_fault==2?ZM_ABORT:ZM_BROKEN;
  if(value!=ZM_WAIT || seconds<=chunk)return value;
  seconds-=chunk;
 }
}
unsigned ZM_FAR __cdecl terminal_zmodem_output(void *ctx,const void *data,unsigned n)
{
 const unsigned char *bytes=data;unsigned i;progress(ctx);
 for(i=0;i<n;++i){
  if(ymodem_io_put(bytes[i]) || ymodem_io_poll())return terminal_transfer_fault==2?ZM_ABORT:ZM_BROKEN;
 }
 return 0;
}
unsigned ZM_FAR __cdecl terminal_zmodem_next(void *ctx,char *name,zw_u32 *size)
{
 live_zmodem *p=ctx;unsigned r=batch_upload_next();
 if(r==BU_DONE)return ZM_DONE;
 if(r!=BU_FILE)return ZM_FILE;
 memcpy(name,batch_upload_current.name,13);*size=batch_upload_current.size;p->observed=0;return 0;
}
unsigned ZM_FAR __cdecl terminal_zmodem_seek(void *ctx,zw_u32 at)
{(void)ctx;return batch_upload_seek(at);}
unsigned ZM_FAR __cdecl terminal_zmodem_read_file(void *ctx,void *data,unsigned n,unsigned *got)
{(void)ctx;return batch_upload_read(data,n,got);}
unsigned ZM_FAR __cdecl terminal_zmodem_close_source(void *ctx,unsigned complete)
{
 live_zmodem *p=ctx;
 return complete?batch_upload_close():p->session.status?batch_upload_abort():batch_upload_skip();
}
unsigned ZM_FAR __cdecl terminal_zmodem_open_received(void *ctx,const batch_header_result *header)
{
 live_zmodem *p=ctx;batch_header_result advisory=*header;unsigned r;
 advisory.flags&=~BH_LENGTH;advisory.size=0;
 r=batch_download_open(&advisory);
 if(r==BD_STORAGE && batch_download_result.file.first_status==TF_CONFLICT){received_name(p,header,1);return ZM_DONE;}
 if(r)return ZM_FILE;
 received_name(p,header,0);
 p->observed=0;ymodem_io_progress();return 0;
}
unsigned ZM_FAR __cdecl terminal_zmodem_write_received(void *ctx,const void *data,unsigned n)
{(void)ctx;return batch_download_exact(data,n);}
unsigned ZM_FAR __cdecl terminal_zmodem_commit(void *ctx)
{(void)ctx;return batch_download_finish();}
unsigned ZM_FAR __cdecl terminal_zmodem_abort_received(void *ctx)
{(void)ctx;return batch_download_cleanup();}
unsigned ZM_FAR __cdecl terminal_zmodem_verify_received(void *ctx,zw_u32 at,const void *data,unsigned count)
{
 const unsigned char *bytes=data;unsigned n,r;(void)ctx;
 while(count){
  if(ymodem_io_poll())return terminal_transfer_fault==2?ZM_ABORT:ZM_BROKEN;
  n=count>128?128:count;r=transfer_download_compare(at,bytes,n);
  if(r)return r==TF_MISMATCH?ZM_PROTOCOL:ZM_FILE;
  at+=n;bytes+=n;count-=n;
 }
 return 0;
}
const zm_ops terminal_zmodem_ops={terminal_zmodem_input,terminal_zmodem_output,terminal_zmodem_next,terminal_zmodem_seek,terminal_zmodem_read_file,terminal_zmodem_close_source,
 terminal_zmodem_open_received,terminal_zmodem_write_received,terminal_zmodem_commit,terminal_zmodem_abort_received};
unsigned __cdecl terminal_zmodem_store(unsigned sending)
{
 live_zmodem *p=(live_zmodem *)terminal_batch_buffer;unsigned status;
 terminal_zmodem_kbytes=0;terminal_zmodem_files=0;
 if(!sending && terminal_zmodem_receive_credit>8192){
  if(!terminal_transfer_fault)terminal_transfer_fault=7;return 1;
 }
 if(upload_source_result.handle_open || upload_source_result.handle_uncertain ||
  transfer_download_result.stage_exists || transfer_download_result.handle_open || transfer_download_result.handle_uncertain){
  terminal_transfer_cleanup_status=1;if(!terminal_transfer_fault)terminal_transfer_fault=7;return 1;
 }
 if(sending?batch_upload_begin(terminal_transfer_filename):batch_download_begin(terminal_transfer_filename)){
  if(!terminal_transfer_fault)terminal_transfer_fault=7;return 1;
 }
 p->observed=p->files=0;
 status=zm_run_checked_profile(&p->session,&terminal_zmodem_ops,p,sending,ymodem_io_modem()?300:0,
  sending?0:terminal_zmodem_receive_credit,sending?0:terminal_zmodem_verify_received);progress(p);
 if(upload_source_result.handle_uncertain || batch_download_result.file.handle_uncertain || batch_download_result.file.stage_exists)
  terminal_transfer_cleanup_status=1;
 if(!status)return 0;
 if(status==ZM_END_UNCONFIRMED)return 2;
 if(!terminal_transfer_fault)terminal_transfer_fault=status==ZM_CANCEL?2:status==ZM_TIMEOUT?3:status==ZM_IO?3:7;
 return 1;
}
