/* Diagnostic only. Called in real foreground after normal geometry capture,
 * with UART enabled before dial. Snapshot and output are outside production services. */
#include <dos.h>
#include "../src/terminal/status_transition.h"
typedef status_word word;
#define TEXT __based(__segname("_CODE"))
extern unsigned __far __cdecl probe_write(const char *,const void __far *,unsigned);
#pragma aux probe_write "status_probe_write";
extern void __far __cdecl probe_poll(void);
#pragma aux probe_poll "status_probe_poll";
extern unsigned __far __cdecl probe_ticks(void);
#pragma aux probe_ticks "status_probe_ticks";
extern void __far __cdecl probe_ris(void);
#pragma aux probe_ris "status_probe_ris";
static const char TEXT names[14][13]={"S0.BIN","T0.BIN","S1.BIN","T1.BIN","S2.BIN","T2.BIN","S3.BIN","T3.BIN","S4.BIN","T4.BIN","S5.BIN","T5.BIN","R4.BIN","R5.BIN"};
static word captured_rows(void)
{
 word i;for(i=0;reset_word_addresses+i<reset_word_addresses_end;++i)
  if(reset_word_addresses[i]==(word)&csi_row_count)return reset_words[i];
 return 65535U;
}
static word wait_cursor(word row,word column,word wrap,word saved)
{
 word started=probe_ticks();
 while((word)(probe_ticks()-started)<90){
  probe_poll();
  if(screen_cursor_row==row && screen_cursor_column==column && csi_wrap_pending==wrap &&
     (saved==65535U || csi_saved_row==saved))return 0;
 }
 return 1;
}
static word write(word index,const void __far *bytes,word size)
{char name[13];word i;for(i=0;i<13;++i)name[i]=names[index][i];return probe_write(name,bytes,size);}
static word capture(word phase,word status)
{
 word state[22],hw=0;
 __asm {
 mov ah,3
 xor bx,bx
 int 10h
 mov hw,dx
 }
 state[0]=phase;state[1]=status;state[2]=csi_row_count;state[3]=csi_last_row;
 state[4]=screen_last_row;state[5]=csi_origin_bottom;state[6]=erase_cell_count;
 state[7]=ui_flow_suppressed;state[8]=screen_cursor_row;state[9]=screen_cursor_column;
 state[10]=screen_previous_row;state[11]=screen_previous_column;
 state[12]=screen_video_offset;state[13]=screen_attribute_offset;
 state[14]=csi_saved_row;state[15]=csi_wrap_pending;state[16]=captured_rows();
 state[17]=hw;state[18]=*(unsigned char __far *)MK_FP(0x40,0x84);
 state[19]=terminal_status_toggle_active;state[20]=ui_flow_attribute;state[21]=attributes_current;
 if(write(phase*2,(const void __far *)MK_FP(0xb800,0),4000))return 1;
 return write(phase*2+1,(const void __far *)state,sizeof(state));
}
unsigned __far __cdecl terminal_status_probe(void)
{
 word i,status;word __far *video=(word __far *)MK_FP(0xb800,0);
 for(i=0;i<2000;++i){video[i]=0x0700|'A'+i/80;screen_attribute_cells[i]=(unsigned char)(i%251);erase_attribute_values[i]=7;}
 if(capture(0,0))return 20;
 status=terminal_status_toggle();if(capture(1,status))return 21;if(status)return 31;
 if(wait_cursor(24,7,0,24))return 50;status=terminal_status_toggle();if(capture(2,status))return 22;if(status)return 32;
 probe_ris();if(capture(3,0))return 23;
 if(wait_cursor(5,79,1,65535U))return 51;
 status=terminal_status_toggle();if(status)return 34;if(csi_wrap_pending!=1)return 41;
 if(write(12,(const void __far *)&status,2))return 26;
 if(wait_cursor(6,1,0,65535U))return 52;
 if(capture(4,status))return 24;
 if(wait_cursor(5,79,1,65535U))return 53;
 status=terminal_status_toggle();if(status)return 35;if(csi_wrap_pending!=1)return 43;
 if(write(13,(const void __far *)&status,2))return 27;
 if(wait_cursor(6,1,0,65535U))return 54;
 if(capture(5,status))return 25;
 return 0;
}
