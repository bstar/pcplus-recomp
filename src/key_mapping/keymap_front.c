/* Foreground PCKEYMAP child. No serial, resident callbacks or private defaults. */
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include "keymap_screen.h"
#include "keymap_field.h"
#include "keymap_text.h"
#include "kbd_editor_file.h"
static unsigned char bindings[KBD_EDITOR_BYTES];
static unsigned short frame[2000],saved[2000];
static unsigned char __far *baseline;
static char target[64],leaf[13];
static unsigned profile,dirty,held,legacy,shape,old_cursor,page;
static unsigned short __far *video;
static unsigned raw_key(void)
{union REGS a,b;a.h.ah=(unsigned char)(legacy?0:0x10);int86(0x16,&a,&b);return b.x.ax;}
static unsigned menu_key(unsigned key)
{
 unsigned lo=key&255,hi=key>>8;
 if(!lo || lo==0xe0 || hi==0xe0 || key==0x0e08 || key==0x0e7f)return key;
 if(key==0x3920 || (short)key<(short)0x372a)return lo;
 return key;
}
static unsigned field_key(unsigned key)
{
 unsigned lo=key&255;
 if(!(key&0xf000))return key;
 if(lo==0xe0)return key&0xff00;
 return lo?lo:key;
}
static void cursor(unsigned position,unsigned appearance)
{
 union REGS a,b;a.h.ah=1;a.x.cx=appearance;int86(0x10,&a,&b);
 a.h.ah=2;a.h.bh=(unsigned char)page;a.x.dx=position;int86(0x10,&a,&b);
}
static void paint(void)
{unsigned i;for(i=0;i<2000;++i)if(frame[i]!=video[i])video[i]=frame[i];}
static void row_text(unsigned row,unsigned col,const char *s,unsigned attr)
{while(*s && col<80)frame[row*80+col++]=(unsigned char)*s+++(attr<<8);}
static void footer(const char *message)
{unsigned i;for(i=1920;i<2000;++i)frame[i]=0x7120;row_text(24,1,message,113);}
static void notice(const char *message)
{footer(message);paint();cursor(0,shape|0x2000);raw_key();}
static void redraw(void)
{keymap_screen_render(frame,profile,bindings+profile*948,leaf);paint();cursor(0,shape|0x2000);}
static unsigned recovery(const directory_replace_result *r)
{return r->close_error || r->rollback_error || r->original_in_backup || r->stage_exists;}
static unsigned canonical(const char *name,char *path)
{
 char stage[64],backup[64];
 return _fullpath(path,name,64)!=0 && !kbd_editor_file_paths(path,stage,backup);
}
static void set_leaf(void)
{const char *p=target,*q=target;while(*p){if(*p=='\\' || *p==':')q=p+1;++p;}strcpy(leaf,q);}
static unsigned save(void)
{
 directory_replace_result r;unsigned e;
 memset(&r,0,sizeof(r));e=kbd_editor_file_save(target,baseline,bindings,&r);
 if(e){
  if(recovery(&r)){held=1;notice("KBD recovery required. Retained files must be checked. Press a key.");}
  else notice("Save failed; definitions remain in memory. Press a key.");
  return 0;
 }
 _fmemcpy(baseline,bindings,KBD_EDITOR_BYTES);dirty=0;return 1;
}
/* Return0 cancels the request;1 means discard or a successful save. */
static unsigned leave_dirty(void)
{
 unsigned key;
 if(!dirty)return 1;
 for(;;){
  footer("Save changes (Y/N)? Esc cancels.");paint();cursor(0,shape|0x2000);key=field_key(menu_key(raw_key()));
  if(key=='y' || key=='Y')return save();
  if(key=='n' || key=='N')return 1;
  if(key==27)return 0;
 }
}
static unsigned prompt_name(char *name)
{
 unsigned n=0,key,i;name[0]=0;
 for(;;){
  footer("Open keyboard file: ");row_text(24,21,name,113);paint();cursor(0x1800+21+n,shape&0x1f1f);
  key=field_key(menu_key(raw_key()));
  if(key==27)return 0;
  if(key==13){if(n)return 1;continue;}
  if(key==0x0e08 || key==8){if(n)name[--n]=0;continue;}
  if(key>='a' && key<='z')key-=32;
  if(n<8 && ((key>='A' && key<='Z') || (key>='0' && key<='9') || key=='_')){name[n++]=(char)key;name[n]=0;}
  for(i=n;i<9;++i)name[i]=0;
 }
}
static void open_file(void)
{
 char name[13],path[64];directory_replace_result r;unsigned e;
 if(!leave_dirty() || held)return;
 if(!prompt_name(name))return;
 strcat(name,".KBD");if(!canonical(name,path)){notice("Invalid keyboard filename. Press a key.");return;}
 /* A confirmed No discards edits only after a filename is accepted. The
  * old saved image remains in bindings while load stages into the released
  * far block; this avoids three simultaneous full KBD images under the parent. */
 if(dirty){_fmemcpy(bindings,baseline,KBD_EDITOR_BYTES);dirty=0;}
 _ffree(baseline);baseline=0;
 memset(&r,0,sizeof(r));e=kbd_editor_file_load(path,bindings,&r);
 baseline=_fmalloc(KBD_EDITOR_BYTES);
 if(!baseline){held=1;notice("Insufficient memory; no file was replaced. Press a key.");return;}
 _fmemcpy(baseline,bindings,KBD_EDITOR_BYTES);
 if(e){if(r.close_error)held=1;notice("Open failed; previous saved file retained. Press a key.");return;}
 strcpy(target,path);set_leaf();dirty=0;
}
static void edit(unsigned slot)
{
 unsigned at=profile*948+slot*12,n,key,status,i,pos=keymap_screen_position(slot);
 int length;unsigned char notation[34],replacement[12];keymap_field_state field;
 for(n=0;n<12 && bindings[at+n];++n){}
 length=n<12?keymap_text_encode(bindings+at,n,notation,sizeof(notation)):-1;
 if(length<0 || length>10){notice("Definition exceeds this field or uses raw notation. Original bytes retained.");return;}
 if(keymap_field_begin(&field,notation,(unsigned)length,(shape>>8)&31,shape&31))return;
 for(;;){
  footer("");row_text(24,0,keymap_screen_label(slot),113);row_text(24,43,"Current value:",113);row_text(24,58,(const char *)notation,113);
  for(i=0;i<10;++i)frame[(pos>>8)*80+(pos&255)+i]=0x1f00+field.field[i];
  paint();cursor(pos+field.cursor,keymap_field_shape(&field));key=menu_key(raw_key());
  if(key==0x2c00){notice("PCPLUS keyboard mapping - LoC Special Edition. Press a key.");continue;}
  status=keymap_field_key(&field,field_key(key));
  if(status==KEYMAP_FIELD_CANCEL)break;
  if(status==KEYMAP_FIELD_ACCEPT){
   length=keymap_field_commit(&field,replacement,sizeof(replacement));
   if(length<0){notice("Invalid key notation; original definition retained. Press a key.");break;}
   if(memcmp(bindings+at,replacement,length+1)){memcpy(bindings+at,replacement,length+1);dirty=1;}
   break;
  }
  if(status==KEYMAP_FIELD_BELL){putchar('\a');fflush(stdout);}
 }
}
int main(int argc,char **argv)
{
 union REGS a,b;directory_replace_result r;unsigned i,key,action,e;unsigned long value;char *end;
 if(argc<3 || argc>4){puts("Usage: PCKEYMAP profile keyboard.kbd [/LEGACY]");return 2;}
 value=strtoul(argv[1],&end,10);if(!argv[1][0] || *end || value>=33)return 2;profile=(unsigned)value;
 if(argc==4){if(strcmp(argv[3],"/LEGACY"))return 2;legacy=1;}
 if(!canonical(argv[2],target)){puts("Invalid keyboard path.");return 2;}
 memset(&r,0,sizeof(r));e=kbd_editor_file_load(target,bindings,&r);
 if(e){printf("Keyboard file could not load (status %u, DOS %u).\n",e,r.dos_error);return r.close_error?14:3;}
 baseline=_fmalloc(KBD_EDITOR_BYTES);if(!baseline){puts("Insufficient memory.");return 8;}
 _fmemcpy(baseline,bindings,KBD_EDITOR_BYTES);set_leaf();
 a.h.ah=15;int86(0x10,&a,&b);page=b.h.bh;
 if(b.h.al!=3 || b.h.ah!=80 || *(unsigned char __far *)MK_FP(0x40,0x84)!=24 || page){puts("Requires80x25 color text page0.");_ffree(baseline);return 2;}
 video=MK_FP(0xb800,0);a.h.ah=3;a.h.bh=0;int86(0x10,&a,&b);shape=b.x.cx;old_cursor=b.x.dx;
 for(i=0;i<2000;++i){saved[i]=video[i];}
 for(;;){
  redraw();key=menu_key(raw_key());action=keymap_screen_key(key);
  if(action<79)edit(action);
  else if(action==KEYMAP_NEXT)profile=profile==32?0:profile+1;
  else if(action==KEYMAP_PREVIOUS)profile=profile?profile-1:32;
  else if(action==KEYMAP_SAVE){save();}
  else if(action==KEYMAP_OPEN)open_file();
  else if(action==KEYMAP_ABOUT)notice("PCPLUS keyboard mapping - LoC Special Edition. Press a key.");
  else if(action==KEYMAP_EXIT){if(leave_dirty())break;}
  else if(action==KEYMAP_RESERVED)notice("ALT-1 through ALT-0 are defined with ALT-M. Press a key.");
  else notice("Invalid key pressed. Press a key.");
  if(held)break;
 }
 for(i=0;i<2000;++i)video[i]=saved[i];cursor(old_cursor,shape);_ffree(baseline);return held?14:0;
}
