/* Actual linked owner with explicit DOS-kernel-only fault boundaries. No PRN. */
#include "printer_device.h"
#include "printer_fs.h"
#include <stdio.h>
#include <string.h>
static unsigned cases,failures,owned,opens,get_calls,sets,readies,writes,closes;
static unsigned fault,mode=0xa081,ready_value=255,lastmode,actual=1,lastbyte;
static char events[128];static unsigned nevent;
static void event(char c){events[nevent++]=c;events[nevent]=0;}
static void check(int yes,const char *s){++cases;printf("%s %s\n",yes?"PASS":"FAIL",s);if(!yes)++failures;}
unsigned printer_fs_open(int *h){++opens;event('O');if(fault==1)return 5;owned=1;*h=7;return 0;}
unsigned printer_fs_get_mode(int h,unsigned *m){++get_calls;event('G');if(h!=7 || !owned)return 6;if(fault==2)return 1;*m=mode;return 0;}
unsigned printer_fs_set_mode(int h,unsigned m){++sets;event('S');lastmode=m&255;if(h!=7 || !owned)return 6;if(fault==3 || fault==7)return 1;return 0;}
unsigned printer_fs_ready(int h,unsigned *r){++readies;event('R');if(h!=7 || !owned)return 6;if(fault==4)return 5;*r=ready_value;return 0;}
unsigned printer_fs_write(int h,const void *p,unsigned *n){++writes;event('W');if(h!=7 || !owned)return 6;lastbyte=*(const unsigned char*)p;*n=actual;return fault==5?112:0;}
unsigned printer_fs_close(int h){++closes;event('C');if(h!=7 || !owned)return 6;if(fault==6 || fault==7)return 6;owned=0;return 0;}
static void reset(unsigned f)
{check(!owned && !printer_device_result.handle_uncertain,"fixture never discards unresolved owner");fault=f;mode=0xa081;ready_value=255;actual=1;nevent=0;events[0]=0;}
int main(int argc,char **argv)
{
 unsigned before,i;printer_device_snapshot saved;
 memset(&printer_device_result,0xa5,sizeof(printer_device_result));saved=printer_device_result;
 check(printer_device_begin()==PD_STATE && printer_device_ready()==PD_STATE && printer_device_write(0)==PD_STATE && printer_device_cleanup()==PD_STATE && !memcmp(&saved,&printer_device_result,32) && !opens,"before-init rejection leaves dirty BSS and kernel unchanged");
 check(printer_device_initialize()==0 && sizeof(printer_device_result)==32 && !printer_device_result.first_status,"DATA cookie initializes exact32B ABI");
 if(argc>1){
  reset(0);check(printer_device_begin()==0,"uncertain fixture admitted");fault=argv[1][0]=='B'?7:6;
  check(printer_device_close()==(fault==7?PD_RESTORE:PD_CLOSE) && printer_device_result.handle_uncertain && printer_device_result.close_calls==1,"ambiguous close retains physical ownership and first status");
  before=closes;saved=printer_device_result;check(printer_device_initialize()==PD_RECOVERY && printer_device_begin()==PD_RECOVERY && printer_device_write(1)==PD_RECOVERY && printer_device_cleanup()==PD_RECOVERY && !memcmp(&saved,&printer_device_result,32) && closes==before,"ambiguous cannot reset reopen restore write or close again");
  check(fault!=7 || (printer_device_result.restore_error==1 && printer_device_result.close_error==6 && printer_device_result.first_status==PD_RESTORE),"restore and close errors remain independently visible");
 }else{
  reset(1);check(printer_device_begin()==PD_OPEN && !printer_device_result.handle_open && !get_calls && !closes,"failed open acquires nothing");
  check(printer_device_cleanup()==PD_OPEN && !closes,"denied open cleanup makes no close");
  reset(2);before=closes;check(printer_device_begin()==PD_IDENTITY && !printer_device_result.handle_open && closes==before+1 && !sets,"failed identity closes acquired handle without mode mutation");
  reset(0);mode=0;before=sets;check(printer_device_begin()==PD_IDENTITY && !owned && sets==before,"regular-file identity never written or set raw");
  reset(0);mode=0x91;check(printer_device_begin()==PD_IDENTITY && !owned,"reserved device mode bit fails closed");
  reset(3);before=sets;check(printer_device_begin()==PD_MODE && !owned && sets==before+2 && printer_device_result.restore_error==1 && printer_device_result.first_status==PD_MODE,"failed raw set attempts original restoration once then closes");
  reset(0);check(printer_device_begin()==0 && lastmode==0xa1 && !strcmp(events,"OGS"),"raw setup preserves low driver flags with DH0 contract");
  saved=printer_device_result;before=opens;check(printer_device_initialize()==PD_BUSY && printer_device_begin()==PD_BUSY && !memcmp(&saved,&printer_device_result,32) && opens==before,"active initialize and rebegin cannot orphan handle");
  ready_value=0;before=writes;check(printer_device_ready()==PD_WAIT && printer_device_write(65)==PD_WAIT && writes==before && !printer_device_result.first_status,"busy device does not write or poison owner");
  ready_value=255;before=readies;for(i=0;i<256;++i)if(printer_device_write(i)!=0 || lastbyte!=i)break;
  check(i==256 && printer_device_result.accepted==256 && readies==before+256,"all256 binary bytes written exactly once after fresh readiness");
  saved=printer_device_result;before=readies;check(printer_device_write(256)==PD_ARGUMENT && !memcmp(&saved,&printer_device_result,32) && readies==before,"invalid word cannot become another byte");
  check(printer_device_close()==0 && lastmode==0x81 && !owned && !strcmp(events+nevent-2,"SC"),"restore original mode precedes physical close");before=closes;
  check(printer_device_close()==0 && printer_device_cleanup()==0 && closes==before,"resolved repeated cleanup never closes reused handle");
  reset(0);mode=0xa1;before=sets;check(printer_device_begin()==0 && printer_device_close()==0 && sets==before,"already raw mode needs no mutation or restore");
  reset(0);check(printer_device_begin()==0,"prepare readiness error");fault=4;before=writes;check(printer_device_write(1)==PD_READY && printer_device_result.dos_error==5 && printer_device_write(1)==PD_READY && writes==before,"readiness error poisons without write");fault=0;check(printer_device_close()==PD_READY,"readiness first failure survives close");
  reset(0);check(printer_device_begin()==0,"prepare malformed readiness");ready_value=1;check(printer_device_ready()==PD_READY && printer_device_result.dos_error==13,"nonstandard status fails closed");check(printer_device_close()==PD_READY,"malformed readiness owner closes");
  reset(0);check(printer_device_begin()==0,"prepare positive short singlebyte failure");actual=0;before=writes;check(printer_device_write(0x1a)==PD_WRITE && !printer_device_result.accepted && printer_device_write(1)==PD_WRITE && writes==before+1,"short singlebyte write never retried");check(printer_device_close()==PD_WRITE,"short failure retained after close");
  reset(0);check(printer_device_begin()==0,"prepare error with accepted byte");fault=5;check(printer_device_write(0xff)==PD_WRITE && printer_device_result.accepted==1 && printer_device_result.dos_error==112,"error accounting retains actual accepted byte");fault=0;check(printer_device_close()==PD_WRITE,"write DOS error survives checked close");
  reset(0);check(printer_device_begin()==0,"prepare counter overflow");printer_device_result.accepted=0xffffffffUL;before=writes;check(printer_device_write(1)==PD_OVERFLOW && writes==before,"DWORD accepted overflow prevents IO");check(printer_device_close()==PD_OVERFLOW,"overflow failure stays first");
 }
 printf("CASES %u\n",cases);return failures?1:0;
}
