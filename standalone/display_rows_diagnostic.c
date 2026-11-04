#include "native_display_rows.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static unsigned checks,failures;
extern void __cdecl display_rows_observer_start(void),display_rows_observer_stop(void);
extern void __cdecl display_rows_observer_arm(void);
extern unsigned __cdecl display_rows_observer_count(void),display_rows_observer_pending(void);
extern unsigned __cdecl display_rows_observer_dropped(void);
extern void __cdecl display_rows_observer_refuse_modes(void);
extern unsigned __cdecl display_rows_observer_modes_pending(void),display_rows_observer_modes_dropped(void);
static void check(unsigned ok,unsigned line){++checks;if(!ok){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static unsigned current_rows(void)
{
 unsigned char __far *p=MK_FP(0x40,0x84);return *p>=24?*p+1:25;
}
static void geometry(native_display_rows_info *p)
{
 union REGS in,out;
 in.h.ah=15;int86(0x10,&in,&out);
 CHECK(p->mode==out.h.al && p->columns==out.h.ah && out.h.bh==0);
 CHECK(p->rows==current_rows() && p->stride==160 && p->cells==80*p->rows);
 if(p->font_capable){
  in.x.ax=0x1130;in.x.bx=0;int86(0x10,&in,&out);
  CHECK(out.h.dl+1==p->rows);
  CHECK(out.x.cx==(p->rows==28?14:p->rows==43 || p->rows==50?8:p->scanline_capable?16:14));
 }
}
int main(int argc,char **argv)
{
 native_display_rows_info p,again,old;unsigned rc,i,before,supported;
 const unsigned sequence[]={25,28,43,50,43,28,25};
 const unsigned invalid[]={0,1,24,26,42,49,51,256,0x12b,0xffff};
 unsigned __far *video;union REGS in,out;void (__interrupt __far *vector)(void);
 setvbuf(stdout,0,_IONBF,0);vector=_dos_getvect(0x10);display_rows_observer_start();
 if(argc>1 && !strcmp(argv[1],"/MONO")){in.x.ax=7;int86(0x10,&in,&out);}
 rc=native_display_rows_probe(&p);CHECK(rc==0);
 if(rc)goto done;
 if(argc>1 && !strcmp(argv[1],"/MONO"))CHECK(p.mode==7 && p.segment==0xb000);
 if(p.segment==0xb000 && p.mode!=7){in.x.ax=7;int86(0x10,&in,&out);CHECK(native_display_rows_probe(&p)==0);}
 printf("ADAPTER mode=%u font=%u scanline=%u vendor=%u rows=%u\n",p.mode,p.font_capable,p.scanline_capable,p.extended_mode,p.rows);
 CHECK(p.rows==25);geometry(&p);
 for(i=0;i<3;++i){CHECK(native_display_rows_probe(&again)==0);CHECK(!memcmp(&p,&again,sizeof(p)));}
 for(i=0;i<sizeof(sequence)/sizeof(sequence[0]);++i){
  unsigned request=sequence[i];old=p;before=display_rows_observer_count();
  video=MK_FP(p.segment,0);video[0]=0x1741;video[(p.rows-1)*80+79]=0x2e5a;
  supported=request==25 || (p.font_capable && (p.scanline_capable || request==43));
  rc=native_display_rows_set(request,&p);
  CHECK(rc==(supported?DISPLAY_ROWS_OK:DISPLAY_ROWS_UNSUPPORTED));
  CHECK(p.rows==(supported?request:old.rows) && !p.fallback);geometry(&p);
  if(!supported){CHECK(display_rows_observer_count()==before);CHECK(video[0]==0x1741 && video[(old.rows-1)*80+79]==0x2e5a);}
  printf("ROWS requested=%u rc=%u actual=%u\n",request,rc,p.rows);
 }
 for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);++i){
  old=p;before=display_rows_observer_count();
  CHECK(native_display_rows_set(invalid[i],&p)==DISPLAY_ROWS_INVALID);
  CHECK(!memcmp(&p,&old,sizeof(p)) && before==display_rows_observer_count());
 }
 CHECK(native_display_rows_set(25,0)==DISPLAY_ROWS_INVALID);
 if(p.scanline_capable){
  display_rows_observer_arm();CHECK(display_rows_observer_pending()==1);
  rc=native_display_rows_set(50,&p);
  CHECK(rc==DISPLAY_ROWS_FAILED && p.fallback==1 && p.rows==25);
  printf("FAULT pending=%u dropped=%u\n",display_rows_observer_pending(),display_rows_observer_dropped());
  CHECK(!display_rows_observer_pending() && display_rows_observer_dropped()==1);geometry(&p);
  printf("REFUSED_FONT rc=%u fallback=%u rows=%u\n",rc,p.fallback,p.rows);
  CHECK(native_display_rows_set(43,&p)==0 && p.rows==43);
  CHECK(native_display_rows_set(25,&p)==0 && p.rows==25);
  CHECK(native_display_rows_set(50,&p)==0 && p.rows==50);
  display_rows_observer_refuse_modes();
  rc=native_display_rows_set(25,&p);
  CHECK(rc==DISPLAY_ROWS_UNUSABLE && p.rows==50 && !p.fallback);
  CHECK(!display_rows_observer_modes_pending() && display_rows_observer_modes_dropped()==2);
  printf("REFUSED_BASELINE rc=%u fallback=%u rows=%u\n",rc,p.fallback,p.rows);
  geometry(&p);
  CHECK(native_display_rows_set(25,&p)==0 && p.rows==25 && !p.fallback);
 }
 /* Nonzero pages and graphics are rejected before changing the display. */
 in.x.ax=0x0501;int86(0x10,&in,&out);before=display_rows_observer_count();
 in.h.ah=15;int86(0x10,&in,&out);
 if(out.h.bh){
  CHECK(native_display_rows_set(43,&p)==DISPLAY_ROWS_UNSUPPORTED);
  CHECK(display_rows_observer_count()==before);
 }else printf("PAGE1 unavailable\n");
 in.x.ax=0x0500;int86(0x10,&in,&out);
 /* Mode6 exists on all tested colour adapters; Hercules uses mode7 only. */
 if(p.mode!=7){
  in.x.ax=6;int86(0x10,&in,&out);before=display_rows_observer_count();
  CHECK(native_display_rows_set(25,&p)==DISPLAY_ROWS_UNSUPPORTED);
  CHECK(display_rows_observer_count()==before);
  in.x.ax=3;int86(0x10,&in,&out);
 }
done:
 display_rows_observer_stop();CHECK(_dos_getvect(0x10)==vector);
 printf("DISPLAY_ROWS %u checks %u failures\n",checks,failures);
 return failures?1:0;
}
