#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include <direct.h>
#include "meta_key_resource.h"
#include "meta_picker_scan.h"
#include "key_editor_file.h"
#include "../src/config/resource_path.h"
#include "meta_resource_faults.h"
extern meta_picker_scan __far scan;
extern meta_picker_state __far picker;
extern unsigned char __far entries[META_PICKER_BYTES];
extern unsigned char __far records[1620];
#define baseline records
#define next (records+540)
#define loaded (records+1080)
static meta_key_resource_result result,before;
static key_actions_dos_result read_result;
static directory_replace_result save_result;
static unsigned checks,pspseg,envseg;
static char request[64],frozen[64],pattern[64],selected[9],cwd[64],other_cwd[64],now[64];
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %u check %u status %u dos %u env %u source %u path %.63s\r\n",__LINE__,checks,result.status,result.dos_error,result.environment_error,result.source,result.path);exit(1);}}while(0)
static unsigned ds(void);
#pragma aux ds = "mov ax,ds" value [ax] modify [];
static unsigned ss(void);
#pragma aux ss = "mov ax,ss" value [ax] modify [];
static void environment(const char *p,unsigned n,unsigned bad)
{_fmemset(MK_FP(envseg,0),bad?'X':0,512);_fmemcpy(MK_FP(envseg,0),p,n);}
static unsigned lookup(const char *p)
{memset(request,0,64);strcpy(request,p);return meta_key_resource_lookup(pspseg,request,&result);}
static void good_env(void){environment("PCPLUS=C:\\FALL",15,0);}
static void list(const char *p)
{unsigned n=0;CHECK(!meta_picker_begin(&picker,entries));CHECK(!meta_picker_scan_begin(&scan,&picker,p));while(scan.phase==META_SCAN_READ || scan.phase==META_SCAN_SORT){CHECK(++n<1000);CHECK(!meta_picker_scan_step(&scan));}CHECK(scan.phase==META_SCAN_DONE);}
static int put(const char *p,const unsigned char __far *v)
{FILE *f=fopen(p,"wb");unsigned i;if(!f)return 0;for(i=0;i<540;++i)if(fputc(v[i],f)==EOF){fclose(f);return 0;}return !fclose(f);}
int main(void)
{
 unsigned i,mode,calls,status;
 CHECK(ds()==ss() && FP_SEG(records)!=ds());CHECK(!_dos_allocmem(16,&pspseg));CHECK(!_dos_allocmem(32,&envseg));_fmemset(MK_FP(pspseg,0),0,256);*(unsigned __far *)MK_FP(pspseg,0x2c)=envseg;
 CHECK(getcwd(cwd,64)!=0 && !strcmp(cwd,"D:\\KEEP"));CHECK(_getdcwd(3,other_cwd,64)!=0 && !strcmp(other_cwd,"C:\\ALT"));
 good_env();resource_reset(0);CHECK(!lookup("BOTH.KEY") && result.source==META_RESOURCE_CURRENT && result.exists && !strcmp(result.path,"D:\\KEEP\\BOTH.KEY") && resource_canonical_calls==1);
 CHECK(!key_editor_file_load(result.path,loaded,&read_result) && loaded[2]=='D');
 environment("PCPLUS=C:\\FALL",15,1);resource_reset(0);CHECK(!lookup("BOTH.KEY") && resource_canonical_calls==1);CHECK(lookup("ONLY.KEY")==META_RESOURCE_ENVIRONMENT && result.environment_error==RESOURCE_PATH_ENVIRONMENT);
 good_env();resource_reset(0);CHECK(!lookup("ONLY.KEY") && result.source==META_RESOURCE_PCPLUS && !strcmp(result.path,"C:\\FALL\\ONLY.KEY") && resource_canonical_calls==2);
 CHECK(!_dos_setfileattr(result.path,_A_RDONLY));CHECK(!lookup("ONLY.KEY") && result.exists);CHECK(!_dos_setfileattr(result.path,0));
 CHECK(!lookup("!PUNCT.KEY") && result.source==META_RESOURCE_PCPLUS && !strcmp(result.path,"C:\\FALL\\!PUNCT.KEY"));
 CHECK(!lookup("BAD.KEY") && result.source==META_RESOURCE_CURRENT);_fmemset(loaded,0xa5,540);CHECK(key_editor_file_load(result.path,loaded,&read_result)==KEY_ACTIONS_DOS_SIZE);for(i=0;i<540;++i)CHECK(loaded[i]==0xa5);
 CHECK(lookup("FOLDER.KEY")==META_RESOURCE_INSPECT);
 CHECK(lookup("MISSING.KEY")==META_RESOURCE_MISSING && result.source==META_RESOURCE_PCPLUS && !strcmp(result.path,"C:\\FALL\\MISSING.KEY") && !result.exists);
 environment("PATH=C:\\DOS",12,0);CHECK(lookup("MISSING.KEY")==META_RESOURCE_MISSING && result.source==META_RESOURCE_CURRENT && !strcmp(result.path,"D:\\KEEP\\MISSING.KEY"));CHECK(meta_key_resource_pattern(pspseg,1,&result)==META_RESOURCE_MISSING && !result.path[0]);
 environment("PCPLUS=\0PCPLUS=C:\\FALL",23,0);CHECK(lookup("ONLY.KEY")==META_RESOURCE_MISSING && result.source==META_RESOURCE_CURRENT);
 good_env();CHECK(!lookup("C:\\FALL\\ONLY.KEY") && result.source==META_RESOURCE_EXPLICIT);CHECK(lookup("C:ONLY.KEY")==META_RESOURCE_MISSING && result.source==META_RESOURCE_EXPLICIT && !strcmp(result.path,"C:\\ALT\\ONLY.KEY"));
 /* A successful current file does not need a valid environment/PSP. */
 strcpy(request,"BOTH.KEY");CHECK(!meta_key_resource_lookup(0,request,&result));
 for(mode=1;mode<=5;++mode){
  resource_reset(mode);status=lookup("BOTH.KEY");CHECK(status==(mode==1?META_RESOURCE_CANONICAL:mode==3?META_RESOURCE_PATH:mode==4?META_RESOURCE_MISSING:META_RESOURCE_INSPECT));
  if(mode!=4)CHECK(resource_canonical_calls==1);
 }
 resource_reset(4);CHECK(meta_key_resource_pattern(pspseg,0,&result)==META_RESOURCE_PATH);resource_reset(0);
 /* Real current-list precedence and deferred fallback, then frozen selection. */
 environment("PCPLUS=C:\\FALL",15,1);CHECK(!meta_key_resource_pattern(0,0,&result) && !strcmp(result.path,"D:\\KEEP\\*.KEY"));list(result.path);CHECK(picker.count==2); /* bad file bytes are not read by enumeration */
 CHECK(!chdir("D:\\EMPTY"));good_env();CHECK(!meta_key_resource_pattern(pspseg,0,&result));list(result.path);CHECK(picker.phase==META_PICKER_EMPTY);
 CHECK(!meta_key_resource_pattern(pspseg,1,&result) && !strcmp(result.path,"C:\\FALL\\*.KEY"));strcpy(pattern,result.path);list(pattern);CHECK(picker.count==4);CHECK(!meta_picker_key(&picker,13));CHECK(!meta_picker_selected(&picker,selected) && !strcmp(selected,"!PUNCT"));
 calls=resource_calls;CHECK(!meta_key_resource_selected(pattern,selected,frozen) && !strcmp(frozen,"C:\\FALL\\!PUNCT.KEY") && resource_calls==calls);
 CHECK(!key_editor_file_load(frozen,loaded,&read_result) && loaded[2]=='P');CHECK(!chdir("D:\\KEEP"));
 /* Save uses the accepted identity even after a new current copy appears. */
 CHECK(!lookup("ONLY.KEY"));strcpy(frozen,result.path);CHECK(!key_editor_file_load(frozen,baseline,&read_result));_fmemcpy(next,baseline,540);next[2]='!';CHECK(put("D:\\KEEP\\ONLY.KEY",baseline));CHECK(!chdir("D:\\EMPTY"));CHECK(!key_editor_file_save(frozen,baseline,next,&save_result) && save_result.installed);CHECK(!key_editor_file_load(frozen,loaded,&read_result) && !_fmemcmp(loaded,next,540));CHECK(!key_editor_file_load("D:\\KEEP\\ONLY.KEY",loaded,&read_result) && !_fmemcmp(loaded,baseline,540));CHECK(!chdir("D:\\KEEP"));
 resource_reset(0);memset(&result,0xa5,sizeof(result));before=result;strcpy(request,"..\\BAD.KEY");CHECK(meta_key_resource_lookup(pspseg,request,&result)==META_RESOURCE_ARGUMENT && !resource_calls && !memcmp(&result,&before,sizeof(result)));
 strcpy(request,"BOTH.KEY");CHECK(meta_key_resource_lookup(pspseg,request,(meta_key_resource_result *)request)==META_RESOURCE_ARGUMENT && !resource_calls);
 CHECK(meta_key_resource_lookup(pspseg,(const char *)0xfff0,&result)==META_RESOURCE_ARGUMENT && !resource_calls);
 CHECK(meta_key_resource_pattern(pspseg,2,&result)==META_RESOURCE_ARGUMENT && !resource_calls);
 strcpy(pattern,"C:\\FALL\\*.KEY");strcpy(selected,"A.B");memset(frozen,0xa5,64);CHECK(meta_key_resource_selected(pattern,selected,frozen)==META_RESOURCE_ARGUMENT && !resource_calls);for(i=0;i<64;++i)CHECK((unsigned char)frozen[i]==0xa5);
 strcpy(selected,"ONLY");CHECK(meta_key_resource_selected(pattern,selected,pattern)==META_RESOURCE_ARGUMENT && !resource_calls);
 CHECK(getcwd(now,64)!=0 && !strcmp(cwd,now));CHECK(_getdcwd(3,now,64)!=0 && !strcmp(other_cwd,now));CHECK(!_dos_freemem(envseg));CHECK(!_dos_freemem(pspseg));
 printf("PASS %u checks; canonical KEY lookup/current-PCPLUS precedence;picker fallback;frozen load/save\r\n",checks);return 0;
}
