/* Real DOS resource transaction; only declared errors are injected below. */
#include "../src/directory/directory_resources.h"
#include "../src/capture/capture_file.h"
#include "../src/capture/capture_reservation.h"
#include <dos.h>
#include <direct.h>
#include <fcntl.h>
#include <malloc.h>
#include <io.h>
#include <process.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned mode,checks,opens,closes,bad,testing,reads;
static int xlt_handle=-1;
static char cwd[64],xlt_path[64];
static directory_resource_request request,before;
static directory_resource_snapshot saved;
static unsigned char defaults[948],chunk[256];
static directory_resource_bundle prior;
static directory_resource_bundle __far *output;
unsigned translation_real_canonical(const char *,char *);
unsigned translation_real_attributes(const char *,unsigned *);
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL mode %u line %u status %u state %u opens %u closes %u bad %u\n",mode,__LINE__,directory_resource_result.status,directory_resource_result.state,opens,closes,bad);return 1;}}while(0)
unsigned capture_fs_canonical(const char *p,char *q)
{if(testing && mode==11)return 5;return translation_real_canonical(p,q);}
unsigned capture_fs_attributes(const char *p,unsigned *q)
{if(testing && mode==12)return 5;return translation_real_attributes(p,q);}
unsigned translation_test_open(const char *p,unsigned flags,int *h)
{
 unsigned status;
 ++opens;
 if(flags!=(O_RDONLY|O_NOINHERIT) || directory_resources_exec_allowed())bad=1;
 if(!capture_file_reserved(xlt_path) && request.translation_mode==1)bad=1;
 if(mode==4 && opens==3)return 5;
 status=_dos_open(p,flags,h);
 if(!status && strstr(p,".XLT"))xlt_handle=*h;
 if(mode==7 && opens==1 && chdir("\\OTHER"))bad=1;
 return status;
}
unsigned translation_test_close(int h)
{
 ++closes;
 if(h==xlt_handle && (mode==1 || mode==2)){
  if(mode==2 && _dos_close(h))bad=1;
  return 6;
 }
 return _dos_close(h);
}
unsigned __cdecl translation_xlt_open(const char *p,unsigned flags,int *h)
{return translation_test_open(p,flags,h);}
unsigned __cdecl translation_xlt_close(int h)
{return translation_test_close(h);}
unsigned __cdecl translation_test_read(int h,void *p,unsigned n,unsigned *got)
{++reads;if(mode==5){*got=0;return 5;}return _dos_read(h,p,n,got);}
unsigned __far __cdecl translation_test_release(capture_file_probe p,void *q)
{return mode==6?CF_BUSY:capture_file_release(p,q);}
static unsigned poison(void)
{unsigned i;for(i=0;i<sizeof(*output);++i)if(((unsigned char __far *)output)[i]!=0xcc)return 0;return 1;}
int main(int argc,char **argv)
{
 unsigned i,status,expected=0,held,count,report[8];FILE *f;
 char number[8],byte;
 if(argc!=2)return 2;mode=(unsigned)atoi(argv[1]);if(mode>15)return 2;
 CHECK(getcwd(cwd,64)!=0);strcpy(xlt_path,cwd);strcat(xlt_path,"\\PCPLUS.XLT");
 output=(directory_resource_bundle __far *)_fmalloc(sizeof(*output));CHECK(output!=0);_fmemset(output,0xcc,sizeof(*output));
 memset(&request,0,sizeof(request));memset(defaults,0,sizeof(defaults));
 request.profile=6;request.psp=_psp;request.translation_mode=mode==14?0:mode==15?2:1;
 memcpy(request.record+0x56,"BOARD",6);memcpy(request.record+0x5f,"BOARD",6);
 for(i=0;i<79;++i)defaults[i*12]='A';
 if(mode==8){request.cli_mask=16384;strcpy(request.cli_translation,"PCPLUS.XLT");}
 if(mode==9){request.cli_mask=16384;strcpy(request.cli_translation,xlt_path);request.translation_mode=3;}
 CHECK(capture_file_initialize()==0 && directory_resources_initialize()==0);
 if(mode==3)CHECK(capture_file_claim(xlt_path,&mode)==0);
 memcpy(&before,&request,sizeof(before));testing=1;
 status=directory_resources_stage(&request,defaults,mode==10?(directory_resource_bundle __far *)&request:output);
 testing=0;
 if(mode==1 || mode==2 || mode==4 || mode==5)expected=DR_TRANSLATION;
 if(mode==3)expected=DR_CLAIM;if(mode==6)expected=DR_RELEASE;
 if(mode>=8 && mode<=10)expected=DR_ARGUMENT;
 if(mode==11)expected=DR_CANONICAL;if(mode==12)expected=DR_LOOKUP;
 CHECK(status==expected && !bad && !memcmp(&before,&request,sizeof(before)));
 held=mode==1 || mode==2 || mode==6;
 CHECK(directory_resources_exec_allowed()==!held);
 if(expected)CHECK(poison());else{
  CHECK(output->profile==6 && output->translation_mode==request.translation_mode);
  CHECK(output->mask==(request.translation_mode==1?20992:4608));
  CHECK(!_fmemcmp(output->translation_path,request.translation_mode==1?xlt_path:"",request.translation_mode==1?strlen(xlt_path)+1:1));
  for(i=0;i<256;++i)CHECK(output->translation[i]==(request.translation_mode==1?(unsigned char)(i*73+19):0));
  CHECK(output->keyboard[0]=='N' && output->keyboard[1]=='6' && output->actions[2]=='N');
 }
 if(mode>=8 && mode<=10)CHECK(!opens && !closes && !reads);
 if(mode==3 || mode==11 || mode==12)CHECK(!opens && !closes);
 if(mode==14 || mode==15)CHECK(opens==2 && !reads && !directory_resource_result.translation_path[0]);
 if(held){
  memcpy(&saved,&directory_resource_result,sizeof(saved));i=closes;
  CHECK(directory_resources_initialize()==DR_RECOVERY);
  CHECK(directory_resources_stage(&request,defaults,output)==DR_RECOVERY);
  CHECK(closes==i && !memcmp(&saved,&directory_resource_result,sizeof(saved)));
  CHECK(capture_file_reserved(xlt_path));
  if(mode==1){
   CHECK(lseek(xlt_handle,0L,SEEK_SET)==0L);
   CHECK(_dos_read(xlt_handle,&byte,1,&count)==0 && count==1);
   sprintf(number,"%u",(unsigned)xlt_handle);
   /* Deliberately bypass refused product EXEC to independently test containment. */
   CHECK(spawnl(P_WAIT,"\\NOINH.COM","NOINH",number,(char *)0)==0);
   CHECK(_dos_read(xlt_handle,&byte,1,&count)==0 && count==1);
  }
 }else{
  if(mode==3)CHECK(capture_file_unclaim(&mode)==0);
  CHECK(!capture_file_reserved(xlt_path));
 }
 if(mode==13){
  _fmemcpy(&prior,output,sizeof(prior));request.cli_mask=16384;strcpy(request.cli_translation,"C:\\MISSING.XLT");
  CHECK(directory_resources_stage(&request,defaults,output)==DR_LOOKUP);
  CHECK(!_fmemcmp(output,&prior,sizeof(prior)));
 }
 CHECK(chdir(cwd)==0);
 report[0]=mode;report[1]=checks;report[2]=opens;report[3]=closes;report[4]=reads;report[5]=held;report[6]=bad;report[7]=status;
 f=fopen("RESULT.BIN","wb");CHECK(f!=0);CHECK(fwrite(report,1,sizeof(report),f)==sizeof(report));CHECK(!fclose(f));
 f=fopen("BUNDLE.BIN","wb");CHECK(f!=0);
 for(i=0;i<sizeof(*output);i+=count){count=sizeof(*output)-i;if(count>256)count=256;_fmemcpy(chunk,((unsigned char __far *)output)+i,count);CHECK(fwrite(chunk,1,count,f)==count);}
 CHECK(!fclose(f));_ffree(output);printf("PASS mode %u checks %u\n",mode,checks);return 0;
}
