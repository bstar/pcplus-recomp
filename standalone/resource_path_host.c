/* Real DOS allocations with synthetic PSP/environment bytes, no private data. */
#include "resource_path.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static unsigned char guarded[66],before[66];
static unsigned char __far *env;
static unsigned psp,environment_segment,checks;
static char name[13]="PCPLUS.XLT";
#define CHECK(x) do { ++checks; if(!(x)){printf("FAIL resource line %u\n",(unsigned)__LINE__);return 1;} } while(0)
static void reset(void)
{unsigned i;memset(guarded,0xa5,66);memcpy(before,guarded,66);for(i=0;i<512;++i)env[i]=0;}
static void entries(const char *value,unsigned n)
{unsigned i;reset();for(i=0;i<n;++i)env[i]=(unsigned char)value[i];}
int main(void)
{
 unsigned i;char directory[80];
 CHECK(!_dos_allocmem(16,&psp));CHECK(!_dos_allocmem(32,&environment_segment));
 env=(unsigned char __far *)MK_FP(environment_segment,0);
 *(unsigned __far *)MK_FP(psp,0x2c)=environment_segment;
 entries("PCPLUS=D:\\CFG\0\0",15);
 CHECK(resource_pcplus_path(psp,name,(char *)guarded+1)==0);
 CHECK(!strcmp((char *)guarded+1,"D:\\CFG\\PCPLUS.XLT") && guarded[0]==0xa5 && guarded[65]==0xa5);
 entries("PCPLUS=D:\\CFG\\\0\0",16);CHECK(!resource_pcplus_path(psp,name,(char *)guarded+1));CHECK(!strcmp((char *)guarded+1,"D:\\CFG\\PCPLUS.XLT"));
 entries("PCPLUS=D:\0\0",11);CHECK(!resource_pcplus_path(psp,name,(char *)guarded+1));CHECK(!strcmp((char *)guarded+1,"D:\\PCPLUS.XLT"));
 entries("PCPLUS=\0PCPLUS=D:\\CFG\0\0",23);CHECK(resource_pcplus_path(psp,name,(char *)guarded+1)==RESOURCE_PATH_ABSENT);CHECK(!memcmp(guarded,before,66));
 entries("pcplus=D:\\CFG\0\0",15);CHECK(resource_pcplus_path(psp,name,(char *)guarded+1)==RESOURCE_PATH_ABSENT);CHECK(!memcmp(guarded,before,66));
 for(i=0;i<512;++i)env[i]='A';CHECK(resource_pcplus_path(psp,name,(char *)guarded+1)==RESOURCE_PATH_ENVIRONMENT);CHECK(!memcmp(guarded,before,66));
 memset(directory,'A',sizeof(directory));memcpy(directory,"PCPLUS=",7);directory[59]=directory[60]=0;
 entries(directory,61);CHECK(!resource_pcplus_path(psp,name,(char *)guarded+1));CHECK(strlen((char *)guarded+1)==63);
 directory[59]='A';directory[61]=0;entries(directory,62);CHECK(resource_pcplus_path(psp,name,(char *)guarded+1)==RESOURCE_PATH_SIZE);CHECK(!memcmp(guarded,before,66));
 entries("PCPLUS=D:\\CFG\0\0",15);
 CHECK(resource_pcplus_path(psp,0,(char *)guarded+1)==RESOURCE_PATH_ARGUMENT);
 CHECK(resource_pcplus_path(psp,"../BAD",(char *)guarded+1)==RESOURCE_PATH_ARGUMENT);
 CHECK(resource_pcplus_path(psp,"BAD..XLT",(char *)guarded+1)==RESOURCE_PATH_ARGUMENT);
 CHECK(resource_pcplus_path(psp,"TOOLONG99.XLT",(char *)guarded+1)==RESOURCE_PATH_ARGUMENT);
 CHECK(resource_pcplus_path(psp,name,0)==RESOURCE_PATH_ARGUMENT);
 CHECK(resource_pcplus_path(psp,name,(char *)65500U)==RESOURCE_PATH_ARGUMENT);
 memcpy(guarded+1,name,sizeof(name));CHECK(resource_pcplus_path(psp,(char *)guarded+1,(char *)guarded+1)==RESOURCE_PATH_ARGUMENT);
 reset();CHECK(resource_pcplus_path(0,name,(char *)guarded+1)==RESOURCE_PATH_ENVIRONMENT);
 CHECK(resource_pcplus_path(65535U,name,(char *)guarded+1)==RESOURCE_PATH_ENVIRONMENT);CHECK(!memcmp(guarded,before,66));
 CHECK(!_dos_freemem(environment_segment));CHECK(!_dos_freemem(psp));
 printf("RESOURCE PATH PASS %u checks\n",checks);return 0;
}
