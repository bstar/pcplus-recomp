#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <direct.h>
#include <malloc.h>
#include "../src/filesystem/viewer_file.h"
#include "../src/capture/capture_file.h"
static unsigned checks,failures,token;
#define CHECK(x) do{checks++;if(!(x)){failures++;printf("FAIL check=%u line=%u\n",checks,__LINE__);}}while(0)
int main(void)
{
 viewer_file_snapshot s,before;unsigned n,i,r,old,drives,attributes;
 unsigned char __far *allocation;unsigned char __far *buffer;char path[64];
 CHECK(viewer_file_inspect(&s)==VF_OK&&s.phase==VF_IDLE&&s.handle==0xffff&&!s.claimed);
 CHECK(viewer_file_close()==VF_OK);
 CHECK(capture_file_initialize()==CF_OK);
 allocation=_fmalloc(288);if(!allocation)return 20;buffer=allocation+16;
 for(i=0;i<288;i++)allocation[i]=0xa5;
 strcpy(path,"D:\\DATA.BIN");CHECK(viewer_file_inspect(&before)==VF_OK);
 CHECK(viewer_file_open(path,0)==VF_ARGUMENT);
 CHECK(viewer_file_open("CON",&token)==VF_ARGUMENT);
 CHECK(viewer_file_open("D:\\*.BIN",&token)==VF_ARGUMENT);
 CHECK(viewer_file_inspect(&s)==VF_OK&&!memcmp(&s,&before,sizeof(s)));
 CHECK(viewer_file_open(path,&token)==VF_OK);
 CHECK(viewer_file_inspect(&s)==VF_OK&&s.phase==VF_OPENED&&s.claimed&&s.handle!=0xffff&&!strcmp(s.path,path)&&!s.position);
 before=s;CHECK(viewer_file_open("D:\\OTHER.BIN",&token)==VF_BUSY);
 CHECK(viewer_file_inspect(&s)==VF_OK&&!memcmp(&s,&before,sizeof(s)));
 CHECK(capture_file_begin("d:data.bin",CF_APPEND)==CF_BUSY);
 CHECK(monitor_file_initialize()==CF_OK&&monitor_file_begin("d:/data.bin",CF_REPLACE)==CF_BUSY);
 n=0xaaaa;CHECK(viewer_file_read(buffer,257,&n)==VF_ARGUMENT&&n==0xaaaa);
 CHECK(viewer_file_seek(0x80000000UL)==VF_ARGUMENT);
 CHECK(viewer_file_inspect(&s)==VF_OK&&!memcmp(&s,&before,sizeof(s)));
 CHECK(viewer_file_read(0,0,&n)==VF_OK&&n==0);
 CHECK(viewer_file_read(buffer,256,&n)==VF_OK&&n==256);
 for(i=0;i<256;i++)CHECK(buffer[i]==(unsigned char)i);
 CHECK(viewer_file_seek(69696UL)==VF_OK);
 CHECK(viewer_file_read(buffer,256,&n)==VF_OK&&n==256);
 for(i=0;i<256;i++)CHECK(buffer[i]==(unsigned char)(69696UL+i));
 CHECK(viewer_file_inspect(&s)==VF_OK&&s.position==69952UL);
 CHECK(viewer_file_seek(65530UL)==VF_OK&&viewer_file_read(buffer,20,&n)==VF_OK&&n==20);
 for(i=0;i<20;i++)CHECK(buffer[i]==(unsigned char)(65530UL+i));
 CHECK(viewer_file_seek(95030UL)==VF_OK&&viewer_file_read(buffer,256,&n)==VF_OK&&n==10);
 CHECK(viewer_file_read(buffer,256,&n)==VF_OK&&n==0);
 CHECK(viewer_file_seek(100000UL)==VF_OK&&viewer_file_read(buffer,1,&n)==VF_OK&&n==0);
 CHECK(viewer_file_close()==VF_OK&&viewer_file_close()==VF_OK);
 CHECK(viewer_file_inspect(&s)==VF_OK&&s.phase==VF_CLOSED&&!s.claimed&&s.handle==0xffff);
 CHECK(viewer_file_read(buffer,1,&n)==VF_STATE);
 CHECK(capture_file_begin(path,CF_APPEND)==CF_OK&&capture_file_cleanup()==CF_OK);
 CHECK(capture_file_begin(path,CF_APPEND)==CF_OK);
 CHECK(viewer_file_open(path,&token)==VF_CLAIM);
 CHECK(viewer_file_inspect(&s)==VF_OK&&s.phase==VF_CLOSED&&!s.claimed&&s.handle==0xffff&&s.claim_error==CF_BUSY);
 CHECK(capture_file_cleanup()==CF_OK);
 CHECK(viewer_file_open("D:\\SUB",&token)==VF_ATTRIBUTES);
 CHECK(viewer_file_close()==VF_ATTRIBUTES);
 r=viewer_file_open("D:\\MISSING.BIN",&token);CHECK(r==VF_ATTRIBUTES||r==VF_CANONICAL);
 CHECK(viewer_file_inspect(&s)==VF_OK&&!s.claimed&&s.handle==0xffff&&s.dos_error==2);
 CHECK(_dos_setfileattr("D:\\READONLY.BIN",_A_RDONLY)==0);
 CHECK(_dos_getfileattr("D:\\READONLY.BIN",&attributes)==0&&(attributes&_A_RDONLY));
 CHECK(viewer_file_open("D:\\READONLY.BIN",&token)==VF_OK);
 CHECK(viewer_file_read(buffer,8,&n)==VF_OK&&n==8&&buffer[0]=='R');
 CHECK(viewer_file_close()==VF_OK);
 _dos_getdrive(&old);_dos_setdrive(4,&drives);CHECK(chdir("\\")==0);
 CHECK(viewer_file_open("DATA.BIN",&token)==VF_OK);
 CHECK(chdir("\\SUB")==0);
 CHECK(viewer_file_read(buffer,1,&n)==VF_OK&&n==1&&buffer[0]==0);
 CHECK(viewer_file_inspect(&s)==VF_OK&&!strcmp(s.path,"D:\\DATA.BIN"));
 CHECK(viewer_file_close()==VF_OK&&chdir("\\")==0);_dos_setdrive(old,&drives);
 for(i=0;i<100;i++){
  CHECK(viewer_file_open(path,&token)==VF_OK);
  CHECK(viewer_file_read(buffer,1,&n)==VF_OK&&n==1&&buffer[0]==0);
  CHECK(viewer_file_close()==VF_OK);
 }
 for(i=0;i<16;i++)CHECK(allocation[i]==0xa5&&allocation[272+i]==0xa5);
 _ffree(allocation);
 printf("VIEWFILE checks=%u failures=%u\n",checks,failures);return failures?1:0;
}
