#include <stdio.h>
#include <stdlib.h>
#include <dos.h>
#include <string.h>
#include "meta_loader.h"
#include "meta_editor.h"
extern meta_editor __far editor;
extern unsigned char __far live[540];
int meta_bank_flow_main(int,char **);
#ifdef META_LOADER_FAULTS
void __far __cdecl meta_load_fault(unsigned);
unsigned __far __cdecl meta_load_calls(unsigned);
#endif
static unsigned checks;
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL loader line %u phase %u reason %u DOS %u\r\n",__LINE__,meta_loader_inspect(0),meta_loader_inspect(1),meta_loader_inspect(2));return 1;}}while(0)
static unsigned pump(void)
{unsigned n=0,e;while(meta_loader_inspect(0)==META_LOAD_READING || meta_loader_inspect(0)==META_LOAD_FIXING){if(++n>2000)return 1;e=meta_loader_step(1);if(e)return e;}return 0;}
static unsigned dump(void)
{
 unsigned i,n=meta_loader_inspect(META_LOAD_BYTES);unsigned char __far *code=MK_FP(meta_loader_inspect(META_LOAD_SEGMENT),0);FILE *f=fopen("C:\\LOADED.BIN","wb");
 if(!f)return 1;for(i=0;i<n;++i)if(fputc(code[i],f)==EOF){fclose(f);return 1;}return fclose(f)!=0;
}
int main(int argc,char **argv)
{
 unsigned pos,n,error,expected,closed=0;char name[64]="TEST.KEY",path[64]="C:\\LAB\\TEST.KEY";
 CHECK(meta_loader_inspect(0)==META_LOAD_EMPTY);
 if(argc>1){
  expected=(unsigned)(argv[1][0]-'0');
#ifdef META_LOADER_FAULTS
  if(argc>2)meta_load_fault((unsigned)(argv[2][0]-'0'));
#endif
  error=meta_loader_begin(_psp,1);if(!error)error=pump();
  if(expected==META_LOAD_ARGUMENT){CHECK(error==expected && meta_loader_inspect(0)==META_LOAD_EMPTY && !meta_loader_inspect(META_LOAD_HANDLE_OPEN));printf("PASS loader header refusal %u checks;no IO or bank entry\r\n",checks);return 0;}
  CHECK(error==expected && meta_loader_inspect(META_LOAD_REASON)==expected);
  CHECK(meta_loader_inspect(0)==(expected==META_LOAD_RECOVERY?META_LOAD_HELD:META_LOAD_FAILED));
  CHECK(!meta_loader_inspect(META_LOAD_HANDLE_OPEN));
#ifdef META_LOADER_FAULTS
  closed=meta_load_calls(2);CHECK(closed==1);CHECK(meta_loader_step(1)==(expected==META_LOAD_RECOVERY?META_LOAD_RECOVERY:META_LOAD_STATE));
#endif
  CHECK(meta_loader_enter()==(expected==META_LOAD_RECOVERY?META_LOAD_RECOVERY:META_LOAD_STATE));
  CHECK(meta_loader_release()==(expected==META_LOAD_RECOVERY?META_LOAD_RECOVERY:META_LOAD_STATE));
  CHECK(meta_loader_cancel()==(expected==META_LOAD_RECOVERY?META_LOAD_RECOVERY:META_LOAD_OK));
#ifdef META_LOADER_FAULTS
  CHECK(meta_load_calls(2)==closed);
#endif
  printf("PASS loader refusal %u checks;reason %u;no bank entry;close calls %u\r\n",checks,expected,closed);return 0;
 }
 CHECK(meta_loader_begin(_psp,0)==META_LOAD_BUSY);
 CHECK(meta_loader_begin(_psp+1,1)==META_LOAD_ARGUMENT && meta_loader_inspect(0)==META_LOAD_EMPTY);
 CHECK(!meta_loader_begin(_psp,1));pos=meta_loader_inspect(META_LOAD_READ_AT);
 CHECK(meta_loader_step(0)==META_LOAD_BUSY && meta_loader_inspect(META_LOAD_READ_AT)==pos);
 CHECK(!meta_loader_cancel() && meta_loader_inspect(0)==META_LOAD_EMPTY);
 CHECK(!meta_loader_begin(_psp,1));
 for(n=0;meta_loader_inspect(0)==META_LOAD_READING && n<200;++n)CHECK(!meta_loader_step(1));
 CHECK(meta_loader_inspect(0)==META_LOAD_FIXING && !meta_loader_cancel());
 CHECK(!meta_loader_begin(_psp,1) && !pump() && meta_loader_inspect(0)==META_LOAD_READY);
 CHECK(!dump());printf("IMAGE base %u segment %u bytes %u\r\n",meta_loader_inspect(META_LOAD_BASE),meta_loader_inspect(META_LOAD_SEGMENT),meta_loader_inspect(META_LOAD_BYTES));
 CHECK(meta_loader_cancel()==META_LOAD_STATE && !meta_loader_enter());
 CHECK(!meta_bank_flow_main(argc,argv));
 CHECK(!meta_loader_release() && meta_loader_inspect(0)==META_LOAD_EMPTY);
 _fmemset(MK_FP(FP_SEG(&editor)+1024,0),0xcc,24000);
 CHECK(!meta_loader_begin(_psp,1) && !pump() && !meta_loader_enter());
 CHECK(!meta_editor_open(&editor,_psp,live,name,path,0x0607));
 CHECK(!meta_editor_step(&editor,1));
 CHECK(meta_loader_release()==META_LOAD_BUSY && meta_loader_inspect(0)==META_LOAD_ACTIVE);
 CHECK(!meta_editor_stop(&editor));
 for(n=0;editor.phase!=META_EDITOR_CLOSED && n<10;++n)CHECK(!meta_editor_step(&editor,1));
 CHECK(editor.phase==META_EDITOR_CLOSED && !meta_loader_release());
 CHECK(!meta_loader_begin(_psp,1) && !pump() && !meta_loader_release());
 CHECK(!meta_loader_begin(_psp,1) && !pump() && !meta_loader_enter());
 CHECK(meta_loader_hold()==META_LOAD_RECOVERY);
 CHECK(meta_loader_release()==META_LOAD_RECOVERY && meta_loader_cancel()==META_LOAD_RECOVERY && meta_loader_step(1)==META_LOAD_RECOVERY && meta_loader_enter()==META_LOAD_RECOVERY && meta_loader_begin(_psp,1)==META_LOAD_RECOVERY);
 printf("PASS loader %u checks;cancel/verify/relocate/workflow/overwrite/reload/lease/held\r\n",checks);return 0;
}
