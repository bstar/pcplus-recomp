/* Maintained full-height PROGRAM display lease around recovered BIOS services. */
#include <dos.h>
#include "program_display.h"
#include "row_geometry.h"
#include "../process/native_display_rows.h"
typedef unsigned short word;
extern word ui_window_rows,terminal_quit,terminal_exit_code,csi_unimplemented_service;
#pragma aux ui_window_rows "ui_window_rows";
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux csi_unimplemented_service "csi_unimplemented_service";
extern word program_cursor,program_shape;
#pragma aux program_cursor "program_cursor";
#pragma aux program_shape "program_shape";
extern word __far program_screen[];
extern word __far program_screen_end[];
#pragma aux program_screen "program_screen";
#pragma aux program_screen_end "program_screen_end";
unsigned program_display_ready=0;
static word saved_rows=25;
static word context(void)
{
 word d=0,s=0,f=0;
 __asm { mov ax,ds
 mov d,ax
 mov ax,ss
 mov s,ax
 pushf
 pop ax
 mov f,ax }
 return d==s && (f&0x600)==0x200;
}
static word capacity(void)
{return FP_SEG(program_screen)==FP_SEG(program_screen_end) &&
 FP_OFF(program_screen_end)-FP_OFF(program_screen)==8000U;}
static word mode(void)
{
 word a=0,b=0;
 __asm { mov ah,0fh
 push bp
 int 10h
 pop bp
 mov a,ax
 mov b,bx }
 return a==0x5003 && !(b&0xff00);
}
static word legal(word rows){return rows==25 || rows==28 || rows==43 || rows==50;}
static word geometry(const native_display_rows_info *p,word rows)
{return p->mode==3 && p->columns==80 && p->rows==rows && p->segment==0xb800 && p->stride==160 && p->cells==rows*80;}
static word failed(void)
{
 program_display_ready=0;terminal_quit=1;terminal_exit_code=2;
 csi_unimplemented_service=0x6ef7;return 3;
}
unsigned __far __cdecl program_display_save(void)
{
 native_display_rows_info before;word i,xy=0,shape=0;
 word __far *video=(word __far *)MK_FP(0xb800,0);
 if(!context())return 1;
 if(program_display_ready)return 2;
 if(!capacity() || !mode() || native_display_rows_probe(&before))return 1;
 if(!legal(before.rows) || !geometry(&before,before.rows) || ui_window_rows!=before.rows)return 1;
 /* Preserve existing25-row logical-wide ownership; larger frames require the
  * composed narrow canonical layout used by the row selector. */
 if(before.rows!=25 && terminal_row_status_layout())return 1;
 __asm { mov ah,3
 xor bh,bh
 push bp
 int 10h
 pop bp
 mov xy,dx
 mov shape,cx }
 if((xy>>8)>=before.rows || (xy&255)>=80)return 1;
 for(i=0;i<before.cells;++i)program_screen[i]=video[i];
 program_cursor=xy;program_shape=shape;saved_rows=before.rows;
 program_display_ready=1;return 0;
}
unsigned __far __cdecl program_display_restore(void)
{
 native_display_rows_info actual;word status,i,xy,shape;
 word __far *video=(word __far *)MK_FP(0xb800,0);
 if(!context())return 3; /* Invalid ABI cannot safely publish near state. */
 if(program_display_ready!=1 || !capacity() || !legal(saved_rows) || ui_window_rows!=saved_rows)return failed();
 if(saved_rows!=25 && terminal_row_status_layout())return failed();
 __asm { mov ax,3
 push bp
 int 10h
 pop bp }
 status=native_display_rows_set(saved_rows,&actual);
 if((status!=DISPLAY_ROWS_OK && status!=DISPLAY_ROWS_FAILED) || !mode() || !geometry(&actual,saved_rows))return failed();
 for(i=0;i<actual.cells;++i)video[i]=program_screen[i];
 xy=program_cursor;shape=program_shape;
 __asm { mov ah,1
 mov cx,shape
 push bp
 int 10h
 pop bp
 mov ah,2
 xor bh,bh
 mov dx,xy
 push bp
 int 10h
 pop bp }
 program_display_ready=0;return 0;
}
