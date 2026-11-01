/* Actual DOS environment/path/queue integration, synthetic contacts only. */
#include "../src/directory/phone_log_startup.h"
#include "../src/directory/phone_log_queue.h"
#include "../src/capture/capture_fs.h"
#include <dos.h>
#include <direct.h>
#include <io.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify exact [];
#define CHECK(c) do{++checks;if(!(c)){printf("FAIL line%u\n",__LINE__);return 1;}}while(0)
static int seed(const char *path,const char *text)
{FILE *f=fopen(path,"wb");unsigned n=(unsigned)strlen(text),written;if(!f)return 0;written=fwrite(text,1,n,f);return fclose(f)==0&&written==n;}
int main(int argc,char **argv)
{
 unsigned char image[1264],saved[1264],jft[20],__far *actual_jft;
 phone_log_queue_snapshot before,after;
 phone_log_stamp start={1999,12,31,23,59,58},end={2000,1,1,0,0,3};
 unsigned mode,status,expected=PLS_OK,flag,i,psp,words[4],active_case;
 union REGS regs;char original[128],selected[128];
 const unsigned char *input=image;
 if(argc!=2)return 1;mode=(unsigned)atoi(argv[1]);if(mode>15)return 1;
 active_case=mode==11||mode==13||mode==14||mode==15;
 regs.h.ah=0x62;intdos(&regs,&regs);psp=regs.x.bx;
 actual_jft=(unsigned char __far *)MK_FP(psp,0x18);
 for(i=0;i<20;++i)jft[i]=actual_jft[i];
 CHECK(FP_SEG((void __far *)image)==stack_segment());
 CHECK(phone_log_queue_initialize()==PLQ_OK);
 CHECK(mkdir("ENV")==0&&mkdir("AFTER")==0);
 CHECK(capture_fs_canonical("PCPLUS.FON",original)==0);
 memset(image,0x5a,sizeof(image));flag=mode==0||mode==13?0:mode==2?256:mode==4?65535:1;
 image[0x1e6]=(unsigned char)flag;image[0x1e7]=(unsigned char)(flag>>8);
 memcpy(saved,image,sizeof(image));
 if(mode==1||mode==3||mode==5)CHECK(seed("PCPLUS.FON",""));
 if(mode==3)CHECK(seed("ENV\\PCPLUS.FON","UNTOUCHED"));
 if(mode==5){CHECK(_dos_setfileattr("PCPLUS.FON",1)==0);expected=PLS_FILESYSTEM;}
 if(mode==6){CHECK(mkdir("PCPLUS.FON")==0);expected=PLS_FILESYSTEM;}
 if(mode==7)expected=PLS_FILESYSTEM;
 if(mode==8||mode==9)expected=PLS_RESOURCE;
 if(mode==10||mode==12)expected=PLS_ARGUMENT;
 if(active_case){
  CHECK(capture_fs_canonical("OTHER.FON",selected)==0);
  CHECK(phone_log_queue_configure(1,selected)==PLQ_OK);
  CHECK(phone_log_queue_start(1,"LoC LAB","5550100",&start)==PLQ_OK);
  expected=mode==14?PLS_RESOURCE:mode==15?PLS_ARGUMENT:PLS_QUEUE_BASE+PLQ_BUSY;
 }
 CHECK(phone_log_queue_inspect(&before)==PLQ_OK);
 if(mode==12)input=(const unsigned char *)(unsigned)0xfffc;
 status=phone_log_startup_configure(input,
     mode==10||mode==15?1263:sizeof(image),mode==0||mode==1?0:psp);
 CHECK(status==expected&&memcmp(image,saved,sizeof(image))==0);
 CHECK(phone_log_queue_inspect(&after)==PLQ_OK);
 if(expected)CHECK(memcmp(&before,&after,sizeof(before))==0);
 else CHECK(after.enabled==!!flag&&!after.active&&!after.queued);
 if(mode==5)CHECK(_dos_setfileattr("PCPLUS.FON",0)==0);
 if(mode==0){CHECK(phone_log_queue_start(1,"IGNORED","5550100",&start)==PLQ_DISABLED);}
 else if(!expected||active_case){
  if(!active_case){
   if(mode==2)CHECK(capture_fs_canonical("ENV\\PCPLUS.FON",selected)==0);
   else strcpy(selected,original);
   if(mode==2||mode==4)CHECK(access(selected,0)!=0);
   CHECK(phone_log_queue_inspect(&after)==PLQ_OK&&!after.queued);
  }
  CHECK(chdir("AFTER")==0);
  if(!active_case)CHECK(phone_log_queue_start(1,"LoC LAB","5550100",&start)==PLQ_OK);
  CHECK(phone_log_queue_end(1,&end)==PLQ_OK);
  CHECK(phone_log_queue_poll()==PLQ_OK&&phone_log_queue_poll()==PLQ_OK);
  CHECK(phone_log_queue_inspect(&after)==PLQ_OK&&!after.queued&&!after.active&&after.committed_events==2);
  CHECK(access("PCPLUS.FON",0)!=0&&access(selected,0)==0);
  CHECK(chdir("..")==0);
 }
 for(i=0;i<20;++i)CHECK(jft[i]==actual_jft[i]);
 words[0]=mode;words[1]=status;words[2]=after.enabled;words[3]=checks;
 {FILE *f=fopen("STATE.BIN","wb");CHECK(f!=0);CHECK(fwrite(words,sizeof(words),1,f)==1);CHECK(fclose(f)==0);}
 printf("STARTUP %u checks 0 failures\n",checks);return 0;
}
