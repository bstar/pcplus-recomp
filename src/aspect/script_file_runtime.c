/* Owned DOS stdio behind the recovered eight-byte near FILE prefix.
 * Script slots survive EXECUTE; the invocation's finish closes them all.
 * This component has not yet been connected to the interpreter/compiler.
 * Native FCLEAR edits prefix bits directly, so prepare reconciles clearerr.
 */
#include "script_file_runtime.h"
#include "runtime.h"
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <io.h>
#include <errno.h>

typedef char prefix_size_check[sizeof(aspect_script_file_prefix)==8?1:-1];
typedef char prefix_flags_check[offsetof(aspect_script_file_prefix,flags)==6?1:-1];
typedef char prefix_descriptor_check[offsetof(aspect_script_file_prefix,descriptor)==7?1:-1];
typedef struct script_owner {
 aspect_script_file_prefix native;
 FILE *stream;
 unsigned char eof_latched,error_latched;
 unsigned char buffer[512];
} script_owner;
static script_owner owners[ASPECT_SCRIPT_FILE_SLOTS];
aspect_script_file_prefix *runtime_script_file_slots[ASPECT_SCRIPT_FILE_SLOTS];
aspect_script_file_prefix runtime_script_file_fallback;
unsigned runtime_script_file_last,runtime_script_file_keep_crlf;
unsigned char runtime_script_file_mode_flags[256];
static char mode_scratch[81];
char *runtime_script_file_mode_pointer=mode_scratch;
unsigned runtime_script_file_live,runtime_script_file_peak;
unsigned runtime_script_file_open_calls,runtime_script_file_close_calls;
unsigned runtime_script_file_cleanup_errors;

static script_owner *owned(aspect_script_file_prefix *native)
{
 unsigned slot;
 for(slot=0;slot<ASPECT_SCRIPT_FILE_SLOTS;++slot)
  if(native==&owners[slot].native && owners[slot].stream)return &owners[slot];
 runtime_set_error(ASPECT_RUN_STATE);return 0;
}
static void sync(script_owner *owner)
{
 owner->native.flags&=(unsigned char)~(ASPECT_SCRIPT_FILE_EOF|ASPECT_SCRIPT_FILE_ERROR);
 if(feof(owner->stream))owner->eof_latched=1;
 if(ferror(owner->stream))owner->error_latched=1;
 if(owner->eof_latched)owner->native.flags|=ASPECT_SCRIPT_FILE_EOF;
 if(owner->error_latched)owner->native.flags|=ASPECT_SCRIPT_FILE_ERROR;
}
static script_owner *prepare(aspect_script_file_prefix *native)
{
 script_owner *owner=owned(native);
 if(owner){
  owner->eof_latched=(unsigned char)((native->flags&ASPECT_SCRIPT_FILE_EOF)!=0);
  owner->error_latched=(unsigned char)((native->flags&ASPECT_SCRIPT_FILE_ERROR)!=0);
  if((!owner->eof_latched && feof(owner->stream)) ||
     (!owner->error_latched && ferror(owner->stream)))clearerr(owner->stream);
 }
 return owner;
}
static int close_owner(script_owner *owner)
{
 int result,descriptor=owner->native.descriptor;
 result=fclose(owner->stream);owner->stream=0;
 owner->native.flags=0;runtime_script_file_mode_flags[descriptor]=0;
 owner->eof_latched=owner->error_latched=0;
 ++runtime_script_file_close_calls;
 if(runtime_script_file_live)--runtime_script_file_live;
 else runtime_set_error(ASPECT_RUN_STATE);
 return result;
}
unsigned runtime_script_files_reset(void)
{
 unsigned slot;
 if(runtime_script_file_live)return ASPECT_RUN_STATE;
 for(slot=0;slot<ASPECT_SCRIPT_FILE_SLOTS;++slot)
  if(owners[slot].stream)return ASPECT_RUN_STATE;
 memset(owners,0,sizeof(owners));memset(runtime_script_file_slots,0,sizeof(runtime_script_file_slots));
 memset(runtime_script_file_mode_flags,0,sizeof(runtime_script_file_mode_flags));
 memset(&runtime_script_file_fallback,0,sizeof(runtime_script_file_fallback));
 runtime_script_file_fallback.flags=2;runtime_script_file_fallback.descriptor=2;
 runtime_script_file_mode_flags[2]=ASPECT_SCRIPT_FILE_TEXT;
 runtime_script_file_last=0;runtime_script_file_keep_crlf=1;
 runtime_script_file_peak=runtime_script_file_open_calls=runtime_script_file_close_calls=0;
 runtime_script_file_cleanup_errors=0;mode_scratch[0]=0;
 return 0;
}
void runtime_script_files_finish(void)
{
 unsigned slot;
 /* Keep going after a flush/close failure so every other owned stream closes.
  * Native outer cleanup discards close results; expose them diagnostically
  * without replacing the script's last comparison or existing runtime error. */
 for(slot=0;slot<ASPECT_SCRIPT_FILE_SLOTS;++slot){
  if(owners[slot].stream && close_owner(&owners[slot]))++runtime_script_file_cleanup_errors;
  runtime_script_file_slots[slot]=0;
 }
}
aspect_script_file_prefix *runtime_script_file_open(const char *path,const char *mode)
{
 script_owner *owner;FILE *stream;int descriptor;unsigned slot=runtime_script_file_last;
 if(slot>=ASPECT_SCRIPT_FILE_SLOTS || !path || !mode){runtime_set_error(ASPECT_RUN_STATE);return 0;}
 owner=&owners[slot];
 if(owner->stream){runtime_set_error(ASPECT_RUN_STATE);return 0;}
 ++runtime_script_file_open_calls;
 stream=fopen(path,mode);if(!stream)return 0;
 descriptor=fileno(stream);
 if(descriptor<0 || descriptor>255 || setvbuf(stream,(char *)owner->buffer,_IOFBF,sizeof(owner->buffer))){
  fclose(stream);return 0;
 }
 memset(&owner->native,0,sizeof(owner->native));owner->stream=stream;
 owner->eof_latched=owner->error_latched=0;
 owner->native.descriptor=(unsigned char)descriptor;
 owner->native.flags=(unsigned char)((mode[0]=='r'?1:2)|(strchr(mode,'+')?0x80:0));
 runtime_script_file_mode_flags[descriptor]=(unsigned char)(strchr(mode,'b')?0:ASPECT_SCRIPT_FILE_TEXT);
 ++runtime_script_file_live;
 if(runtime_script_file_live>runtime_script_file_peak)runtime_script_file_peak=runtime_script_file_live;
 return &owner->native;
}
int runtime_script_file_close(aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);return owner?close_owner(owner):-1;
}
int runtime_script_file_flush(aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);int result;
 if(!owner)return -1;result=fflush(owner->stream);sync(owner);return result;
}
int runtime_script_file_getc(aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);int result;
 if(!owner)return -1;result=fgetc(owner->stream);sync(owner);return result;
}
char *runtime_script_file_gets(char *buffer,int size,aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);char *result;
 if(!owner)return 0;
 if(!buffer || size<1 || size>81){runtime_set_error(ASPECT_RUN_OPERAND);return 0;}
 result=fgets(buffer,size,owner->stream);sync(owner);return result;
}
int runtime_script_file_putc(int value,aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);int result;
 if(!owner)return -1;result=fputc(value,owner->stream);sync(owner);return result;
}
int runtime_script_file_puts(const char *value,aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);int result;
 if(!owner)return -1;if(!value){runtime_set_error(ASPECT_RUN_OPERAND);return -1;}
 result=fputs(value,owner->stream);sync(owner);return result;
}
unsigned runtime_script_file_read(void *buffer,unsigned size,unsigned count,aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);unsigned result;
 if(!owner)return 0;
 if(!buffer || size!=1 || count>80){runtime_set_error(ASPECT_RUN_OPERAND);return 0;}
 result=fread(buffer,size,count,owner->stream);sync(owner);return result;
}
unsigned runtime_script_file_write(const void *buffer,unsigned size,unsigned count,aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);unsigned result;
 if(!owner)return 0;
 if(!buffer || size!=1 || count>80){runtime_set_error(ASPECT_RUN_OPERAND);return 0;}
 result=fwrite(buffer,size,count,owner->stream);sync(owner);return result;
}
int runtime_script_file_seek(aspect_script_file_prefix *native,long position,int origin)
{
 script_owner *owner=prepare(native);int result;long previous,end,target;
 if(!owner)return -1;
 if(origin<0 || origin>2){runtime_set_error(ASPECT_RUN_OPERAND);return -1;}
 /* Native853A computes CUR from logical ftell before discarding the buffer.
  * NativeA22E rejects a negative resulting position before asking DOS, whose
  * own negative-seek behavior differs across implementations. Unsigned sums
  * preserve the original 32-bit ADD/ADC wrap without C signed overflow. */
 if(origin==1){position=(long)((unsigned long)ftell(owner->stream)+(unsigned long)position);origin=0;}
 clearerr(owner->stream);owner->eof_latched=0;owner->native.flags&=(unsigned char)~ASPECT_SCRIPT_FILE_EOF;
 (void)fflush(owner->stream);
 if(origin==0 && position<0){errno=EINVAL;result=-1;}
 else if(origin==2 && position<0){
  previous=ftell(owner->stream);
  result=fseek(owner->stream,0L,2);
  if(!result){
   end=ftell(owner->stream);target=(long)((unsigned long)end+(unsigned long)position);
   if(target<0){(void)fseek(owner->stream,previous,0);errno=EINVAL;result=-1;}
   else result=fseek(owner->stream,position,2);
  }
 }else result=fseek(owner->stream,position,origin);
 sync(owner);return result;
}
long runtime_script_file_tell(aspect_script_file_prefix *native)
{
 script_owner *owner=prepare(native);long result;
 if(!owner)return -1L;result=ftell(owner->stream);sync(owner);return result;
}
