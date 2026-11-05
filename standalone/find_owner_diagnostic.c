#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "../src/filesystem/find_owner.h"
extern void __cdecl find_probe_get(unsigned *);
extern void __cdecl find_probe_set(void __far *);
extern unsigned __cdecl find_probe_first(const char *);
extern unsigned __cdecl find_probe_next(void);
static unsigned checks,failures;
#define CHECK(x) do{checks++;if(!(x)){failures++;printf("FAIL %u line %u\n",checks,__LINE__);}}while(0)
int main(void)
{
 unsigned old[2],current[2],foreign_address[2],i,r,count;
 unsigned char foreign[43],saved[43];
 file_find_entry entry,sentinel;
 char too_long[65];
 find_probe_get(old);
 memset(foreign,0xa5,sizeof(foreign));
 find_probe_set((void __far *)foreign);
 find_probe_get(foreign_address);
 CHECK(foreign_address[0]==FP_OFF((void __far *)foreign));
 CHECK(foreign_address[1]==FP_SEG((void __far *)foreign));
 CHECK(find_probe_first("FOREIGN\\F*.TXT")==0);
 CHECK(!strcmp((char *)foreign+30,"F00.TXT"));
 memcpy(saved,foreign,sizeof(saved));
 memset(&sentinel,0xa5,sizeof(sentinel));entry=sentinel;
 CHECK(file_find_next(&entry)==FILE_FIND_INACTIVE);
 CHECK(!memcmp(&entry,&sentinel,sizeof(entry)));
 CHECK(file_find_begin(0,0,&entry)==FILE_FIND_ARGUMENT);
 memset(too_long,'X',64);too_long[64]=0;
 CHECK(file_find_begin(too_long,0,&entry)==FILE_FIND_ARGUMENT);
 CHECK(file_find_begin("",0,&entry)==FILE_FIND_ARGUMENT);
 CHECK(file_find_begin("FILES\\*.TXT",256,&entry)==FILE_FIND_ARGUMENT);
 CHECK(!memcmp(&entry,&sentinel,sizeof(entry)));
 r=file_find_begin("FILES\\*.TXT",0x10,&entry);count=0;
 while(!r) {
  CHECK(strlen(entry.name)>0&&strlen(entry.name)<=12);
  CHECK(entry.attributes!=0x10);
  CHECK(entry.size==count+1);
  CHECK(entry.date==(unsigned)(((1993-1980)<<9)|(7<<5)|9));
  CHECK(entry.time==(unsigned)((14<<11)|(32<<5)|5));
  CHECK(file_find_begin("FOREIGN\\*.TXT",0,&entry)==FILE_FIND_BUSY);
  find_probe_get(current);
  CHECK(!memcmp(current,foreign_address,sizeof(current)));
  CHECK(!memcmp(foreign,saved,sizeof(saved)));
  count++;r=file_find_next(&entry);
 }
 CHECK(count==3&&r==FILE_FIND_END);
 entry=sentinel;
 CHECK(file_find_next(&entry)==FILE_FIND_END);
 CHECK(!memcmp(&entry,&sentinel,sizeof(entry)));
 file_find_close();
 CHECK(find_probe_next()==0);
 CHECK(!strcmp((char *)foreign+30,"F01.TXT"));
 memcpy(saved,foreign,sizeof(saved));
 entry=sentinel;
 r=file_find_begin("ABSENT\\*.TXT",0,&entry);
 CHECK(r==3);
 CHECK(!memcmp(&entry,&sentinel,sizeof(entry)));
 CHECK(file_find_next(&entry)==r);
 find_probe_get(current);
 CHECK(!memcmp(current,foreign_address,sizeof(current)));
 CHECK(!memcmp(foreign,saved,sizeof(saved)));
 file_find_close();
 r=file_find_begin("FILES\\MISSING.X",0,&entry);
 CHECK(r==2||r==FILE_FIND_END);
 CHECK(!memcmp(&entry,&sentinel,sizeof(entry)));
 file_find_close();
 CHECK(file_find_begin("FILES\\SUB",0x10,&entry)==0);
 CHECK(!strcmp(entry.name,"SUB")&&entry.attributes==0x10);
 file_find_close();
 CHECK(file_find_next(&entry)==FILE_FIND_INACTIVE);
 for(i=0;i<100;i++) {
  CHECK(file_find_begin("FILES\\F00.TXT",0,&entry)==0);
  CHECK(!strcmp(entry.name,"F00.TXT")&&entry.size==1);
  file_find_close();
 }
 find_probe_get(current);
 CHECK(!memcmp(current,foreign_address,sizeof(current)));
 CHECK(!memcmp(foreign,saved,sizeof(saved)));
 find_probe_set(MK_FP(old[1],old[0]));
 find_probe_get(current);CHECK(!memcmp(current,old,sizeof(current)));
 printf("FIND checks=%u failures=%u\n",checks,failures);
 return failures?1:0;
}
