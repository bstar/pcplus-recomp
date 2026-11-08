/* Injected into the full DOS dispatch diagnostic before main. Only GET's
 * ownership/recovery result is controlled; file, far heap and native release
 * use the actual runtime. Production GET remains disabled. */
#include "get_command.h"
extern void runtime_reset_native(void),runtime_cleanup(void),runtime_finish(void);
extern unsigned runtime_open(unsigned,const char *),runtime_close(unsigned);
extern void __far *runtime_alloc(unsigned);
extern void __far *runtime_strings[128];
static unsigned held,recover_calls,recover_status,recover_release;
unsigned __cdecl runtime_get_command_retained(void){return held;}
unsigned __cdecl runtime_get_command_recover(void)
{++recover_calls;if(recover_release)held=0;return recover_status;}
static void lifecycle_preserved(void __far *pointer,FILE *file)
{
 ck(runtime_strings[0]==pointer && runtime_string_count==1 && runtime_live==1);
 ck(runtime_file.handle==file && runtime_depth==7 && runtime_frame==123 && runtime_stack_pointer==456);
 ck(runtime_string_pending_far==0x12345678UL && runtime_string_pending_near==21);
 ck(runtime_cleanup_count==0 && runtime_close_count==0);
}
static void lifecycle_probe(void)
{
 void __far *pointer;FILE *file;unsigned i;
 current="GET lifecycle";
 runtime_error=0;runtime_reset_native();ck(aspect_file_init(&runtime_file)==ASPECT_FILE_OK);
 file=fopen("LIFE.ASX","wb");ck(file!=0);if(!file)return;
 fputc(0,file);fputc(0x94,file);fclose(file);
 ck(runtime_open(0,"LIFE.ASX")==1);
 pointer=runtime_alloc(81);ck(pointer!=0);if(!pointer)return;
 _fmemset(pointer,0,81);runtime_strings[0]=pointer;runtime_string_count=1;
 file=runtime_file.handle;
 runtime_depth=7;runtime_frame=123;runtime_stack_pointer=456;
 runtime_string_pending_far=0x12345678UL;runtime_string_pending_near=21;
 runtime_cleanup_count=runtime_close_count=0;held=1;
 /* No read of the invalid path/token, reset, free or close is admitted. */
 runtime_reset_native();ck(runtime_error==ASPECT_RUN_STATE);lifecycle_preserved(pointer,file);
 ck(runtime_open(0,(const char *)0)==0);lifecycle_preserved(pointer,file);
 ck(runtime_close(0)==65535U);lifecycle_preserved(pointer,file);
 ck(aspect_runtime_run("LIFE.ASX",10)==ASPECT_RUN_STATE);lifecycle_preserved(pointer,file);
 ck(recover_calls==0);
 /* A refused retirement is retryable; preserve first error on every pass. */
 runtime_error=ASPECT_RUN_CANCELLED;recover_status=ASPECT_RUN_IO;
 for(i=0;i<3;++i){runtime_cleanup();runtime_finish();lifecycle_preserved(pointer,file);ck(runtime_error==ASPECT_RUN_CANCELLED);}
 ck(recover_calls==6);
 /* A later authenticated retirement permits exactly one native release. */
 recover_release=1;runtime_finish();
 ck(recover_calls==7 && !held);ck(runtime_error==ASPECT_RUN_CANCELLED);
 ck(runtime_live==0 && runtime_string_count==0 && runtime_strings[0]==0);
 ck(runtime_file.handle==0 && runtime_cleanup_count==1 && runtime_close_count==1);
 ck(runtime_depth==0 && runtime_frame==runtime_stack_pointer);
 ck(runtime_string_pending_far==0 && runtime_string_pending_near==0);
 /* Successful recovery from cleanup alone also releases real heap storage. */
 runtime_error=0;runtime_reset_native();pointer=runtime_alloc(81);ck(pointer!=0);
 if(pointer){_fmemset(pointer,0,81);runtime_strings[0]=pointer;runtime_string_count=1;
  held=1;recover_status=0;runtime_cleanup();ck(!held && runtime_live==0 && runtime_string_count==0 && !runtime_error);}
 runtime_finish();recover_release=0;
}
