/* Maintained offline DOS settings UI; not a PCSETUP shared-memory child. */
#include "setup_document.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static setup_document document;
static setup_document_result result;
static unsigned saved_screen[2000];
static unsigned __far *video;
static unsigned page,cursor,shape;
static char edit[SETUP_TEXT_SIZE];
static const char *pages[]={"SERIAL","TERMINAL","MODEM","COMMANDS","RESPONSES"};
static void put(unsigned row,unsigned col,const char *s,unsigned attr,unsigned width)
{
 unsigned i;for(i=0;i<width && col+i<80;++i){
  video[row*80+col+i]=(unsigned)((attr<<8)|(unsigned char)(*s?*s++:' '));
 }
}
static unsigned key(void)
{
 union REGS r;r.h.ah=0;int86(0x16,&r,&r);return r.x.ax;
}
static void position(unsigned row,unsigned col)
{
 union REGS r;r.h.ah=2;r.h.bh=(unsigned char)page;r.h.dh=(unsigned char)row;r.h.dl=(unsigned char)col;int86(0x10,&r,&r);
}
static unsigned screen_start(void)
{
 union REGS r;unsigned mode,columns,offset,i;
 r.h.ah=15;int86(0x10,&r,&r);mode=r.h.al;columns=r.h.ah;page=r.h.bh;
 if(columns!=80 || (mode!=2 && mode!=3 && mode!=7))return 0;
 offset=*(unsigned __far *)MK_FP(0x40,0x4e);
 if(offset>61536U || (offset&1))return 0;
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
static void load_field(unsigned field,unsigned *pos,unsigned *dirty)
{
 if(setup_get(&document.staged,field,edit,sizeof(edit))!=SETUP_OK)edit[0]=0;
 *pos=(unsigned)strlen(edit);*dirty=0;
}
static unsigned commit(unsigned field,unsigned *dirty)
{
 if(!*dirty)return 1;
 if(setup_set(&document.baseline,&document.staged,field,edit)!=SETUP_OK)return 0;
 *dirty=0;return 1;
}
static unsigned first(unsigned page_number)
{ unsigned i;for(i=0;i<SETUP_FIELD_COUNT;++i)if(setup_field(i)->page==page_number)return i;return 0; }
static void draw(unsigned field,unsigned pos,const char *message)
{
 unsigned row=5,i,p=setup_field(field)->page;char text[SETUP_TEXT_SIZE];
 for(i=0;i<25;++i)put(i,0,"",0x17,80);
 put(0,0," PCPlus / SYSTEM CONFIGURATION",0x1f,80);
 put(1,2,document.target,0x1e,13);put(1,18,"Existing 2.01 image / mapped fields",0x17,45);
 put(3,2,pages[p],0x1e,20);
 for(i=0;i<SETUP_FIELD_COUNT;++i)if(setup_field(i)->page==p){
  put(row,2,setup_field(i)->label,i==field?0x70:0x17,22);
  if(i==field)strcpy(text,edit);
  else if(setup_get(&document.staged,i,text,sizeof(text))!=SETUP_OK)strcpy(text,"<INVALID - edit to repair>");
  put(row++,25,text,i==field?0x70:0x1f,53);
 }
 put(19,2,setup_field(field)->help,0x1e,76);
 put(21,2,message,0x1f,76);
 put(23,0," Tab/Arrows Field  PgUp/PgDn Page  F1 Help  F10 Save  Esc Discard",0x70,80);
 row=5+field-first(p);position(row,25+(pos<52?pos:52));
}
static unsigned run(void)
{
 unsigned field=0,pos,dirty,k,ascii,scan,len,next,insert=1;
 const char *message="Changes remain staged until F10. Response values use hex pairs.";
 load_field(field,&pos,&dirty);
 for(;;){
  draw(field,pos,message);k=key();ascii=k&255;scan=k>>8;len=(unsigned)strlen(edit);
  if(ascii==27){
   if(dirty || memcmp(&document.baseline,&document.staged,sizeof(document.baseline))){
    draw(field,pos,"Discard all unsaved changes? Y / N");k=key()&255;
    if(k!='y' && k!='Y')continue;
   }
   return 0;
  }
  if(scan==0x3b){
   draw(field,pos,"Edit values, then F10 to validate/save. Esc discards. Press any key.");key();continue;
  }
  if(scan==0x44){
   if(!commit(field,&dirty)){message="Invalid value. Check the field help below.";continue;}
   if(setup_document_save(&document,&result)==SETUP_DOCUMENT_OK){message="Settings saved. Escape returns to DOS.";}
   else if(result.status==SETUP_DOCUMENT_INVALID){
    field=result.bad_field<SETUP_FIELD_COUNT?result.bad_field:field;load_field(field,&pos,&dirty);
    message="Cannot save: repair the invalid field.";
   }else if(result.status==SETUP_DOCUMENT_CHANGED)message="File changed outside this editor. Discard and reopen to review.";
   else if(result.status==SETUP_DOCUMENT_LOCKED || document.locked)message="Recovery files retained: PRMEDIT.BAK / PRMEDIT.$$$. Exit and inspect.";
   else message="Save failed. Check file access and PRMEDIT.BAK / PRMEDIT.$$$.";
   continue;
  }
  if(ascii==9 || ascii==13 || scan==0x0f || scan==0x48 || scan==0x50 || scan==0x49 || scan==0x51){
   if(!commit(field,&dirty)){message="Invalid value. Correct it before leaving this field.";continue;}
   if(scan==0x49 || scan==0x51){next=setup_field(field)->page;next=(next+(scan==0x51?1:4))%5;field=first(next);}
   else if((scan==0x0f && ascii!=9) || scan==0x48)field=field?field-1:SETUP_FIELD_COUNT-1;
   else field=(field+1)%SETUP_FIELD_COUNT;
   load_field(field,&pos,&dirty);message="Changes remain staged until F10.";continue;
  }
  if(scan==0x4b){if(pos)--pos;continue;}
  if(scan==0x4d){if(pos<len)++pos;continue;}
  if(scan==0x47){pos=0;continue;}if(scan==0x4f){pos=len;continue;}
  if(scan==0x52){insert=!insert;continue;}
  if(scan==0x53){if(pos<len){memmove(edit+pos,edit+pos+1,len-pos);dirty=1;}continue;}
  if(ascii==8){if(pos){--pos;memmove(edit+pos,edit+pos+1,len-pos);dirty=1;}continue;}
  if(ascii>=32 && ascii!=127){
   if(insert || pos==len){if(len>=SETUP_TEXT_SIZE-1)continue;memmove(edit+pos+1,edit+pos,len-pos+1);}
   edit[pos++]=(char)ascii;dirty=1;
  }
 }
}
int main(int argc,char **argv)
{
 unsigned status;
 if(argc!=2){puts("Usage: PRMEDIT filename.PRM\nRun in the settings directory. Existing 2.01 files only.");return 1;}
 /* argv strings need only their real extent; copy into the bounded API buffer. */
 if(strlen(argv[1])>12){puts("Use an 8.3 leaf filename in the current directory.");return 1;}
 memset(edit,0,sizeof(edit));strcpy(edit,argv[1]);
 status=setup_document_open(edit,&document,&result);
 if(status!=SETUP_DOCUMENT_OK){printf("Cannot open settings: status %u, DOS error %u.\n",status,result.io.dos_error);return 2;}
 if(!screen_start()){puts("PRMEDIT requires an 80-column text screen (mode 2, 3 or 7).");return 3;}
 status=run();screen_end();return (int)status;
}
