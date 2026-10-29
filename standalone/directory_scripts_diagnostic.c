/* Real DOS script preflight; explicit declared fault adapters only. */
#include "../src/directory/directory_resources.h"
#include "../src/capture/capture_file.h"
#include "../src/capture/capture_reservation.h"
#include <dos.h>
#include <direct.h>
#include <fcntl.h>
#include <io.h>
#include <malloc.h>
#include <process.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned mode,checks,opens,closes,bad,reads,script_reads,testing;
static int script_handle=-1;
static char cwd[64],script_path[64];
static directory_resource_request request,before;
static directory_resource_snapshot saved;
static unsigned char defaults[948],chunk[256];
static directory_resource_bundle prior;
static directory_resource_bundle __far *output;
unsigned translation_real_canonical(const char *,char *);
unsigned translation_real_attributes(const char *,unsigned *);
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL mode %u line %u status %u source %u state %u opens %u closes %u bad %u\n",mode,__LINE__,directory_resource_result.status,directory_resource_result.source_status,directory_resource_result.state,opens,closes,bad);return 1;}}while(0)
unsigned capture_fs_canonical(const char *p,char *q)
{return translation_real_canonical(p,q);}
unsigned capture_fs_attributes(const char *p,unsigned *q)
{if(testing && mode==27 && strstr(p,"GO.ASX"))return 5;return translation_real_attributes(p,q);}
unsigned translation_test_open(const char *p,unsigned flags,int *h)
{
 unsigned status;++opens;
 if(flags!=(O_RDONLY|O_NOINHERIT) || directory_resources_exec_allowed())bad=1;
 if(directory_resource_result.script_path[0] && !capture_file_reserved(directory_resource_result.script_path))bad=1;
 status=_dos_open(p,flags,h);
 if(mode==19 && opens==1 && chdir("\\OTHER"))bad=1;
 return status;
}
unsigned translation_test_close(int h){++closes;return _dos_close(h);}
unsigned __cdecl translation_xlt_open(const char *p,unsigned f,int *h){return translation_test_open(p,f,h);}
unsigned __cdecl translation_xlt_close(int h){return translation_test_close(h);}
unsigned __cdecl translation_test_read(int h,void *p,unsigned n,unsigned *got){++reads;return _dos_read(h,p,n,got);}
unsigned __cdecl script_test_open(const char *p,unsigned flags,int *h)
{unsigned status;if(mode==13){++opens;return 5;}status=translation_test_open(p,flags,h);if(!status)script_handle=*h;return status;}
unsigned __cdecl script_test_read(int h,void *p,unsigned n,unsigned *got)
{
 ++script_reads;
 if(mode==14 && script_reads==2){*got=0;return 5;}
 if(mode==22){*got=n+1;return 0;}
 if(mode==6 && n>7)n=7;
 return _dos_read(h,p,n,got);
}
unsigned __cdecl script_test_close(int h)
{if(mode==15 || mode==16){++closes;if(mode==16 && _dos_close(h))bad=1;return 6;}return translation_test_close(h);}
unsigned __far __cdecl translation_test_release(capture_file_probe p,void *q)
{return mode==18?CF_BUSY:capture_file_release(p,q);}
static unsigned poison(void)
{unsigned i;for(i=0;i<sizeof(*output);++i)if(((unsigned char __far *)output)[i]!=0xcc)return 0;return 1;}
int main(int argc,char **argv)
{
 unsigned i,status,expected=0,held,count,report[9],kind;FILE *f;
 unsigned char __far *allocation;char number[8],byte;
 directory_script_fingerprint fingerprint,old_fingerprint;directory_script_result result,old_result;
 if(argc!=2)return 2;mode=(unsigned)atoi(argv[1]);if(mode>27)return 2;
 CHECK(getcwd(cwd,64)!=0);strcpy(script_path,cwd);strcat(script_path,"\\GO.ASX");
 allocation=(unsigned char __far *)_fmalloc(sizeof(*output)+32);CHECK(allocation!=0);_fmemset(allocation,0xcc,sizeof(*output)+32);output=(directory_resource_bundle __far *)(allocation+16);
 memset(&request,0,sizeof(request));memset(defaults,0,sizeof(defaults));request.profile=6;request.psp=_psp;request.translation_mode=1;
 memcpy(request.record+0x56,"BOARD",6);memcpy(request.record+0x5f,"BOARD",6);
 memcpy(request.record+0x34,"GO",3);
 if(mode==0)request.record[0x34]=0;
 if(mode==20)memcpy(request.record+0x34,"CON",4);
 if(mode==10)memcpy(request.record+0x34,"A\\GO",5);
 if(mode==24)memcpy(request.record+0x34,"C:\\GO",6);
 if(mode==25)memcpy(request.record+0x34," ignored",9);
 for(i=0;i<79;++i)defaults[i*12]='A';
 memset(&fingerprint,0xcc,sizeof(fingerprint));memcpy(&old_fingerprint,&fingerprint,sizeof(fingerprint));
 memset(&result,0xcc,sizeof(result));memcpy(&old_result,&result,sizeof(result));
 CHECK(directory_script_read(0,1,&fingerprint,&result)==DSCRIPT_ARGUMENT);
 CHECK(directory_script_read(script_path,0,&fingerprint,&result)==DSCRIPT_ARGUMENT);
 CHECK(directory_script_read(script_path,1,0,&result)==DSCRIPT_ARGUMENT);
 CHECK(directory_script_read(script_path,1,&fingerprint,0)==DSCRIPT_ARGUMENT);
 CHECK(directory_script_read(script_path,1,(directory_script_fingerprint *)0xffff,&result)==DSCRIPT_ARGUMENT);
 CHECK(directory_script_read(script_path,1,&fingerprint,(directory_script_result *)0xffff)==DSCRIPT_ARGUMENT);
 CHECK(directory_script_read(script_path,1,&fingerprint,(directory_script_result *)&fingerprint)==DSCRIPT_ARGUMENT);
 CHECK(directory_script_read(script_path,1,(directory_script_fingerprint *)script_path,&result)==DSCRIPT_ARGUMENT);
 CHECK(directory_script_read("GO.ASX",1,&fingerprint,&result)==DSCRIPT_ARGUMENT);
 CHECK(!memcmp(&result,&old_result,sizeof(result)) && !memcmp(&fingerprint,&old_fingerprint,sizeof(fingerprint)) && !opens && !closes && !script_reads);
 CHECK(capture_file_initialize()==0 && directory_resources_initialize()==0);
 if(mode==17)CHECK(capture_file_claim(script_path,&mode)==0);
 memcpy(&before,&request,sizeof(before));testing=1;status=directory_resources_stage(&request,defaults,output);testing=0;
 if(mode==4 || mode==5 || mode==13 || mode==14 || mode==15 || mode==16 || mode==22)expected=DR_SCRIPT;
 if(mode==11 || mode==26 || mode==27)expected=DR_LOOKUP;
 if(mode==17)expected=DR_CLAIM;if(mode==18)expected=DR_RELEASE;if(mode==20)expected=DR_ARGUMENT;
 CHECK(status==expected && !bad && !memcmp(&before,&request,sizeof(before)));
 held=mode==15 || mode==16 || mode==18;CHECK(directory_resources_exec_allowed()==!held);
 if(expected)CHECK(poison());else{
  kind=mode==0 || mode==25?0:mode==7 || mode==8 || mode==12 || mode==21?2:1;
  CHECK(output->profile==6 && output->script.kind==kind && output->mask==20992);
  CHECK(output->keyboard[0]=='N' && output->keyboard[1]=='6' && output->actions[2]=='N');
  if(kind)CHECK(output->script_path[0]=='C' && output->script.bytes==(mode==12?0:output->script.bytes));
 }
 for(i=0;i<16;++i)CHECK(allocation[i]==0xcc && allocation[16+sizeof(*output)+i]==0xcc);
 if(mode==11 || mode==17 || mode==20 || mode==26 || mode==27)CHECK(!opens && !closes && !script_reads);
 if(mode==0 || mode==25)CHECK(opens==3 && !script_reads && !output->script_path[0]);
 if(mode==15 || mode==16)CHECK(directory_resource_result.script_handle==(unsigned)script_handle && directory_resource_result.close_error==6);
 if(held){
  memcpy(&saved,&directory_resource_result,sizeof(saved));i=closes;
  CHECK(directory_resources_initialize()==DR_RECOVERY && directory_resources_stage(&request,defaults,output)==DR_RECOVERY);
  CHECK(closes==i && !memcmp(&saved,&directory_resource_result,sizeof(saved)));
  CHECK(capture_file_reserved(directory_resource_result.script_path));
  if(mode==15){
   CHECK(lseek(script_handle,0L,SEEK_SET)==0L && _dos_read(script_handle,&byte,1,&count)==0 && count==1);
   sprintf(number,"%u",(unsigned)script_handle);
   /* Deliberately bypass product's refused EXEC to independently prove containment. */
   CHECK(spawnl(P_WAIT,"\\NOINH.COM","NOINH",number,(char *)0)==0);
   CHECK(_dos_read(script_handle,&byte,1,&count)==0 && count==1);
  }
 }else{if(mode==17)CHECK(capture_file_unclaim(&mode)==0);CHECK(!capture_file_reserved(script_path));}
 if(mode==23){_fmemcpy(&prior,output,sizeof(prior));memcpy(request.record+0x34,"MISSING",8);CHECK(directory_resources_stage(&request,defaults,output)==DR_LOOKUP);CHECK(!_fmemcmp(output,&prior,sizeof(prior)));}
 CHECK(chdir(cwd)==0);
 report[0]=mode;report[1]=checks;report[2]=opens;report[3]=closes;report[4]=script_reads;report[5]=held;report[6]=bad;report[7]=status;report[8]=directory_resource_result.source_status;
 f=fopen("RESULT.BIN","wb");CHECK(f!=0);CHECK(fwrite(report,1,sizeof(report),f)==sizeof(report));CHECK(!fclose(f));
 f=fopen("BUNDLE.BIN","wb");CHECK(f!=0);
 for(i=0;i<sizeof(*output);i+=count){count=sizeof(*output)-i;if(count>256)count=256;_fmemcpy(chunk,((unsigned char __far *)output)+i,count);CHECK(fwrite(chunk,1,count,f)==count);}
 CHECK(!fclose(f));_ffree(allocation);printf("PASS mode %u checks %u\n",mode,checks);return 0;
}
