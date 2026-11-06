/* Source-only parent for passive VGA capture at actual BIOS keyboard reads. */
#include <dos.h>
#include <process.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern unsigned __cdecl help_probe_invoke(void);
extern unsigned help_probe_topic,help_probe_ui0,help_probe_ui1,help_probe_ui2,help_probe_ui3,help_probe_ui4,help_probe_ui5;
extern void __cdecl help_screen_begin(unsigned,const unsigned *);
extern void __cdecl help_screen_end(void);
extern unsigned __cdecl help_screen_count(void);
extern void __cdecl help_screen_metadata(unsigned,unsigned *,unsigned *);
static char screen[8000];
static unsigned keys[64];
char *__cdecl help_probe_resolve(const char *key)
{return strcmp(key,"PCPLUS.HLP")?"PCHELP.RTE":"HELP.HLP";}
int __cdecl help_probe_format(char *out,const char *format,unsigned long pointer)
{return sprintf(out,format,pointer);}
unsigned __cdecl help_probe_execute(const char *exe,const char *tail,unsigned a,unsigned b,unsigned c)
{
 (void)a;(void)b;(void)c;
 return (unsigned)spawnl(P_WAIT,exe,exe,"PCHELP",tail+8,(char *)0);
}
int main(int argc,char **argv)
{
 unsigned segment,rows,i,j,status,count,position,shape,restored=1;FILE *f;union REGS r;char name[13];
 if(argc!=3)return 2;rows=(unsigned)atoi(argv[1]);help_probe_topic=(unsigned)atoi(argv[2]);
 if(rows!=25&&rows!=50)return 2;
 for(i=0;i<64;++i)keys[i]=27;
 f=fopen("KEYS.BIN","rb");if(!f)return 3;i=(unsigned)fread(keys,2,64,f);if(ferror(f)||fclose(f)||!i)return 3;
 if(_dos_allocmem(32*500,&segment))return 4;
 for(i=0;i<32;++i){unsigned char __far *p=MK_FP(segment+i*500,0);for(j=0;j<8000;++j)p[j]=0xa5;}
 r.x.ax=3;int86(0x10,&r,&r);
 if(rows==50){r.x.ax=0x1112;r.x.bx=0;int86(0x10,&r,&r);}
 for(i=0;i<rows*80;++i)((unsigned __far *)MK_FP(0xb800,0))[i]=0x172e;
 r.h.ah=1;r.x.cx=0x0607;int86(0x10,&r,&r);r.h.ah=2;r.x.bx=0;r.x.dx=0x070b;int86(0x10,&r,&r);
 help_probe_ui0=0;help_probe_ui1=7;help_probe_ui2=15;help_probe_ui3=0x70;help_probe_ui4=8;help_probe_ui5=16;
 help_screen_begin(segment,keys);status=help_probe_invoke();help_screen_end();count=help_screen_count();
 for(i=0;i<rows*80;++i)if(((unsigned __far *)MK_FP(0xb800,0))[i]!=0x172e)restored=0;
 if(*(unsigned __far *)MK_FP(0x40,0x50)!=0x070b||*(unsigned __far *)MK_FP(0x40,0x60)!=0x0607)restored=0;
 f=fopen("META.BIN","wb");if(!f){_dos_freemem(segment);return 5;}
 for(i=0;i<count;++i){help_screen_metadata(i,&position,&shape);
  if(fwrite(&position,2,1,f)!=1||fwrite(&shape,2,1,f)!=1){fclose(f);_dos_freemem(segment);return 5;}}
 if(fclose(f)){_dos_freemem(segment);return 5;}
 for(i=0;i<count;++i){
  unsigned char __far *p=MK_FP(segment+i*500,0);
  for(j=0;j<8000;++j)screen[j]=p[j];
  sprintf(name,"VIEW%02u.BIN",i);f=fopen(name,"wb");if(!f){_dos_freemem(segment);return 5;}
  if(fwrite(screen,1,8000,f)!=8000||fclose(f)){_dos_freemem(segment);return 5;}
 }
 if(_dos_freemem(segment))return 6;
 printf("HELPSCREEN status=%u captures=%u rows=%u restored=%u\n",status,count,rows,restored);
 return status==0xffff?1:0;
}
