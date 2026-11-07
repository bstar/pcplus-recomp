#include <stdio.h>
#include <string.h>
#include "keymap_screen.h"
#include "keymap_text.h"
static const char *profiles[33]={
 "TTY     ","VT52    ","VT100   ","VT102   ","VT220   ","VT320   ","ANSI    ","IBM PC  ","WYSE 75 ","ATT 605 ","ATT 4410",
 "TVI 922 ","HEATH 19","IBM 3101","IBM 3161","DG D100 ","DG D200 ","DG D210 ","ADDS 60 ","ADDS 90 ","ADM 3A  ","ADM 5   ","ADM 31  ","ESPRIT 3","3270/950","TVI 910 ","TVI 912 ","TVI 920 ","TVI 925 ","TVI 950 ","TVI 955 ","WYSE 50 ","WYSE 100"};
static const unsigned positions[79]={
 0x060a,0x070a,0x080a,0x090a,0x0a0a,0x0b0a,0x0e0c,0x0f0c,0x100c,0x110c,0x120c,0x130c,0x140c,0x150c,0x160c,0x170c,
 0x0120,0x0220,0x0320,0x0420,0x0520,0x0620,0x0720,0x0820,0x0920,0x0a20,0x0b20,0x0c20,
 0x0e20,0x0f20,0x1020,0x1120,0x1220,0x1320,0x1420,0x1520,0x1620,0x1720,
 0x0135,0x0235,0x0335,0x0435,0x0535,0x0635,0x0735,0x0835,0x0935,0x0a35,0x0b35,0x0c35,
 0x0e35,0x0f35,0x1035,0x1135,0x1235,0x1335,0x1435,0x1535,0x1635,0x1735,
 0x0146,0x0246,0x0346,0x0446,0x0546,0x0646,0x0746,0x0846,0x0946,0x0a46,0x0b46,0x0c46,
 0x0e46,0x0f46,0x1046,0x1146,0x1346,0x1446,0x1646};
static const unsigned keys[79]={
 0x372a,0x4a2d,0x4e2b,0x532e,0xe02f,0xe00d,9,0x0f00,0x5200,0x5300,0x0e08,0x7700,0x7500,0x8400,0x7600,0x0e7f,
 0x3b00,0x3c00,0x3d00,0x3e00,0x3f00,0x4000,0x4100,0x4200,0x4300,0x4400,0x8500,0x8600,
 0x5230,0x4f31,0x5032,0x5133,0x4b34,0x4c35,0x4d36,0x4737,0x4838,0x4939,
 0x5400,0x5500,0x5600,0x5700,0x5800,0x5900,0x5a00,0x5b00,0x5c00,0x5d00,0x8700,0x8800,
 0x48e0,0x50e0,0x4be0,0x4de0,0x52e0,0x53e0,0x47e0,0x4fe0,0x49e0,0x51e0,
 0x5e00,0x5f00,0x6000,0x6100,0x6200,0x6300,0x6400,0x6500,0x6600,0x6700,0x8900,0x8a00,
 0x4800,0x5000,0x4b00,0x4d00,0x4700,0x4f00,13};
unsigned keymap_screen_key(unsigned key)
{
 unsigned i;
 for(i=0;i<79;++i)if(keys[i]==key)return i;
 if(key==32 || key==0x5100)return KEYMAP_NEXT;
 if(key==0x4900)return KEYMAP_PREVIOUS;
 if(key==0x1800)return KEYMAP_OPEN;
 if(key==0x1f00)return KEYMAP_SAVE;
 if(key==27 || key==0x2d00)return KEYMAP_EXIT;
 if(key==0x2c00)return KEYMAP_ABOUT;
 if(key>=0x7800 && key<=0x8100 && !(key&255))return KEYMAP_RESERVED;
 return KEYMAP_INVALID;
}
unsigned keymap_screen_position(unsigned slot){return slot<79?positions[slot]:0xffff;}
const char *keymap_screen_profile(unsigned profile){return profile<33?profiles[profile]:0;}
static void text(unsigned short *frame,unsigned row,unsigned col,const char *s,unsigned attr)
{
 while(*s && col<80){frame[row*80+col++]=(unsigned char)*s+++(attr<<8);}
}
unsigned keymap_screen_render(unsigned short *frame,unsigned profile,const unsigned char *bindings,const char *leaf)
{
 static const char *left[]={"TAB .......","BACKTAB ...","INSERT ....","DELETE ....","BACKSPACE .","C-HOME ....","C-END .....","C-PGUP ....","C-PGDN ....","C-BACKSPACE"};
 static const char *grey[]={"GREY CUP","GREY CDN","GREY CLF","GREY CRT","GREY INS","GREY DEL","GREY HOME","GREY END","GREY PGUP","GREY PGDN"};
 static const char *cursor[]={"CURUP","CURDN","CURLF","CURRT","","HOME","END","","ENTER",""};
 static const char *pad[]={"KEYPAD *","KEYPAD -","KEYPAD +","KEYPAD .","KEYPAD /","KEY ENTER"};
 unsigned i,j,col,row,n;int length;char label[100];unsigned char value[34];
 if(!frame || !bindings || !leaf || profile>=33)return 0;
 for(i=0;i<13 && leaf[i];++i){}if(i==13)return 0;
 for(i=0;i<2000;++i)frame[i]=0x1720;
 for(i=0;i<80;++i){frame[i]=0x17cd;frame[13*80+i]=0x17cd;}
 frame[21]=0x17cb;frame[13*80+21]=0x17ca;
 for(i=1;i<13;++i)frame[i*80+21]=0x17ba;
 for(i=0;i<21;++i)frame[4*80+i]=0x17cd;
 frame[4*80+21]=0x17b9;
 text(frame,1,0,"    PROCOMM PLUS",31);text(frame,2,0,"  KEYBOARD MAPPING",31);text(frame,3,0,"    Version 2.01",31);
 for(i=1;i<=12;++i){
  sprintf(label,"F%u %s",i,i<10?".....":"....");text(frame,i,23,label,23);
  sprintf(label,"S-F%u %s",i,i<10?"....":"...");text(frame,i,43,label,23);
  sprintf(label,"C-F%u",i);text(frame,i,64,label,23);
 }
 for(i=0;i<6;++i)text(frame,6+i,0,pad[i],23);
 for(i=0;i<10;++i){
  text(frame,14+i,0,left[i],23);sprintf(label,"KEYPAD %u",i);text(frame,14+i,23,label,23);
  text(frame,14+i,43,grey[i],23);text(frame,14+i,64,cursor[i],23);
 }
 for(i=0;i<79;++i){
  row=positions[i]>>8;col=positions[i]&255;
  for(j=0;j<10;++j)frame[row*80+col+j]=0x1f20;
  for(n=0;n<12 && bindings[i*12+n];++n){}
  length=n<12?keymap_text_encode(bindings+i*12,n,value,sizeof(value)):-1;
  if(length<0)text(frame,row,col,"[RAW]",31);
  else{
   for(j=0;j<(unsigned)length && j<10;++j)frame[row*80+col+j]=0x1f00+value[j];
   if(length>10)frame[row*80+col+9]=0x1f2b;
  }
 }
 for(i=1920;i<2000;++i)frame[i]=0x7120;
 sprintf(label," %s\263 PgUp/Dn:Terminals \263 Alt-O:Open \263 Alt-S:Save \263 Esc:Exit \263 %-12s",profiles[profile],leaf);
 text(frame,24,0,label,113);return 1;
}
