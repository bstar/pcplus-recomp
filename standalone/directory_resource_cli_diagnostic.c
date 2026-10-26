#include "../src/directory/directory_resource_cli.h"
#include "../src/capture/capture_fs.h"
#include <direct.h>
#include <dos.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
unsigned terminal_option_mask;
char terminal_keyboard_path[64],terminal_actions_path[64];
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_keyboard_path "terminal_keyboard_path";
#pragma aux terminal_actions_path "terminal_actions_path";
unsigned __far __cdecl terminal_resource_cli_bind(void);
unsigned cli_real_canonical(const char *,char *);
static unsigned mode,checks,canonical_calls;
static directory_resource_request request,before;
static directory_resource_cli_snapshot bound;
static unsigned char record[114],defaults[948];
static char cwd[64];
static char original_keyboard[64],original_actions[64];
#define CHECK(c) do{++checks;if(!(c)){printf("FAIL mode %u line %u state %u status %u\n",mode,__LINE__,directory_resource_cli.state,directory_resource_cli.status);return 1;}}while(0)
unsigned capture_fs_canonical(const char *path,char *absolute)
{
 unsigned status;++canonical_calls;
 if((mode==7 && canonical_calls==1) || (mode==8 && canonical_calls==2))return 5;
 status=cli_real_canonical(path,absolute);
 if(!status && mode==9 && canonical_calls==1){memset(absolute,'X',64);absolute[64]=0;}
 return status;
}
int main(int argc,char **argv)
{
 unsigned i,status,bind_status,mask,expected_mask,report[7];
 unsigned char chunk[512];unsigned count;FILE *file;
 directory_resource_bundle __far *bundle;
 if(argc!=2)return 2;mode=(unsigned)atoi(argv[1]);if(mode>16)return 2;
 CHECK(getcwd(cwd,sizeof(cwd))!=0);
 memset(record,0,sizeof(record));memcpy(record+0x56,"BOARD",6);memcpy(record+0x5f,"BOARD",6);
 if(mode==15){for(i=0;i<0x56;++i)record[i]=(unsigned char)(i*37+0x80);for(i=0x68;i<114;++i)record[i]=(unsigned char)(i*17+3);}
 memset(defaults,0,sizeof(defaults));for(i=0;i<79;++i)defaults[i*12]=(unsigned char)('A'+i%26);
 bundle=(directory_resource_bundle __far *)_fmalloc(sizeof(*bundle));CHECK(bundle!=0);_fmemset(bundle,0xcc,sizeof(*bundle));
 memset(&request,0xa5,sizeof(request));memcpy(&before,&request,sizeof(before));
 CHECK(directory_resource_cli_request(record,4,_psp,&request)==DRC_STATE && !memcmp(&request,&before,sizeof(request)));
 strcpy(terminal_keyboard_path,"CLI.KBD");strcpy(terminal_actions_path,"CLI.KEY");
 mask=16|64|15|32768;
 if(mode!=0 && mode!=5)mask|=mode==2?512:mode==3?4096:512|4096;
 terminal_option_mask=mask;
 if(mode==6){strcpy(terminal_keyboard_path,cwd);strcat(terminal_keyboard_path,"\\CLI.KBD");terminal_keyboard_path[0]='c';}
 if(mode==10)strcpy(terminal_keyboard_path,"*");
 if(mode==11)strcpy(terminal_actions_path,"*");
 memcpy(original_keyboard,terminal_keyboard_path,64);memcpy(original_actions,terminal_actions_path,64);
 bind_status=terminal_resource_cli_bind();
 if(mode>=7 && mode<=11){
  CHECK(bind_status==((mode==8 || mode==11)?10:9));
  CHECK(directory_resource_cli.state==DRC_FAILED && directory_resource_cli.keyboard[0]==0 && directory_resource_cli.actions[0]==0);
  CHECK(terminal_option_mask==mask && !memcmp(original_keyboard,terminal_keyboard_path,64) && !memcmp(original_actions,terminal_actions_path,64));
  CHECK(directory_resource_cli.failed_resource==((mode==8 || mode==11)?4096:512));
  CHECK(directory_resource_cli_request(record,4,_psp,&request)==DRC_STATE && !memcmp(&request,&before,sizeof(request)));
  memcpy(&bound,&directory_resource_cli,sizeof(bound));i=canonical_calls;
  CHECK(directory_resource_cli_initialize()==0 && terminal_resource_cli_bind()!=0 && i==canonical_calls);
  CHECK(!memcmp(&bound,&directory_resource_cli,sizeof(bound)));
  status=DRC_STATE;
 }else{
  CHECK(bind_status==0 && directory_resource_cli.state==DRC_BOUND);
  CHECK(directory_resource_cli.original_mask==mask && terminal_option_mask==mask);
  if(mask&512)CHECK(!strcmp(terminal_keyboard_path,directory_resource_cli.keyboard) && terminal_keyboard_path[0]=='C');
  if(mask&4096)CHECK(!strcmp(terminal_actions_path,directory_resource_cli.actions) && terminal_actions_path[0]=='C');
  if(mode==0 || mode==5)CHECK(canonical_calls==0);
  memcpy(&bound,&directory_resource_cli,sizeof(bound));
  /* Directory-derived active choices must never become original overrides. */
  terminal_option_mask|=512|4096;strcpy(terminal_keyboard_path,"OLD.KBD");strcpy(terminal_actions_path,"OLD.KEY");
  if(mode==4 || mode==5)CHECK(chdir("\\OTHER")==0);
  if(mode==12){i=canonical_calls;CHECK(terminal_resource_cli_bind()!=0 && canonical_calls==i);}
  CHECK(directory_resource_cli_initialize()==0 && !memcmp(&bound,&directory_resource_cli,sizeof(bound)));
  CHECK(directory_resource_cli_request(record,5,_psp,&request)==DRC_ARGUMENT && !memcmp(&request,&before,sizeof(request)));
  CHECK(directory_resource_cli_request(record,4,0,&request)==DRC_ARGUMENT && !memcmp(&request,&before,sizeof(request)));
  CHECK(directory_resource_cli_request((unsigned char *)0xfff0,4,_psp,&request)==DRC_ARGUMENT);
  CHECK(directory_resource_cli_request(record,4,_psp,(directory_resource_request *)record)==DRC_ARGUMENT);
  CHECK(directory_resource_cli_request(record,4,_psp,(directory_resource_request *)&directory_resource_cli)==DRC_ARGUMENT);
  CHECK(directory_resource_cli_request(record,mode==16?6:4,_psp,&request)==0);
  expected_mask=mask&(512|4096);
  CHECK(request.cli_mask==expected_mask && !memcmp(request.record,record,114));
  CHECK(!memcmp(request.cli_keyboard,bound.keyboard,64) && !memcmp(request.cli_actions,bound.actions,64));
  CHECK(directory_resources_initialize()==0);
  status=directory_resources_stage(&request,defaults,bundle);
  CHECK(status==(mode==13?DR_LOOKUP:mode==14?DR_ACTIONS:0));
 }
 CHECK(chdir(cwd)==0);
 file=fopen("CLI.BIN","wb");CHECK(file!=0);CHECK(fwrite(&directory_resource_cli,1,sizeof(directory_resource_cli),file)==sizeof(directory_resource_cli));CHECK(!fclose(file));
 file=fopen("REQUEST.BIN","wb");CHECK(file!=0);CHECK(fwrite(&request,1,sizeof(request),file)==sizeof(request));CHECK(!fclose(file));
 file=fopen("BUNDLE.BIN","wb");CHECK(file!=0);
 for(i=0;i<sizeof(*bundle);i+=count){count=sizeof(*bundle)-i;if(count>512)count=512;_fmemcpy(chunk,((unsigned char __far *)bundle)+i,count);CHECK(fwrite(chunk,1,count,file)==count);}CHECK(!fclose(file));
 report[0]=mode;report[1]=checks;report[2]=bind_status;report[3]=status;report[4]=canonical_calls;report[5]=mask;report[6]=directory_resource_cli.state;
 file=fopen("RESULT.BIN","wb");CHECK(file!=0);CHECK(fwrite(report,1,sizeof(report),file)==sizeof(report));CHECK(!fclose(file));
 _ffree(bundle);printf("PASS mode %u checks %u\n",mode,checks);return 0;
}
