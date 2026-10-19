#include "source_compile.h"
#include "script_path.h"
#include "runtime.h"
#include "serial.h"
#include "serial_runtime.h"
#include "../config/resource_path.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <process.h>
#include <fcntl.h>
#include <io.h>
#include <dos.h>
#include <errno.h>
#include <malloc.h>
#include <sys/stat.h>
extern unsigned __cdecl aspect_serial_psp(void);
unsigned runtime_compiler_calls,runtime_compiler_exit,runtime_compiler_dos_error;
static unsigned busy;
static unsigned missing(const char *path)
{unsigned attributes,status;status=_dos_getfileattr(path,&attributes);return status==2||status==3;}
static unsigned pcplus(const char *path,char *out)
{
 unsigned prefix,n;
 if(strchr(path,'\\')||strchr(path,':'))return 0;
 /* The directory helper's leaf grammar is intentionally ASCII-only. Keep
  * the loader's existing OEM filename domain by appending the already checked
  * script leaf ourselves, within that same64-byte resource buffer. */
 if(resource_pcplus_path(aspect_serial_psp(),"X",out))return 0;
 prefix=strlen(out)-1;n=strlen(path);if(prefix+n>=64)return 0;
 memcpy(out+prefix,path,n+1);return 1;
}
static unsigned preflight(const char *path)
{
 int handle;unsigned attributes,i;
 for(i=0;path[i];++i){unsigned char ch=path[i];if(ch<33||ch==127||ch=='"'||ch=='/'||ch=='*'||ch=='?'||ch=='<'||ch=='>'||ch=='|')return ASPECT_RUN_OPERAND;}
 if(_dos_getfileattr(path,&attributes)||attributes&_A_SUBDIR)return ASPECT_RUN_OPEN;
 handle=open(path,O_RDONLY|O_BINARY);if(handle<0)return ASPECT_RUN_OPEN;
 if(isatty(handle)){close(handle);return ASPECT_RUN_OPEN;}
 if(close(handle))return ASPECT_RUN_IO;return 0;
}
static int reserve_log(const char *source,char *path)
{
 unsigned i,n=0;int handle;const char *p;
 for(p=source;*p;++p)if(*p=='\\'||*p==':')n=(unsigned)(p-source+1);
 if(n+13>=128)return -1;
 memcpy(path,source,n);
 for(i=0;i<1000;++i){sprintf(path+n,"LPC%05X.LOG",i);handle=open(path,O_CREAT|O_EXCL|O_RDWR|O_BINARY,S_IREAD|S_IWRITE);if(handle>=0)return handle;}
 return -1;
}
static unsigned compile(const char *source)
{
 char compiler[64],log_path[128],buffer[128];
 int log=-1,out=-1,err=-1,result=-1,n;unsigned status=0,scope=0,paused=0,psp;
 void (__interrupt __far *break_vector)(void),(__interrupt __far *critical_vector)(void);
 if(busy)return ASPECT_RUN_STATE;busy=1;
 runtime_compiler_exit=runtime_compiler_dos_error=0;
 status=preflight(source);if(status)goto done;
 psp=aspect_serial_psp();
 if(resource_program_path(psp,"ASPCOMP.EXE",compiler)){status=ASPECT_RUN_OPEN;goto done;}
 status=preflight(compiler);if(status)goto done;
 if(runtime_console_cancel_poll()){status=runtime_error;goto done;}
 log=reserve_log(source,log_path);if(log<0){status=ASPECT_RUN_IO;goto done;}
 out=dup(1);err=dup(2);if(out<0||err<0){status=ASPECT_RUN_IO;goto done;}
 if(dup2(log,1)||dup2(log,2)){status=ASPECT_RUN_IO;goto done;}
 status=aspect_serial_compile_pause();if(status){runtime_serial_error=status;status=ASPECT_RUN_SERIAL;goto done;}paused=1;
 if(runtime_console_cancel_poll()){status=runtime_error;goto done;}
 status=runtime_compiler_scope(1);if(status)goto done;scope=1;
 break_vector=_dos_getvect(0x23);critical_vector=_dos_getvect(0x24);
 /* Release only unused CRT far heap segments. Live interpreter/session data
  * and IRQ code remain resident while Watcom's P_WAIT executor releases its
  * unused parent block and restores the parent's stack/PSP on return. */
 _fheapshrink();++runtime_compiler_calls;
 /* The compiler's default target is the same .ASX sibling. Passing only the
  * source keeps the native80-byte source path inside DOS's126-byte tail. */
 result=spawnl(P_WAIT,compiler,"ASPCOMP",source,(char *)0);
 runtime_compiler_exit=result<0?65535U:(unsigned)result;
 if(result<0){runtime_compiler_dos_error=errno;status=errno==ENOMEM?ASPECT_RUN_HEAP:ASPECT_RUN_OPEN;}
 else if(result)status=result==ASPECT_RUN_ARITHMETIC_FAULT?ASPECT_RUN_ARITHMETIC_FAULT:ASPECT_RUN_IO;
 if(aspect_serial_psp()!=psp||_dos_getvect(0x23)!=break_vector||_dos_getvect(0x24)!=critical_vector){
  _dos_setvect(0x23,break_vector);_dos_setvect(0x24,critical_vector);status=ASPECT_RUN_STATE;
 }
done:
 if(scope){unsigned r=runtime_compiler_scope(0);if(r&&!status)status=r;}
 if(paused){unsigned r=aspect_serial_compile_resume();if(r){runtime_serial_error=r;if(!status)status=ASPECT_RUN_SERIAL;}}
 if(out>=0){if(dup2(out,1)&&!status)status=ASPECT_RUN_IO;close(out);}
 if(err>=0){if(dup2(err,2)&&!status)status=ASPECT_RUN_IO;close(err);}
 if(log>=0){
  if(result>0&&lseek(log,0L,SEEK_SET)>=0){
   while((n=read(log,buffer,sizeof(buffer)))>0){unsigned i;for(i=0;i<(unsigned)n&&!runtime_error;++i)runtime_console_emit_byte((unsigned char)buffer[i]);if(runtime_error)break;}
  }
  if(close(log)&&!status)status=ASPECT_RUN_IO;
  if(remove(log_path)&&!status)status=ASPECT_RUN_IO;
 }
 if(!status&&runtime_console_cancel_poll())status=runtime_error;
 busy=0;return status;
}
unsigned runtime_source_open(aspect_file *file,char *path,unsigned source)
{
 char candidate[ASPECT_SCRIPT_PATH_CAPACITY],fallback[64],target[ASPECT_SCRIPT_PATH_CAPACITY];unsigned status,n;
 strcpy(candidate,path);
 if(!source){
  if(aspect_file_open(file,candidate)==ASPECT_FILE_OK)return 0;
  if(!missing(candidate))return ASPECT_RUN_OPEN;
  if(pcplus(candidate,fallback)){
   if(aspect_file_open(file,fallback)==ASPECT_FILE_OK)return 0;
   if(!missing(fallback))return ASPECT_RUN_OPEN;
  }
  n=strlen(candidate);candidate[n-1]='P';
 }
 status=preflight(candidate);
 if(status){
  if(!missing(candidate)||!pcplus(candidate,fallback))return status;
  strcpy(candidate,fallback);status=preflight(candidate);if(status)return status;
 }
 strcpy(target,candidate);n=strlen(target);target[n-1]='X';
 status=compile(candidate);if(status)return status;
 if(aspect_file_open(file,target)!=ASPECT_FILE_OK)return ASPECT_RUN_OPEN;
 strcpy(path,target);return 0;
}
