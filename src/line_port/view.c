/* Maintained renderer from native Alt-P observations, not extracted UI bytes. */
#include "view.h"
typedef unsigned word;
#define TEXT __based(__segname("_CODE"))
static const char TEXT heading[]="BAUD RATE   PARITY     DATA BITS   STOP BITS   PORT";
static const char TEXT footer[]="Esc) Exit   Alt-S) Save and Exit  YOUR CHOICE:";
static const char TEXT title[]="LINE/PORT SETUP";
static const char TEXT current[]="CURRENT SETTINGS:";
static const char TEXT rates[]="300\0\0\0\0" "1200\0\0\0" "2400\0\0\0" "4800\0\0\0" "9600\0\0\0" "19200\0\0" "38400\0\0" "57600\0\0" "115200";
static const char TEXT parity_letters[]="NOEMS";
static const char TEXT parity_rows[]="N) NONE\0" "E) EVEN\0" "O) ODD\0\0" "M) MARK\0" "S) SPACE";
static const char TEXT preset_n[]="Alt-N) N/8/1";
static const char TEXT preset_e[]="Alt-E) E/7/1";
static void text(word __far *f,word at,const char __far *s,word attr)
{while(*s)f[at++]=attr|(unsigned char)*s++;}
static word length(const char __far *s)
{word n=0;while(s[n])++n;return n;}
unsigned __far __cdecl line_port_view(const line_port_values *v,word __far *f,word cells)
{
 word r,c,n,at;
 /* Materialize far pointers before indexed arithmetic: based-pointer
  * expressions otherwise lose their code-segment frame in this toolchain. */
 const char __far *rate_text=rates;
 const char __far *parity_text=parity_rows;
 if(!v || !f || cells<2000 || v->port>7 || v->baud>8 || v->parity>4 ||
    (v->stop!=1 && v->stop!=2) || (v->bits!=7 && v->bits!=8))return 1;
 for(r=2;r<=19;++r)for(c=18;c<=76;++c)f[r*80+c]=0x0720;
 for(c=19;c<76;++c)f[2*80+c]=f[4*80+c]=f[19*80+c]=0x07cd;
 for(r=3;r<19;++r)f[r*80+18]=f[r*80+76]=0x07ba;
 f[2*80+18]=0x07c9;f[2*80+76]=0x07bb;
 f[4*80+18]=0x07cc;f[4*80+76]=0x07b9;
 f[19*80+18]=0x07c8;f[19*80+76]=0x07bc;
 text(f,3*80+31,current,0x0b00);
 /* Refresh writes a fixed-width six-character baud label. */
 for(c=48;c<54;++c)f[3*80+c]=0x0b20;
 n=length((rate_text+v->baud*7));text(f,3*80+54-n,(rate_text+v->baud*7),0x0b00);
 at=3*80+54;
 f[at++]=0x0b2c;f[at++]=0x0b00|parity_letters[v->parity];
 f[at++]=0x0b2c;f[at++]=0x0b30+v->bits;
 f[at++]=0x0b2c;f[at++]=0x0b30+v->stop;
 f[at++]=0x0b2c;text(f,at,"COM",0x0b00);at+=3;
 f[at]=0x0b31+v->port;
 text(f,6*80+20,heading,0x0b00);
 for(r=0;r<9;++r){
  at=(8+r)*80;
  f[at+20]=0x0731+r;f[at+21]=0x0729;
  n=length((rate_text+r*7));text(f,at+29-n,(rate_text+r*7),0x0700);
  if(r<5)text(f,at+32,(parity_text+r*8),0x0700);
  if(r<2){
   text(f,at+43,r?"Alt-8) 8":"Alt-7) 7",0x0700);
   text(f,at+55,r?"Alt-2) 2":"Alt-1) 1",0x0700);
  }
  if(r<8){text(f,at+67,"F1) COM1",0x0700);f[at+68]=0x0731+r;f[at+74]=0x0731+r;}
  if(r==7)text(f,at+32,preset_n,0x0700);
  if(r==8)text(f,at+32,preset_e,0x0700);
 }
 text(f,18*80+20,footer,0x0b00);
 for(c=0;c<80;++c)f[24*80+c]=0x7120;
 text(f,24*80+32,title,0x7100);
 return 0;
}
