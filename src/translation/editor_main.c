/* Source-owned offline DOS XLT editor. F1/F2/F3/F4 follow the recovered surface. */
#include "editor_document.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static xlt_document document;
static xlt_document_result result;
static unsigned saved_screen[2000],page,cursor,shape;
static unsigned __far *video;
static void put(unsigned row,unsigned col,const char *s,unsigned attr,unsigned width)
{unsigned i;for(i=0;i<width && col+i<80;++i)video[row*80+col+i]=(attr<<8)|(unsigned char)(*s?*s++:' ');}
static unsigned key(void)
{union REGS r;r.h.ah=0;int86(0x16,&r,&r);return r.x.ax;}
static void position(unsigned row,unsigned col)
{union REGS r;r.h.ah=2;r.h.bh=(unsigned char)page;r.h.dh=(unsigned char)row;r.h.dl=(unsigned char)col;int86(0x10,&r,&r);}
static unsigned screen_start(void)
{
 union REGS r;unsigned mode,columns,offset,i;
 r.h.ah=15;int86(0x10,&r,&r);mode=r.h.al;columns=r.h.ah;page=r.h.bh;
 if(columns!=80 || (mode!=2 && mode!=3 && mode!=7))return 0;
 offset=*(unsigned __far *)MK_FP(0x40,0x4e);if(offset>61536U || (offset&1))return 0;
 video=(unsigned __far *)MK_FP(mode==7?0xb000:0xb800,offset);
 for(i=0;i<2000;++i)saved_screen[i]=video[i];
 r.h.ah=3;r.h.bh=(unsigned char)page;int86(0x10,&r,&r);cursor=r.x.dx;shape=r.x.cx;
 r.h.ah=1;r.x.cx=0x0607;int86(0x10,&r,&r);return 1;
}
static void screen_end(void)
{
 union REGS r;unsigned i;for(i=0;i<2000;++i)video[i]=saved_screen[i];
 r.h.ah=1;r.x.cx=shape;int86(0x10,&r,&r);r.h.ah=2;r.h.bh=(unsigned char)page;r.x.dx=cursor;int86(0x10,&r,&r);
}
static void draw(unsigned selected,const char *message)
{
 unsigned i,base=selected&128,attr;char text[80];
 for(i=0;i<25;++i)put(i,0,"",0x17,80);
 put(0,0," PCPlus / CHARACTER TRANSLATION",0x1f,80);
 sprintf(text," %s  %s%s",document.target,document.exists?"":"NEW / ",xlt_document_dirty(&document)?"CHANGED":"SAVED");put(1,0,text,0x1e,80);
 sprintf(text," INPUT > OUTPUT / DECIMAL       PAGE %u / 2",base?2:1);put(2,0,text,0x1e,80);
 for(i=base;i<base+128;++i){
  attr=i==selected?0x70:document.staged[i]==i?0x17:0x1e;
  sprintf(text,"%03u>%03u",i,(unsigned)document.staged[i]);put(4+(i-base)%16,2+(i-base)/16*9,text,attr,8);
 }
 put(21,2,message,0x1f,76);
 put(23,0," F1 Save  F2 Page  F3 Reload  F4 Identity  G Go to  Enter Edit  Esc Exit",0x70,80);
 position(4+(selected-base)%16,2+(selected-base)/16*9+4);
}
static unsigned confirm(unsigned selected,const char *message)
{unsigned k;draw(selected,message);k=key()&255;return k=='y' || k=='Y';}
static unsigned number(unsigned selected,const char *label,unsigned initial,unsigned *out)
{
 char edit[4],message[80];unsigned pos,len,k,scan,c,i,value;
 sprintf(edit,"%u",initial);pos=len=(unsigned)strlen(edit);
 for(;;){
  sprintf(message,"%s [0..255]: %s   Enter accepts / Esc cancels",label,edit);draw(selected,message);
  k=key();c=k&255;scan=k>>8;
  if(c==27)return 0;
  if(c==13){if(!len)continue;value=0;for(i=0;i<len;++i)value=value*10+edit[i]-'0';if(value<=255){*out=value;return 1;}continue;}
  if(scan==0x47){pos=0;continue;}if(scan==0x4f){pos=len;continue;}
  if(scan==0x4b){if(pos)--pos;continue;}if(scan==0x4d){if(pos<len)++pos;continue;}
  if(scan==0x53){if(pos<len){memmove(edit+pos,edit+pos+1,len-pos);--len;}continue;}
  if(c==8){if(pos){--pos;memmove(edit+pos,edit+pos+1,len-pos);--len;}continue;}
  if(c>='0' && c<='9' && len<3){memmove(edit+pos+1,edit+pos,len-pos+1);edit[pos++]=(char)c;++len;}
 }
}
static const char *saved(void)
{
 if(xlt_document_save(&document,&result)==XE_OK)return "Table saved.";
 if(document.locked)return result.installed?"Installed, but recovery cleanup failed. Inspect XLTEDIT.BAK / XLTEDIT.$$$.":"Recovery files retained. Exit and inspect XLTEDIT.BAK / XLTEDIT.$$$.";
 if(result.status==XE_CHANGED)return "File changed outside this editor. Reload to review before saving.";
 return "Save failed. Changes retained. Check access and XLTEDIT.BAK / XLTEDIT.$$$.";
}
static void run(void)
{
 unsigned selected=0,k,c,scan,value;char path[13];const char *message="Select a byte with arrows; Enter changes its replacement.";
 for(;;){
  draw(selected,message);k=key();c=k&255;scan=k>>8;
  if(c==27){if(!xlt_document_dirty(&document) || confirm(selected,"Discard unsaved changes and exit? Y / N"))return;continue;}
  if(scan==0x3b){message=saved();continue;}
  if(scan==0x3c || scan==0x49 || scan==0x51){selected^=128;continue;}
  if(scan==0x3d){
   if(xlt_document_dirty(&document) && !confirm(selected,"Discard unsaved changes and reload from disk? Y / N"))continue;
   memcpy(path,document.target,13);
   message=xlt_document_open(path,0,&document,&result)==XE_OK?"Table reloaded.":"Reload failed. Current changes retained.";continue;
  }
  if(scan==0x3e){message=xlt_document_identity(&document)==XE_OK?"Identity staged. F1 saves; Esc can discard.":"Recovery state is locked. Exit and inspect files.";continue;}
  if(c=='g' || c=='G'){if(number(selected,"Source byte",selected,&value))selected=value;continue;}
  if(c==13){if(number(selected,"Replacement byte",document.staged[selected],&value))message=xlt_document_set(&document,selected,value)==XE_OK?"Mapping changed; F1 saves.":"Recovery state is locked. Exit and inspect files.";continue;}
  if(scan==0x48){selected=(selected&240)|((selected-1)&15);continue;}
  if(scan==0x50){selected=(selected&240)|((selected+1)&15);continue;}
  if(scan==0x4b){selected=(selected&128)|((selected-16)&127);continue;}
  if(scan==0x4d){selected=(selected&128)|((selected+16)&127);continue;}
  if(scan==0x47){selected&=128;continue;}if(scan==0x4f){selected=(selected&128)|127;continue;}
 }
}
int main(int argc,char **argv)
{
 char path[13];unsigned create=0;
 if(argc==3 && !strcmp(argv[1],"/N")){create=1;++argv;--argc;}
 if(argc!=2 || strlen(argv[1])>12){puts("Usage: XLTEDIT [/N] filename.XLT\n/N stages a new identity table; F1 creates it. Use an 8.3 leaf.");return 1;}
 memset(path,0,13);strcpy(path,argv[1]);
 if(xlt_document_open(path,create,&document,&result)){printf("Cannot open table: status %u, DOS error %u.\n",result.status,result.dos_error?result.dos_error:result.io.dos_error);return 2;}
 if(!screen_start()){puts("XLTEDIT requires an 80-column text screen (mode 2, 3 or 7).");return 3;}
 run();screen_end();return 0;
}
