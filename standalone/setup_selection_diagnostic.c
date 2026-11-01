/* Production frozen setup owner and DOS readers; no synthetic file replies. */
#include "../src/config/live_setup_owner.h"
#include "../src/capture/capture_file.h"
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
unsigned char directory_pending;
unsigned directory_pending_count;
#pragma aux directory_pending "directory_pending";
#pragma aux directory_pending_count "directory_pending_count";
transfer_import_settings terminal_transfer_preferences;
static prm_dos_image accepted,original;
static directory_live_context old_context,next_context,expected,saved_context;
static live_configuration_plan old_plan,next_plan,destination;
static terminal_import_settings source;
static unsigned checks,opens,reads,closes,canonical_calls;
static char request[64]="TEST.PRM",dir_path[64]="C:\\TEST.DIR",tail[68];
static unsigned char target[64]="Board:23";
static live_setup_result result;
static transfer_import_settings transfer;
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL %u\r\n",__LINE__);return 1;}} while(0)
unsigned selection_real_canonical(const char *,char *);
unsigned capture_fs_canonical(const char *p,char *out)
{++canonical_calls;return selection_real_canonical(p,out);}
unsigned selection_open(const char *p,unsigned flags,int *h)
{++opens;return _dos_open(p,flags,h);}
unsigned selection_read(int h,void __far *p,unsigned n,unsigned *got)
{++reads;return _dos_read(h,p,n,got);}
unsigned selection_close(int h)
{++closes;return _dos_close(h);}
static unsigned io_count(void){return opens+reads+closes+canonical_calls;}
static unsigned begin(const directory_live_context *context,const live_configuration_plan *plan)
{return live_setup_begin(request,context,plan,context?80:16,target);}
static unsigned invoke(const directory_live_context *before,const directory_live_context *after,const prm_dos_image *image,unsigned action)
{unsigned count=io_count(),status=live_setup_select(before,after,image,action);return count==io_count()?status:65535U;}
int main(int argc,char **argv)
{
 unsigned mode,i,status,report[6];prm_dos_result io;directory_live_result decoded;live_configuration_result classified;FILE *f;
 if(argc!=2)return 2;mode=(unsigned)atoi(argv[1]);if(mode>10)return 2;
 memset(&old_plan,0,sizeof(old_plan));memset(&next_plan,0,sizeof(next_plan));
 CHECK(!prm_dos_load(request,&accepted,&io));memcpy(&original,&accepted,sizeof(original));
 CHECK(!directory_live_read_context(request,dir_path,1,0,&old_plan.serial,&old_plan.modem,&old_plan.directory,&decoded,&old_context));
 CHECK(!directory_live_read_context(request,dir_path,2,0,&next_plan.serial,&next_plan.modem,&next_plan.directory,&decoded,&next_context));
 if(mode==0)CHECK(invoke(0,&next_context,&accepted,1)==LIVE_SETUP_UNBOUND);
 memcpy(&source,&old_plan.serial,sizeof(source));source.clipboard_separator=17;
 CHECK(!live_setup_bind(request,mode==0?0:&old_context,&source));
 memcpy(&expected,&old_context,sizeof(expected));memcpy(&saved_context,&next_context,sizeof(saved_context));
 if(mode==0){
  CHECK(invoke(&expected,&next_context,&accepted,1)==LIVE_SETUP_IDENTITY);
  CHECK(!invoke(0,&next_context,&accepted,0));CHECK(!begin(0,&old_plan));CHECK(!live_setup_abort(0));
  CHECK(!invoke(0,&next_context,&accepted,1));
 }else if(mode==1){
  CHECK(!invoke(&expected,&next_context,&accepted,0));CHECK(!begin(&old_context,&old_plan));CHECK(!live_setup_abort(0));
  CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else if(mode==2){
  expected.selection.record[61]^=1;CHECK(invoke(&expected,&next_context,&accepted,1)==LIVE_SETUP_IDENTITY);
  CHECK(!begin(&old_context,&old_plan));CHECK(!live_setup_abort(0));
  expected.selection.record[61]^=1;CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else if(mode==3){
  expected.selection.record[61]='1';expected.selection.record[70]=42;
  CHECK(!live_setup_reconcile_accounting(&expected,1));
  CHECK(invoke(&old_context,&next_context,&accepted,1)==LIVE_SETUP_IDENTITY);
  CHECK(!begin(&expected,&old_plan));CHECK(!live_setup_abort(0));CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else if(mode==4){
  directory_pending=1;CHECK(invoke(&expected,&next_context,&accepted,1)==LIVE_SETUP_STATE);
  directory_pending=0;directory_pending_count=1;CHECK(invoke(&expected,&next_context,&accepted,1)==LIVE_SETUP_STATE);
  directory_pending=1;CHECK(invoke(&expected,&next_context,&accepted,0)==LIVE_SETUP_STATE);
  CHECK(!begin(&old_context,&old_plan));CHECK(!live_setup_abort(0));
  directory_pending=0;directory_pending_count=0;CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else if(mode==5){
  CHECK(!begin(&old_context,&old_plan));CHECK(invoke(&expected,&next_context,&accepted,1)==LIVE_SETUP_STATE);
  CHECK(!live_setup_finish(&destination,&result));CHECK(destination.directory.entry_number==1);
  CHECK(!live_setup_abort(0));CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else if(mode==6){
  CHECK(!begin(&old_context,&old_plan));CHECK(!live_setup_finish(&destination,&result));
  CHECK(invoke(&expected,&next_context,&accepted,1)==LIVE_SETUP_STATE);
  CHECK(!live_setup_transfer_settings(&transfer));CHECK(!live_setup_acknowledge(0));CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else if(mode==7){
  CHECK(invoke(&expected,&next_context,&accepted,2)==LIVE_SETUP_ARGUMENT);
  CHECK(invoke(&expected,0,&accepted,1)==LIVE_SETUP_ARGUMENT);
  CHECK(invoke(&expected,&next_context,0,1)==LIVE_SETUP_ARGUMENT);
  CHECK(invoke(&expected,&expected,&accepted,1)==LIVE_SETUP_ARGUMENT);
  CHECK(invoke((directory_live_context *)&accepted,&next_context,&accepted,1)==LIVE_SETUP_ARGUMENT);
  CHECK(invoke(&expected,(directory_live_context *)&accepted,&accepted,1)==LIVE_SETUP_ARGUMENT);
  CHECK(invoke((directory_live_context *)0xff80,&next_context,&accepted,1)==LIVE_SETUP_ARGUMENT);
  CHECK(invoke(&expected,(directory_live_context *)0xff80,&accepted,1)==LIVE_SETUP_ARGUMENT);
  CHECK(invoke(&expected,&next_context,(prm_dos_image *)0xff80,1)==LIVE_SETUP_ARGUMENT);
  CHECK(!begin(&old_context,&old_plan));CHECK(!live_setup_abort(0));CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else if(mode==8){
  for(i=0;i<8;++i){
   memcpy(&next_context,&saved_context,sizeof(next_context));
   if(i==0)next_context.prm_path[0]='X';
   if(i==1)strcpy(next_context.directory_path,"TEST.DIR");
   if(i==2)strcpy(next_context.directory_path,"c:\\TEST.DIR");
   if(i==3)strcpy(next_context.directory_path,"C:/TEST.DIR");
   if(i==4)memset(next_context.directory_path,'X',64);
   if(i==5)next_context.selection.entry_number=0;
   if(i==6)next_context.selection.entry_number=201;
   if(i==7)next_context.codes=2;
   CHECK(invoke(&expected,&next_context,&accepted,1)==LIVE_SETUP_IDENTITY);
   CHECK(!begin(&old_context,&old_plan));CHECK(!live_setup_abort(0));
  }
  memcpy(&next_context,&saved_context,sizeof(next_context));CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else if(mode==9){
  for(i=0;i<4;++i){
   if(i==0)accepted.bytes[0]=99;
   if(i==1)accepted.bytes[0x198]=2;
   if(i==2)accepted.bytes[0x31c]='?';
   if(i==3)next_context.selection.record[0x49]=99;
   CHECK(invoke(&expected,&next_context,&accepted,1)==LIVE_SETUP_DECODE);
   CHECK(!begin(&old_context,&old_plan));CHECK(!live_setup_abort(0));
   memcpy(&accepted,&original,sizeof(accepted));memcpy(&next_context,&saved_context,sizeof(next_context));
  }
  CHECK(!invoke(&expected,&next_context,&accepted,1));
 }else{
  strcpy(next_context.directory_path,"C:\\ABCDEFGH\\IJKLMNOP\\QRSTUVWX\\YZABCDEF\\GHIJKLMN\\ABCDEFG\\NEW.DIR");
  CHECK(strlen(next_context.directory_path)==63);CHECK(!invoke(&expected,&next_context,&accepted,1));
 }
 CHECK(!live_setup_frozen_command(tail));CHECK(!strcmp(tail," C:\\TEST.PRM"));
 CHECK(begin(&old_context,&old_plan)==LIVE_SETUP_IDENTITY);
 CHECK(!live_configuration_decode(&accepted,&next_context.selection,next_context.codes,0,0,&next_plan,&classified));
 /* Negotiated speed/session R differ from the newly selected saved baseline. */
 next_plan.serial.baud_low=38400;next_plan.serial.baud_high=0;next_plan.serial.clipboard_separator=94;
 CHECK(!begin(&next_context,&next_plan));CHECK(!live_setup_finish_policy(&destination,&result,31|2048));
 CHECK(!(result.applied_mask&LIVE_CHANGE_BAUD));CHECK(destination.serial.baud_low==38400 && !destination.serial.baud_high);
 CHECK(!(result.applied_mask&LIVE_CHANGE_CLIPBOARD));CHECK(destination.serial.clipboard_separator==94);
 CHECK(destination.directory.entry_number==2);CHECK(!live_setup_acknowledge(0));
 CHECK(!memcmp(&accepted,&original,sizeof(accepted)));CHECK(!memcmp(&expected,&old_context,sizeof(expected)) || mode==3);
 CHECK(opens==closes);status=io_count();CHECK(status>0);
 report[0]=mode;report[1]=checks;report[2]=opens;report[3]=reads;report[4]=closes;report[5]=canonical_calls;
 f=fopen("C:\\REPORT.BIN","wb");CHECK(f!=0);CHECK(fwrite(report,2,6,f)==6);CHECK(!fclose(f));puts("PASS");return 0;
}
