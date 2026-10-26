#include "../src/directory/directory_resources.h"
#include "../src/capture/capture_file.h"
#include "../src/capture/capture_fs.h"
#include "../src/capture/capture_reservation.h"
#include <dos.h>
#include <direct.h>
#include <fcntl.h>
#include <malloc.h>
#include <process.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned mode,checks,opens,closes,canonical_calls,attribute_calls,testing,failed_witness;
static unsigned char defaults[948],before_defaults[948];
static directory_resource_request request,before_request;
static directory_resource_snapshot saved;
static directory_resource_bundle __far *output;
static directory_resource_bundle prior_bundle;
static int retained_handle;
static unsigned char __far *memory;
static char cwd[64];
unsigned resource_real_canonical(const char *,char *);
unsigned resource_real_attributes(const char *,unsigned *);
#define CHECK(c) do{++checks;if(!(c)){printf("FAIL mode %u line %u status %u state %u opens %u closes %u\n",mode,__LINE__,directory_resource_result.status,directory_resource_result.state,opens,closes);return 1;}}while(0)
unsigned capture_fs_canonical(const char *path,char *absolute)
{
 unsigned status;
 if(testing){++canonical_calls;if(mode==18)return 5;}
 status=resource_real_canonical(path,absolute);
 if(testing && !status && mode==28){memset(absolute,'A',64);absolute[64]=0;}
 return status;
}
unsigned capture_fs_attributes(const char *path,unsigned *attributes)
{if(testing){++attribute_calls;if(mode==19)return 5;if(mode==29){*attributes=0x10;return 0;}}return resource_real_attributes(path,attributes);}
unsigned resource_test_open(const char *path,unsigned flags,int *handle)
{
 unsigned status;
 ++opens;
 if(flags!=(O_RDONLY|O_NOINHERIT) || directory_resources_exec_allowed())failed_witness=1;
 /* Probe both claimed paths before every content open. No read may precede
  * same-process exclusion, even while only the first resource is being read. */
 if(directory_resource_result.keyboard_path[0] && !capture_file_reserved(directory_resource_result.keyboard_path))failed_witness=1;
 if(directory_resource_result.actions_path[0] && !capture_file_reserved(directory_resource_result.actions_path))failed_witness=1;
 if(mode==30 && opens==2)return 5;
 if(mode==31 && opens==1)return 5;
 status=_dos_open(path,flags,handle);if(!status)retained_handle=*handle;
 if(mode==17 && opens==1 && chdir("\\OTHER"))failed_witness=1;
 return status;
}
unsigned resource_test_close(int handle)
{
 ++closes;
 if((mode==11 || mode==12) && closes==1){if(mode==11 && _dos_close(handle))failed_witness=1;return 6;}
 return _dos_close(handle);
}
unsigned __far __cdecl resource_test_release(capture_file_probe probe,void *context)
{return mode==16?CF_BUSY:capture_file_release(probe,context);}
static unsigned __far __cdecl other_probe(const char *path,void *context)
{return path && context?0:1;}
static unsigned poison(void)
{unsigned i;for(i=0;i<sizeof(*output);++i)if(((unsigned char __far *)output)[i]!=0xcc)return 0;return 1;}
int main(int argc,char **argv)
{
 unsigned i,status,report[9],expected=0,held=0,owner=0,attributes;
 FILE *file;unsigned char chunk[512];unsigned count;
 if(argc!=2)return 2;mode=(unsigned)atoi(argv[1]);if(mode>35)return 2;
 CHECK(getcwd(cwd,sizeof(cwd))!=0);
 memory=(unsigned char __far *)_fmalloc(sizeof(*output)+32);CHECK(memory!=0);
 output=(directory_resource_bundle __far *)(memory+16);_fmemset(memory,0xcc,sizeof(*output)+32);
 memset(&request,0,sizeof(request));memset(defaults,0,sizeof(defaults));
 for(i=0;i<79;++i)defaults[i*12]=(unsigned char)('A'+i%26);
 request.profile=mode==5?6:4;request.psp=_psp;
 if(mode!=0){memcpy(request.record+0x56,"BOARD",6);memcpy(request.record+0x5f,"BOARD",6);}
 if(mode==3 || mode==4){memcpy(request.record+0x56,"MISSING",8);memcpy(request.record+0x5f,"MISSING",8);}
 if(mode==5 || mode==6 || mode==7){
  request.cli_mask=512|4096;
  strcpy(request.cli_keyboard,cwd);strcat(request.cli_keyboard,mode==6?"\\MISSING.KBD":"\\CLI.KBD");
  strcpy(request.cli_actions,cwd);strcat(request.cli_actions,"\\CLI.KEY");
 }
 if(mode==7)request.record[0x56]='*';
 if(mode==8)request.profile=5;
 if(mode==26)memset(defaults,'X',12);
 if(mode==27){request.cli_mask=512;strcpy(request.cli_keyboard,"CLI.KBD");}
 CHECK(directory_resources_exec_allowed()==1);
 memset(&directory_resource_result,0xa5,sizeof(directory_resource_result));
 CHECK(directory_resources_initialize()==0);
 CHECK(capture_file_initialize()==0 && monitor_file_initialize()==0 && snapshot_file_initialize()==0);
 memcpy(&saved,&directory_resource_result,sizeof(saved));
 CHECK(directory_resources_stage(0,defaults,output)==DR_ARGUMENT);
 CHECK(directory_resources_stage((const directory_resource_request *)0xfff0,defaults,output)==DR_ARGUMENT);
 CHECK(directory_resources_stage(&request,(const unsigned char *)0xfff0,output)==DR_ARGUMENT);
 CHECK(directory_resources_stage(&request,defaults,(directory_resource_bundle __far *)&request)==DR_ARGUMENT);
 CHECK(directory_resources_stage(&request,defaults,(directory_resource_bundle __far *)MK_FP(FP_SEG((void __far *)&request)-1,FP_OFF((void __far *)&request)+16))==DR_ARGUMENT);
 CHECK(directory_resources_stage(&request,defaults,(directory_resource_bundle __far *)MK_FP(FP_SEG((void __far *)&request),0xfff0))==DR_ARGUMENT);
 CHECK(directory_resources_stage(&request,defaults,(directory_resource_bundle __far *)MK_FP(0xffff,0x10))==DR_ARGUMENT);
 CHECK(directory_resources_stage(&request,defaults,(directory_resource_bundle __far *)defaults)==DR_ARGUMENT);
 CHECK(directory_resources_stage(&request,defaults,(directory_resource_bundle __far *)&directory_resource_result)==DR_ARGUMENT);
 CHECK(!memcmp(&saved,&directory_resource_result,sizeof(saved)) && poison());
 if(mode==13){CHECK(capture_file_begin("BOARD.KBD",CF_APPEND)==0);owner=1;}
 if(mode==14){CHECK(monitor_file_begin("BOARD.KEY",CF_APPEND)==0);owner=2;}
 if(mode==15)CHECK(capture_file_reserve(other_probe,&mode)==0);
 if(mode==20){
  CHECK(capture_fs_attributes("BOARD.KBD",&attributes)==0 && (attributes&1));
  CHECK(capture_fs_attributes("BOARD.KEY",&attributes)==0 && (attributes&1));
 }
 if(mode==32 || mode==33){
  char identity[128];CHECK(capture_fs_canonical(mode==32?"BOARD.KBD":"BOARD.KEY",identity)==0);
  CHECK(capture_file_claim(identity,&mode)==0);
 }
 if(mode==34)CHECK(snapshot_file_begin("BOARD.KBD",CF_APPEND)==0);
 if(mode==35)CHECK(history_file_event(HISTORY_BEGIN,"BOARD.KEY",0)==0);
 memcpy(&before_request,&request,sizeof(request));memcpy(before_defaults,defaults,sizeof(defaults));
 testing=1;status=directory_resources_stage(&request,defaults,output);testing=0;
 CHECK(!failed_witness && !memcmp(&request,&before_request,sizeof(request)) && !memcmp(defaults,before_defaults,948));
 if(mode==6 || mode==23)expected=DR_LOOKUP;
 if(mode==7 || mode==8 || mode==26 || mode==27)expected=DR_ARGUMENT;
 if(mode==9 || mode==11 || mode==12 || mode==21)expected=DR_KEYMAP;
 if(mode==10 || mode==22)expected=DR_ACTIONS;
 if(mode==13 || mode==14 || mode==15)expected=DR_CLAIM;
 if(mode==16)expected=DR_RELEASE;
 if(mode==18)expected=DR_CANONICAL;
 if(mode==19)expected=DR_LOOKUP;
 if(mode==28)expected=DR_PATH;
 if(mode==29)expected=DR_LOOKUP;
 if(mode==30)expected=DR_ACTIONS;
 if(mode==31)expected=DR_KEYMAP;
 if(mode>=32)expected=DR_CLAIM;
 held=mode==11 || mode==12 || mode==16;
 CHECK(status==expected);
 CHECK(directory_resources_exec_allowed()==!held);
 if(expected){CHECK(poison());}else{
  CHECK(output->profile==request.profile);
  CHECK(output->mask==((mode==0 || mode==4)?0:mode==3?512:4608));
  if(mode==0 || mode==4)CHECK(!_fmemcmp(output->keyboard,defaults,948));
 }
 for(i=0;i<16;++i)CHECK(memory[i]==0xcc && memory[16+sizeof(*output)+i]==0xcc);
 if(mode==7 || mode==8 || mode==26 || mode==27)CHECK(!canonical_calls && !attribute_calls && !opens && !closes);
 if(mode==13 || mode==14 || mode==15 || mode>=32)CHECK(!opens && !closes);
 if(held){
  memcpy(&saved,&directory_resource_result,sizeof(saved));i=closes;
  CHECK(directory_resources_initialize()==DR_RECOVERY);
  CHECK(directory_resources_stage(&request,defaults,output)==DR_RECOVERY);
  CHECK(i==closes && !memcmp(&saved,&directory_resource_result,sizeof(saved)));
  CHECK(capture_file_reserved(saved.keyboard_path));
  if(mode==12){
   char number[8],byte;unsigned got;
   CHECK(_dos_read(retained_handle,&byte,1,&got)==0 && got==1);
   sprintf(number,"%u",(unsigned)retained_handle);
   /* Deliberately bypass the product's refused EXEC predicate to witness
    * DOS containment independently. The child opens no files before probing. */
   CHECK(spawnl(P_WAIT,"\\NOINH.COM","NOINH",number,(char *)0)==0);
   CHECK(_dos_read(retained_handle,&byte,1,&got)==0 && got==1);
  }
 }else{
  CHECK(directory_resources_initialize()==0);
  if(owner==1)CHECK(capture_file_close()==0);
  if(owner==2)CHECK(monitor_file_close()==0);
  if(mode==15)CHECK(capture_file_release(other_probe,&mode)==0);
  if(mode==32 || mode==33)CHECK(capture_file_unclaim(&mode)==0);
  if(mode==34)CHECK(snapshot_file_close()==0);
  if(mode==35)CHECK(history_file_event(HISTORY_CLOSE,0,0)==0);
  CHECK(!capture_file_reserved(directory_resource_result.keyboard_path));
 }
 /* One process must also reset prior successful directory imports when the
  * next entry has blank/missing resources. Never reuse its selected bytes. */
 if(mode==24){
  memset(request.record,0,114);
  CHECK(directory_resources_stage(&request,defaults,output)==0);
  CHECK(output->mask==0 && output->keyboard_source==0 && output->actions_source==0);
  CHECK(!_fmemcmp(output->keyboard,defaults,948));
  for(i=0;i<10;++i)CHECK(output->actions[i*54]==3 && output->actions[i*54+1]==0 && output->actions[i*54+2]==0);
 }
 if(mode==25){
  _fmemcpy(&prior_bundle,output,sizeof(prior_bundle));
  request.cli_mask=512;strcpy(request.cli_keyboard,"C:\\ABSENT.KBD");
  CHECK(directory_resources_stage(&request,defaults,output)==DR_LOOKUP);
  CHECK(!_fmemcmp(output,&prior_bundle,sizeof(prior_bundle)));
 }
 CHECK(chdir(cwd)==0);
 file=fopen("BUNDLE.BIN","wb");CHECK(file!=0);
 for(i=0;i<sizeof(*output);i+=count){count=sizeof(*output)-i;if(count>512)count=512;
  _fmemcpy(chunk,((unsigned char __far *)output)+i,count);CHECK(fwrite(chunk,1,count,file)==count);}
 CHECK(!fclose(file));
 file=fopen("STATE.BIN","wb");CHECK(file!=0);CHECK(fwrite(&directory_resource_result,1,sizeof(directory_resource_result),file)==sizeof(directory_resource_result));CHECK(!fclose(file));
 report[0]=mode;report[1]=status;report[2]=checks;report[3]=opens;report[4]=closes;report[5]=canonical_calls;report[6]=attribute_calls;report[7]=held;report[8]=failed_witness;
 file=fopen("RESULT.BIN","wb");CHECK(file!=0);CHECK(fwrite(report,1,sizeof(report),file)==sizeof(report));CHECK(!fclose(file));
 _ffree(memory);printf("PASS mode %u checks %u\n",mode,checks);return 0;
}
