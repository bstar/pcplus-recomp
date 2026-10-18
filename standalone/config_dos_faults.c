/* Injected DOS-service boundaries test the actual maintained backend's errors. */
#include "prm_dos.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static unsigned mode,opens,closes,live,offset,failures;
static prm_dos_image image,before,loaded;
static prm_dos_result result;
static void reset(unsigned value){mode=value;opens=closes=live=offset=0;}
static void check(int ok,const char *name){printf("%s %s\n",ok ? "PASS" : "FAIL",name);if(!ok)failures++;}
unsigned prm_fault_open(const char *path,unsigned flags,int *handle)
{ (void)path;(void)flags;opens++;if(mode==1)return 2;live++;*handle=7;return 0; }
unsigned prm_fault_creat(const char *path,unsigned attr,int *handle)
{ return prm_fault_open(path,attr,handle); }
unsigned prm_fault_close(int handle)
{ (void)handle;closes++;if(live)live--;return mode==3 || mode==7 ? 6 : 0; }
unsigned prm_fault_read(int handle,void __far *buffer,unsigned size,unsigned *bytes)
{
 unsigned i,count,limit=mode==8 ? 1265 : 1264;
 unsigned char __far *out=(unsigned char __far *)buffer;
 (void)handle;*bytes=0;
 if(mode==2 || mode==7)return 5;
 count=limit-offset;if(count>size)count=size;if(mode==6 && count>13)count=13;
 for(i=0;i<count;i++)out[i]=(unsigned char)((offset+i)*17U+3U);
 offset+=count;*bytes=count;return 0;
}
unsigned prm_fault_write(int handle,const void __far *buffer,unsigned size,unsigned *bytes)
{
 const unsigned char __far *in=(const unsigned char __far *)buffer;
 unsigned i;(void)handle;*bytes=0;
 for(i=0;i<size;i++)if(in[i]!=(unsigned char)(i*17U+3U))return 13;
 if(mode==4)return 5;
 *bytes=mode==5 ? 17 : size;return 0;
}
int main(void)
{
 unsigned i;
 for(i=0;i<1264;i++)image.bytes[i]=(unsigned char)(i*17U+3U);
 memset(&before,0xa5,sizeof(before));loaded=before;
 reset(1);check(prm_dos_load("X",&loaded,&result)==PRM_DOS_OPEN && result.dos_error==2 && !closes && !live,"open failure has no handle to close");
 reset(2);check(prm_dos_load("X",&loaded,&result)==PRM_DOS_READ && result.dos_error==5 && closes==1 && !live && !memcmp(&loaded,&before,sizeof(before)),"read error closes and leaves destination unchanged");
 reset(3);check(prm_dos_load("X",&loaded,&result)==PRM_DOS_CLOSE && result.close_error==6 && closes==1 && !live && !memcmp(&loaded,&before,sizeof(before)),"read close error prevents destination commit");
 reset(7);check(prm_dos_load("X",&loaded,&result)==PRM_DOS_READ && result.dos_error==5 && result.close_error==6 && closes==1,"primary read and secondary close errors both retained");
 reset(8);check(prm_dos_load("X",&loaded,&result)==PRM_DOS_SIZE && result.bytes_processed==1265 && closes==1 && !memcmp(&loaded,&before,sizeof(before)),"oversized probe leaves destination unchanged");
 reset(6);check(prm_dos_load("X",&loaded,&result)==PRM_DOS_OK && closes==1 && !live && !memcmp(&loaded,&image,sizeof(image)),"fragmented reads assemble exact opaque image");
 reset(4);check(prm_dos_save("X",&image,&result)==PRM_DOS_WRITE && result.dos_error==5 && closes==1 && !live,"write error closes handle");
 reset(5);check(prm_dos_save("X",&image,&result)==PRM_DOS_WRITE && result.bytes_processed==17 && !result.dos_error && closes==1 && !live,"short successful write reported as failure");
 reset(3);check(prm_dos_save("X",&image,&result)==PRM_DOS_CLOSE && result.close_error==6 && closes==1 && !live,"save close error propagated");
 reset(0);check(prm_dos_save("X",&image,&result)==PRM_DOS_OK && result.bytes_processed==1264 && closes==1 && !live,"successful save preserves exact bytes");
 return failures ? 1 : 0;
}
