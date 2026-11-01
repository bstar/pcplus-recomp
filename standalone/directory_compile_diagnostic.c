#include "../src/directory/directory_compile.h"
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
#pragma aux directory_compile_storage "directory_compile_storage";
directory_compile_owner __far directory_compile_storage;
static unsigned mode,checks,testing,execs,opens,closes;
static directory_resource_bundle __far *bundle;
static directory_resource_bundle prior;
static directory_compile_owner saved;
static char source[64],target[64],helper[64],scratch[128];
static unsigned char chunk[256];
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL mode %u line %u state %u status %u detail %u dos %u child %u/%u/%u execs %u\n",mode,__LINE__,directory_compile_storage.state,directory_compile_storage.status,directory_compile_storage.source_status,directory_compile_storage.dos_error,directory_compile_storage.child.status,directory_compile_storage.child.dos_error,directory_compile_storage.child.child_status,execs);return 1;}}while(0)
unsigned __cdecl compile_test_open(const char *p,unsigned f,int *h)
{if(testing)++opens;return _dos_open(p,f,h);}
unsigned __cdecl compile_test_read(int h,void *p,unsigned n,unsigned *got){return _dos_read(h,p,n,got);}
unsigned __cdecl compile_test_close(int h)
{unsigned status=_dos_close(h);if(testing){++closes;if(mode==10)return 6;}return status;}
unsigned __far __cdecl compile_test_release(capture_file_probe p,void *q)
{return mode==9?CF_BUSY:capture_file_release(p,q);}
unsigned __cdecl process_run(const char *path,const char *tail,process_result *r)
{
 int child;
 ++execs;
 if(!directory_compile_exec_allowed() || !capture_file_reserved(source) || !capture_file_reserved(target) || !capture_file_reserved(helper) || !capture_file_reserved(scratch))return 4;
 memset(r,0,sizeof(*r));
 /* Component's declared DOS adapter; foreground tests separately exercise the
  * actual process_run implementation with UART/memory/IRQ ownership. */
 child=spawnl(P_WAIT,path,path,tail+1,(char *)0);
 if(child<0){r->status=3;r->dos_error=(unsigned)_doserrno;return 3;}
 r->child_status=(unsigned)child;r->retained_paragraphs=16;return 0;
}
int main(int argc,char **argv)
{
 unsigned i,status,want=0,count,held,owner=0,report[8];char cwd[64];FILE *f;
 directory_script_fingerprint before;directory_script_result io;
 if(argc!=2)return 2;mode=(unsigned)atoi(argv[1]);if(mode>18)return 2;
 CHECK(getcwd(cwd,64)!=0);strcpy(source,cwd);strcat(source,"\\GO.ASP");strcpy(target,cwd);strcat(target,"\\GO.ASX");strcpy(helper,"C:\\ASPCOMP.EXE");strcpy(scratch,cwd);strcat(scratch,"\\LPC00004.TMP");
 bundle=(directory_resource_bundle __far *)_fmalloc(sizeof(*bundle));CHECK(bundle!=0);_fmemset(bundle,0xcc,sizeof(*bundle));
 CHECK(directory_script_read(source,DSCRIPT_SOURCE,&before,&io)==0);
 for(i=0;i<64;++i)bundle->script_path[i]=i<strlen(source)+1?source[i]:0;
 for(i=0;i<12;++i)((unsigned char __far *)&bundle->script)[i]=((unsigned char *)&before)[i];
 _fmemcpy(&prior,bundle,sizeof(prior));CHECK(capture_file_initialize()==0);
 if(mode==2){f=fopen(source,"ab");CHECK(f!=0);fputs("; changed\n",f);CHECK(!fclose(f));}
 if(mode==3){f=fopen(target,"wb");CHECK(f!=0);fputs("SENTINEL",f);CHECK(!fclose(f));}
 if(mode==17)CHECK(!mkdir(target));
 if(mode>=5 && mode<=8){CHECK(capture_file_begin(mode==5?source:mode==6?target:mode==7?helper:scratch,(mode==6 || mode==8)?CF_NEW:CF_APPEND)==0);owner=1;}
 if(mode==18){CHECK(capture_file_begin("LPC00004.TMP",CF_NEW)==0);owner=1;}
 if(mode==16){
  _fmemset(&directory_compile_storage,0xa5,256);
  CHECK(directory_compile_run(0,bundle)==DC_ARGUMENT);
  CHECK(directory_compile_run(_psp,(directory_resource_bundle __far *)&directory_compile_storage)==DC_ARGUMENT);
  CHECK(directory_compile_run(_psp,(directory_resource_bundle __far *)MK_FP(0xffff,0xfff0))==DC_ARGUMENT);
  for(i=0;i<256;++i)CHECK(((unsigned char __far *)&directory_compile_storage)[i]==0xa5);
 }
 testing=1;status=directory_compile_run(_psp,bundle);testing=0;
 if(mode==1 || mode==4 || mode==13)want=DC_PROCESS;
 if(mode==2 || mode==11)want=DC_CHANGED;
 if(mode==3 || mode==17)want=DC_TARGET;
 if((mode>=5 && mode<=8) || mode==18)want=DC_CLAIM;
 if(mode==9)want=DC_RELEASE;if(mode==10)want=DC_SOURCE;
 if(mode==12 || mode==14)want=DC_OUTPUT;
 CHECK(status==want);
 held=mode==9 || mode==10 || mode==11 || mode==13 || mode==14;
 CHECK(directory_compile_storage.state==(held?DC_HELD:want?DC_FAILED:DC_DONE));
 CHECK(directory_compile_exec_allowed()==!held);
 CHECK(execs==((mode==0 || mode==1 || mode==4 || mode==9 || (mode>=11 && mode<=16))?1:0));
 if(want)CHECK(!_fmemcmp(bundle,&prior,sizeof(prior)));
 else{CHECK(bundle->script.kind==DSCRIPT_COMPILED);CHECK(!_fmemcmp(bundle->script_path,target,strlen(target)+1));}
 if(held){
  _fmemcpy(&saved,&directory_compile_storage,256);i=closes;
  CHECK(directory_compile_initialize()==DC_STATE && directory_compile_run(_psp,bundle)==DC_STATE);
  CHECK(closes==i && !_fmemcmp(&directory_compile_storage,&saved,256));
  CHECK(capture_file_reserved(source) && capture_file_reserved(target) && capture_file_reserved(helper) && capture_file_reserved(scratch));
 }
 if(owner)CHECK(capture_file_close()==0);
 f=fopen("BUNDLE.BIN","wb");CHECK(f!=0);
 for(i=0;i<sizeof(*bundle);i+=count){count=sizeof(*bundle)-i;if(count>256)count=256;_fmemcpy(chunk,((unsigned char __far *)bundle)+i,count);CHECK(fwrite(chunk,1,count,f)==count);}
 CHECK(!fclose(f));
 if(held){_fmemset(bundle,0x44,sizeof(*bundle));CHECK(capture_file_reserved(source) && capture_file_reserved(target) && !_fmemcmp(&directory_compile_storage,&saved,256));}
 f=fopen("STATE.BIN","wb");CHECK(f!=0);_fmemcpy(chunk,&directory_compile_storage,256);CHECK(fwrite(chunk,1,256,f)==256);CHECK(!fclose(f));
 report[0]=mode;report[1]=checks;report[2]=status;report[3]=execs;report[4]=held;report[5]=opens;report[6]=closes;report[7]=directory_compile_storage.installed;
 f=fopen("RESULT.BIN","wb");CHECK(f!=0);CHECK(fwrite(report,1,sizeof(report),f)==sizeof(report));CHECK(!fclose(f));_ffree(bundle);printf("PASS mode %u checks %u\n",mode,checks);return 0;
}
