/* Actual DOS boundaries; explicitly selected injected failure results around
 * real short-prefix writes/truncation/commit/close. Fresh process per case. */
#include "../src/directory/phone_log_file.h"
#include "../src/directory/phone_log_fs.h"
#include "../src/capture/capture_fs.h"
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
unsigned phone_real_write(int,const void *,unsigned,unsigned *);
unsigned phone_real_close(int);
unsigned phone_real_seek(int,unsigned long);
unsigned phone_real_truncate(int);
unsigned phone_real_commit(int);
static unsigned mode,phase,io_calls,closes,checks;
static const char heading[]="HEADING\r\n",record[]="EVENT\r\n";
#define CHECK(c) do{++checks;if(!(c)){printf("FAIL %u line %u status %u DOS %u\n",mode,__LINE__,phone_log_file_result.status,phone_log_file_result.dos_error);return 1;}}while(0)
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{
 unsigned status;++io_calls;
 if((mode==1||mode==2||(mode>=4&&mode<=7)||mode==15||mode==16)&&phase==0){
  phase=1;status=phone_real_write(handle,data,3,written);
  if(status)return status;
  return mode==2?5:0;
 }
 return phone_real_write(handle,data,count,written);
}
unsigned phone_log_fs_seek(int handle,unsigned long position)
{++io_calls;if(mode==4&&phase==1)return 5;return phone_real_seek(handle,position);}
unsigned phone_log_fs_truncate(int handle)
{++io_calls;if(mode==5&&phase==1)return 5;return phone_real_truncate(handle);}
unsigned phone_log_fs_commit(int handle)
{
 ++io_calls;
 if(mode==3&&!phase){phase=1;return 5;}
 if(mode==6&&phase==1)return 5;
 return phone_real_commit(handle);
}
unsigned capture_fs_close(int handle)
{
 unsigned status;++io_calls;++closes;
 if((mode==7&&phase==1)||mode==8||mode==9){
  status=mode==9?0:phone_real_close(handle);
  return status?status:6;
 }
 return phone_real_close(handle);
}
static unsigned append(void)
{return phone_log_file_append("CALLS.FON",heading,9,record,7);}
static int seed(unsigned long length)
{
 unsigned long i;FILE *stream=fopen("CALLS.FON","wb");if(!stream)return 0;
 for(i=0;i<length;++i)if(fputc((unsigned char)(i*37+11),stream)==EOF){fclose(stream);return 0;}
 return fclose(stream)==0;
}
static unsigned long size(void)
{long length;FILE *stream=fopen("CALLS.FON","rb");if(!stream)return 0xffffffffUL;fseek(stream,0L,SEEK_END);length=ftell(stream);fclose(stream);return (unsigned long)length;}
int main(int argc,char **argv)
{
 unsigned status,before,i;unsigned long initial;
 unsigned char saved[20],maximum[256];unsigned char __far *jft;union REGS regs;
 phone_log_file_snapshot snapshot;FILE *state;
 if(argc!=2)return 1;mode=(unsigned)atoi(argv[1]);if(mode>17)return 1;
 initial=mode==10||mode==16?70001UL:mode==11||mode==15?0:8;
 regs.h.ah=0x62;intdos(&regs,&regs);jft=(unsigned char __far *)MK_FP(regs.x.bx,0x18);
 for(i=0;i<20;++i)saved[i]=jft[i];
 memset(&phone_log_file_result,0xa5,sizeof(phone_log_file_result));
 CHECK(phone_log_file_initialize()==PLF_OK&&phone_log_file_result.state==PLF_IDLE);
 if(mode!=11&&mode!=15)CHECK(seed(initial));
 if(mode==12){
  CHECK(_dos_setfileattr("CALLS.FON",_A_RDONLY)==0);
  CHECK(append()==PLF_INSPECT&&size()==initial);
 }else if(mode==13){
  snapshot=phone_log_file_result;
  CHECK(phone_log_file_append("NUL",0,0,record,7)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",0,0,(void *)0xfffe,7)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",0,0,&phone_log_file_result,7)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",0,0,record,0)==PLF_ARGUMENT);
  CHECK(!io_calls&&memcmp(&snapshot,&phone_log_file_result,sizeof(snapshot))==0);
 }else if(mode==14){
  /* DOSBox reports missing at attributes, then path-not-found at exclusive
   * create. Preserve that actual phase/error rather than guessing INSPECT. */
  CHECK(phone_log_file_append("NOEXIST\\CALLS.FON",0,0,record,7)==PLF_OPEN);
  CHECK(phone_log_file_result.dos_error==3);
  CHECK(!phone_log_file_result.handle_open&&!phone_log_file_result.committed);
 }else if(mode==17){
  for(i=0;i<sizeof(maximum);++i)maximum[i]=(unsigned char)i;
  CHECK(phone_log_file_append("CALLS.FON",0,0,maximum,256)==PLF_OK);
  CHECK(phone_log_file_result.requested==256&&phone_log_file_result.written==256&&size()==initial+256);
 }else{
  status=append();
  if(mode==0||mode==10||mode==11){
   CHECK(status==PLF_OK&&phone_log_file_result.committed);
   CHECK(phone_log_file_result.heading_bytes==(initial?0:9));
   CHECK(size()==initial+7+(initial?0:9));
  }else if(mode<=3||mode==15||mode==16){
   CHECK(status==(mode==3?PLF_COMMIT:PLF_WRITE));
   CHECK(size()==initial&&!phone_log_file_result.committed&&!phone_log_file_result.recovery_required);
   mode=0;CHECK(append()==PLF_OK);CHECK(size()==initial+7+(initial?0:9));
  }else{
   CHECK(status==(mode>=8?PLF_CLOSE:PLF_WRITE));
   CHECK(phone_log_file_result.recovery_required&&!phone_log_file_result.committed);
   CHECK(size()==initial+(mode==4||mode==5?3:mode>=8?7:0));
   snapshot=phone_log_file_result;before=io_calls;
   CHECK(phone_log_file_initialize()==PLF_RECOVERY&&append()==PLF_RECOVERY);
   CHECK(io_calls==before&&memcmp(&snapshot,&phone_log_file_result,sizeof(snapshot))==0&&closes==1);
  }
 }
 /* Mode9 deliberately models an unconsumed failed close. DOS process exit
  * owns that final handle cleanup; every other case restores the live JFT. */
 if(mode!=9)for(i=0;i<20;++i)CHECK(saved[i]==jft[i]);
 state=fopen("STATE.BIN","wb");CHECK(state!=0);
 CHECK(fwrite(&phone_log_file_result,1,sizeof(phone_log_file_result),state)==sizeof(phone_log_file_result));
 CHECK(fclose(state)==0);
 printf("PASS %u checked-append assertions\n",checks);return 0;
}
