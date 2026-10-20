#include "native_program.h"
#include "native_display.h"
#include "process_serial.h"
#include <dos.h>
#include <string.h>
extern unsigned char native_display_mode;
extern unsigned native_display_viewport,native_display_cursor_start,native_display_cursor_end;
extern unsigned native_crt_error,native_dos_error;
extern char *program_ui_wait_message;
extern void __cdecl program_ui_cursor(unsigned);
extern void __cdecl program_ui_clear(unsigned);
extern void __cdecl program_ui_mode(unsigned);
extern void __cdecl program_ui_scanlines(unsigned);
extern void __cdecl program_ui_shape(void);
extern unsigned __cdecl program_ui_wait(void);
extern unsigned __cdecl program_ui_key_available(void);
unsigned native_program_busy,native_program_waiting;
static unsigned key_status;
static char wait_message[]="Press any key to continue ...";
static unsigned interrupt_flag(void);
#pragma aux interrupt_flag = "pushf" "pop ax" "and ax,0x200" value [ax] modify [];
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
/* Native WAIT tail-calls here. The maintained BIOS platform keeps the restored
 * UART ISR live, detects fatal input/flow errors, and consumes one local key.
 * No DOS read/CTRL-C checks or synthetic successful key results are used. */
unsigned __cdecl native_program_wait_key(void)
{
 union REGS in,out;unsigned status;
 for(;;){
  if(aspect_serial_active){status=aspect_serial_poll();if(status){key_status=status;return 65535U;}}
  if(program_ui_key_available()){in.h.ah=0;int86(0x16,&in,&out);return out.x.ax;}
 }
}
static unsigned restore_mode(unsigned mode,unsigned rows,unsigned height)
{
 union REGS in,out;
 /* Native7ee8 selects vertical scan lines before the native6f3e mode reset.
  * Standard ROM font selection follows the original application's policy. */
 program_ui_scanlines(rows==43||height==14?1:height==16||rows==50?2:0);
 program_ui_mode(mode);
 if(rows!=25){in.x.ax=0x1112;in.x.bx=0;int86(0x10,&in,&out);}
 if(native_display_probe()||native_display_mode!=mode||native_display_rows!=rows||
    *(unsigned __far *)MK_FP(0x40,0x85)!=height)return NATIVE_DISPLAY_STATE;
 return 0;
}
unsigned __cdecl native_program_execute(const char *program,const char *tail,
 unsigned processor,unsigned wait,unsigned save_screen,native_program_result *result)
{
 native_program_result local;union REGS in,out;
 unsigned mode,rows,columns,height,cursor,shape,changed,status;
 if(native_program_busy||native_program_waiting||native_process_busy||native_display_owned||
    aspect_process_serial_detached||aspect_serial_active==2)return NATIVE_PROGRAM_BUSY;
 /* Check before taking a near pointer to a stack local for memset/copy. */
 if(data_segment()!=stack_segment()||!result)return NATIVE_PROGRAM_ARGUMENT;
 memset(&local,0,sizeof(local));local.process.child_status=local.wait_key=65535U;
 local.process.status=NATIVE_PROCESS_STATE;
 if(!program||!*program||program[0]=='['||processor>1||wait>1||save_screen>1||!interrupt_flag()){
  local.status=NATIVE_PROGRAM_ARGUMENT;*result=local;return local.status;
 }
 native_program_busy=1;
 status=native_display_probe();if(status)goto display_rejected;
 mode=native_display_mode;rows=native_display_rows;columns=native_display_columns;
 height=*(unsigned __far *)MK_FP(0x40,0x85);
 /* Production renderer currently admits80x25 only. The composed diagnostic
  * also verifies native40-column and43/50-row standard ROM views. Arbitrary
  * downloadable fonts/adapters are not silently claimed as restored. */
 if((mode!=1&&mode!=2&&mode!=3&&mode!=7)||
    !((rows==25&&(height==8||height==14||height==16))||
      ((rows==43||rows==50)&&height==8))){status=NATIVE_DISPLAY_STATE;goto display_rejected;}
 in.h.ah=3;in.h.bh=0;int86(0x10,&in,&out);cursor=out.x.dx;shape=out.x.cx;
 if(save_screen){status=native_display_capture();if(status)goto display_rejected;}
 status=aspect_process_serial_pause();
 if(status){local.serial_status=status;local.status=NATIVE_PROGRAM_SERIAL;goto cleanup;}
 if(save_screen){program_ui_clear(7);program_ui_cursor(0x100);}
 /* Native PROGRAM clears errno before entering SYSTEM/spawnl. A previous
  * missing target must not become the next successful child's UI error. */
 native_crt_error=native_dos_error=0;
 if(processor)status=native_process_system(program,0,&local.process);
 else status=native_process_search(program,tail,0,&local.process);
 if(status)local.status=NATIVE_PROGRAM_PROCESS;
 /* Reclaim child-mutated UART/vector before any WAIT. Never lose queued
  * input to the original PROGRAM reset/uart_enable path's RBR discard. */
 local.serial_status=aspect_process_serial_resume();
 if(local.serial_status)local.status=NATIVE_PROGRAM_SERIAL;
 changed=native_display_probe()||native_display_mode!=mode||native_display_rows!=rows||
     native_display_columns!=columns||*(unsigned __far *)MK_FP(0x40,0x85)!=height;
 if(changed){
  local.display_status=restore_mode(mode,rows,height);
  if(local.display_status){local.status=NATIVE_PROGRAM_DISPLAY;goto cleanup;}
 }
 /* Native PROGRAM's special raw exit247 also requests a NOCLEAR view reset,
  * even when BIOS geometry itself is unchanged. The application owner must
  * consume this result when its actual renderer is bound. */
 if(!save_screen&&(changed||local.process.child_status==247))local.view_reset=1;
 if(wait&&!local.serial_status){
  program_ui_wait_message=wait_message;
  native_display_viewport=(rows-1)<<8;key_status=0;native_program_waiting=1;
  local.wait_key=program_ui_wait();native_program_waiting=0;
  if(key_status){local.serial_status=key_status;local.status=NATIVE_PROGRAM_SERIAL;}
 }
 if(save_screen){
  local.display_status=restore_mode(mode,rows,height);
  if(local.display_status){local.status=NATIVE_PROGRAM_DISPLAY;goto cleanup;}
  local.display_status=native_display_restore();
  if(local.display_status)local.status=NATIVE_PROGRAM_DISPLAY;
 }
 native_display_cursor_start=shape>>8;native_display_cursor_end=shape&255;
 program_ui_shape();program_ui_cursor(cursor);
 goto cleanup;
display_rejected:
 local.display_status=status;local.status=NATIVE_PROGRAM_DISPLAY;
cleanup:
 /* Failed capture/pause must leave the owner's previous view intact. A
  * failed restore is explicit and retires storage; it is never success. */
 if(native_display_owned)native_display_discard();
 native_program_waiting=native_program_busy=0;*result=local;return local.status;
}
