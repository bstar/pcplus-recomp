#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include <i86.h>
#include <direct.h>
#include "meta_picker_scan.h"
#include "meta_scan_faults.h"
extern meta_picker_scan __far scan;
extern meta_picker_state __far picker;
extern unsigned char __far entries[META_PICKER_BYTES];
static unsigned long checks;
static unsigned char dta1[128],dta2[128],snapshot[160];
static char pattern[64]="C:\\LAB\\*.KEY",cwd[64],cdir[64],now[64],selected[9];
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %u check %lu phase %u status %u dos %u count %u calls %u\r\n",__LINE__,checks,scan.phase,scan.status,scan.dos_error,picker.count,scan_calls);exit(1);}}while(0)
static unsigned ds(void);
#pragma aux ds = "mov ax,ds" value [ax] modify [];
static unsigned ss(void);
#pragma aux ss = "mov ax,ss" value [ax] modify [];
static void __far *get_dta(void)
{union REGS in,out;struct SREGS seg;segread(&seg);in.h.ah=0x2f;intdosx(&in,&out,&seg);return MK_FP(seg.es,out.x.bx);}
static void set_dta(void __far *p)
{union REGS in,out;struct SREGS seg;segread(&seg);seg.ds=FP_SEG(p);in.x.dx=FP_OFF(p);in.h.ah=0x1a;intdosx(&in,&out,&seg);}
static unsigned walk(const char *p,unsigned fault,unsigned interleave)
{
 void __far *saved_dta=get_dta();struct find_t other;unsigned step=0,status=0,previous,calls,i,other_count=0;unsigned char *guard;
 CHECK(!meta_picker_begin(&picker,entries));scan_reset(fault);CHECK(!meta_picker_scan_begin(&scan,&picker,p));CHECK(!scan_calls);
 if(interleave){CHECK(!_dos_findfirst("C:\\OTHER\\*.TXT",0,&other));other_count=1;}
 while(scan.phase==META_SCAN_READ || scan.phase==META_SCAN_SORT){
  CHECK(++step<20000);guard=step&1?dta1:dta2;memset(guard,0xa5,128);set_dta(guard);previous=scan.phase;calls=scan_calls;
  status=meta_picker_scan_step(&scan);CHECK(get_dta()==(void __far *)guard);for(i=0;i<128;++i)CHECK(guard[i]==0xa5);
  CHECK(scan_calls-calls<=(previous==META_SCAN_READ?1:0));
  if(interleave && other_count<3){CHECK(!_dos_findnext(&other));++other_count;}
  else if(interleave && other_count==3){CHECK(_dos_findnext(&other)==18);++other_count;}
  if(status)break;
 }
 CHECK(getcwd(now,64)!=0 && !strcmp(now,cwd));CHECK(_getdcwd(3,now,64)!=0 && !strcmp(now,cdir));
 if(interleave)CHECK(other_count==4);set_dta(saved_dta);return status;
}
int main(void)
{
 unsigned mode,status,i,calls,last=0,value;void __far *original=get_dta();char bad[64];
 CHECK(ds()==ss() && FP_SEG(&scan)!=ds() && FP_SEG(entries)!=ds() && sizeof(scan)<=160);
 CHECK(getcwd(cwd,64)!=0 && !strcmp(cwd,"D:\\KEEP"));CHECK(_getdcwd(3,cdir,64)!=0 && !strcmp(cdir,"C:\\ALT"));
 CHECK(!_dos_setfileattr("C:\\LAB\\READONLY.KEY",_A_RDONLY));
 CHECK(!walk(pattern,0,1));CHECK(scan.phase==META_SCAN_DONE && !scan.limit_reached && picker.count==3 && picker.phase==META_PICKER_ACTIVE);
 CHECK(!_fstrcmp((const char __far *)entries,"A") && !_fstrcmp((const char __far *)entries+9,"READONLY") && !_fstrcmp((const char __far *)entries+18,"Z"));
 CHECK(!meta_picker_key(&picker,13));CHECK(!meta_picker_selected(&picker,selected) && !strcmp(selected,"A"));calls=scan_calls;CHECK(meta_picker_scan_step(&scan)==META_SCAN_STATE && scan_calls==calls);
 strcpy(bad,"c:/lab/*.key");CHECK(!walk(bad,0,0));CHECK(!_fstrcmp(scan.pattern,"C:\\LAB\\*.KEY"));
 CHECK(!walk("C:\\EMPTY\\*.KEY",0,0));CHECK(scan.phase==META_SCAN_DONE && picker.phase==META_PICKER_EMPTY && !picker.count);
 CHECK(walk("C:\\MISSING\\*.KEY",0,0)==META_SCAN_DOS && scan.phase==META_SCAN_FAILED && scan.dos_error==3 && picker.phase==META_PICKER_COLLECT);
 for(mode=1;mode<=6;++mode){
  status=walk(pattern,mode,0);
  if(mode==5)CHECK(!status && picker.count==2 && scan.phase==META_SCAN_DONE);
  else{CHECK(status==(mode<3?META_SCAN_DOS:META_SCAN_NAME) && scan.phase==META_SCAN_FAILED && picker.phase==META_PICKER_COLLECT);CHECK(meta_picker_key(&picker,13)==META_PICKER_BUSY);calls=scan_calls;CHECK(meta_picker_scan_step(&scan)==META_SCAN_STATE && scan_calls==calls);}
 }
 CHECK(!walk("C:\\MANY\\*.KEY",0,0));CHECK(scan.limit_reached==1 && picker.count==1001 && scan_calls==1001 && scan_nexts==1000);
 for(i=0;i<1001;++i){_fmemcpy(selected,entries+i*9,9);value=atoi(selected+1);CHECK(selected[0]=='K' && strlen(selected)==5 && value<=1001 && (!i || value>last));last=value;}
 /* Cancellation does no DOS operation; no half-list becomes active. */
 CHECK(!meta_picker_begin(&picker,entries));scan_reset(0);CHECK(!meta_picker_scan_begin(&scan,&picker,pattern));CHECK(!meta_picker_scan_step(&scan));calls=scan_calls;CHECK(!meta_picker_scan_cancel(&scan));CHECK(scan.phase==META_SCAN_CANCELED && picker.phase==META_PICKER_COLLECT && scan_calls==calls);CHECK(meta_picker_scan_step(&scan)==META_SCAN_STATE && scan_calls==calls);
 CHECK(!meta_picker_begin(&picker,entries));scan_reset(0);CHECK(!meta_picker_scan_begin(&scan,&picker,pattern));
 while(scan.phase==META_SCAN_READ)CHECK(!meta_picker_scan_step(&scan));
 CHECK(scan.phase==META_SCAN_SORT);calls=scan_calls;CHECK(!meta_picker_scan_cancel(&scan));CHECK(scan.phase==META_SCAN_CANCELED && picker.phase==META_PICKER_SORT && scan_calls==calls);CHECK(meta_picker_scan_step(&scan)==META_SCAN_STATE && scan_calls==calls);
 for(mode=0;mode<8;++mode){
  CHECK(!meta_picker_begin(&picker,entries));scan_reset(0);_fmemset(&scan,0xa5,sizeof(scan));_fmemcpy(snapshot,&scan,sizeof(scan));
  strcpy(bad,mode==0?"*.KEY":mode==1?"C:*.KEY":mode==2?"C:\\LAB\\A*.KEY":mode==3?"C:\\LAB\\*.TXT":mode==4?"C:\\LAB\\..\\*.KEY":mode==5?"C:\\CON\\*.KEY":mode==6?"C:\\TOOLONGGG\\*.KEY":"C:\\LAB\\?\\*.KEY");
  CHECK(meta_picker_scan_begin(&scan,&picker,bad)==META_SCAN_ARGUMENT && !scan_calls && !_fmemcmp(snapshot,&scan,sizeof(scan)));
 }
 CHECK(!meta_picker_begin(&picker,entries));scan_reset(0);CHECK(meta_picker_scan_begin((meta_picker_scan __far *)MK_FP(ds(),0xfff0),&picker,pattern)==META_SCAN_ARGUMENT && !scan_calls);
 CHECK(meta_picker_scan_begin(&scan,&picker,(const char *)0xfff0)==META_SCAN_ARGUMENT && !scan_calls);
 CHECK(!meta_picker_scan_begin(&scan,&picker,pattern));picker.count=1;CHECK(meta_picker_scan_step(&scan)==META_SCAN_ARGUMENT && !scan_calls);
 CHECK(!_dos_setfileattr("C:\\LAB\\READONLY.KEY",0));set_dta(original);
 printf("PASS %lu checks; scan state %u bytes; actual DOS enumeration/DTA/CWD/interleaving;6 faults;1001 limit\r\n",checks,sizeof(scan));return 0;
}
