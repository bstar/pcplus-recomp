#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "keymap_screen.h"
static unsigned short frame[2000],expected[2000],observed[2000];
static unsigned char bindings[948];
int main(void)
{
 FILE *f;unsigned long key;unsigned p;int action;
 f=fopen("KEYS.BIN","rb");if(!f)return 1;
 for(key=0;key<65536UL;++key){action=fgetc(f);if(action==EOF || keymap_screen_key((unsigned)key)!=(unsigned)action)return 2;}
 if(fgetc(f)!=EOF || fclose(f))return 3;
 f=fopen("FRAMES.BIN","rb");if(!f)return 4;
 for(p=0;p<33;++p){
  if(fread(expected,1,4000,f)!=4000 || !keymap_screen_render(frame,p,bindings,"SYN.KBD") || memcmp(frame,expected,4000))return 5;
  movedata(FP_SEG(frame),FP_OFF(frame),0xb800,0,4000);
  movedata(0xb800,0,FP_SEG(observed),FP_OFF(observed),4000);
  if(memcmp(observed,expected,4000))return 6;
 }
 if(fgetc(f)!=EOF || fclose(f))return 7;
 puts("PASS 65536 KEYS 33 VGA FRAMES");return 0;
}
