/* Filesystem-boundary model; compile the actual policy source unchanged. */
#define PHONE_LOG_HOST
#define __cdecl
#include "../src/directory/phone_log_file.c"
#undef cookie
#undef busy
#undef held
#include <stdio.h>
#include <stdlib.h>

static struct {
 unsigned steps,fail1,fail2,short_at,prefix,attributes,exists,opened,closes;
 unsigned close_consumes,reenter,canonical_bad,trace[32];
 unsigned long length,position,virtual_end;
 unsigned char data[1024];
} disk;
static unsigned checks,cases;
static const char head[]="HEAD\r\n",line[]="EVENT\r\n";
#define CHECK(c) do{++checks;if(!(c)){fprintf(stderr,"FAIL line %d case %u steps %u\n",__LINE__,cases,disk.steps);exit(1);}}while(0)
static unsigned step(unsigned operation)
{
 unsigned fail;
 CHECK(disk.steps<32);disk.trace[disk.steps++]=operation;
 if(disk.reenter){
  phone_log_file_snapshot saved=phone_log_file_result;
  CHECK(phone_log_file_append("OTHER.FON",0,0,line,7)==PLF_BUSY);
  CHECK(phone_log_file_initialize()==PLF_BUSY);
  CHECK(memcmp(&saved,&phone_log_file_result,sizeof(saved))==0);
 }
 fail=disk.steps==disk.fail1||disk.steps==disk.fail2;
 return fail?5:0;
}
unsigned capture_fs_canonical(const char *path,char *absolute)
{
 unsigned error=step(1);CHECK(strcmp(path,"CALLS.FON")==0);
 if(!error){
  if(disk.canonical_bad==1)memset(absolute,'X',128);
  else strcpy(absolute,disk.canonical_bad==2?"CALLS.FON":"C:\\CALLS.FON");
 }
 return error;
}
unsigned capture_fs_attributes(const char *path,unsigned *attributes)
{unsigned error=step(2);CHECK(strcmp(path,"C:\\CALLS.FON")==0);*attributes=disk.attributes;return error?error:disk.exists?0:2;}
static unsigned opened(unsigned creating,int *handle)
{
 unsigned error=step(3);if(error)return error;
 CHECK(!disk.opened);CHECK(creating?!disk.exists:disk.exists);
 disk.exists=1;disk.opened=1;*handle=11;return 0;
}
unsigned capture_fs_create(const char *path,int *handle)
{CHECK(strcmp(path,"C:\\CALLS.FON")==0);return opened(1,handle);}
unsigned capture_fs_open_append(const char *path,int *handle)
{CHECK(strcmp(path,"C:\\CALLS.FON")==0);return opened(0,handle);}
unsigned capture_fs_seek_end(int handle,unsigned long *position)
{
 unsigned error=step(4);CHECK(handle==11&&disk.opened);
 if(!error){disk.position=disk.virtual_end?disk.virtual_end:disk.length;*position=disk.position;}return error;
}
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{
 unsigned error=step(5),amount=count;CHECK(handle==11&&disk.opened&&count);
 if(error||disk.steps==disk.short_at)amount=disk.prefix;
 CHECK(amount<=count&&disk.position+amount<=sizeof(disk.data));
 memcpy(disk.data+disk.position,data,amount);disk.position+=amount;
 if(disk.length<disk.position)disk.length=disk.position;
 *written=amount;return error;
}
unsigned phone_log_fs_seek(int handle,unsigned long position)
{unsigned error=step(6);CHECK(handle==11&&disk.opened);if(!error)disk.position=position;return error;}
unsigned phone_log_fs_truncate(int handle)
{unsigned error=step(7);CHECK(handle==11&&disk.opened);if(!error)disk.length=disk.position;return error;}
unsigned phone_log_fs_commit(int handle)
{unsigned error=step(8);CHECK(handle==11&&disk.opened);return error;}
unsigned capture_fs_close(int handle)
{
 unsigned error=step(9);CHECK(handle==11&&disk.opened);++disk.closes;
 if(!error||disk.close_consumes)disk.opened=0;return error;
}
static void setup(unsigned existing,unsigned empty)
{
 memset(&disk,0,sizeof(disk));disk.exists=existing;disk.reenter=1;
 if(existing&&!empty){disk.length=8;memcpy(disk.data,"ORIGINAL",8);}
 memset(&phone_log_file_result,0xa5,sizeof(phone_log_file_result));
 owner.cookie=0x504c;owner.busy=0;owner.handle=-1;
 CHECK(phone_log_file_initialize()==PLF_OK);
 CHECK(phone_log_file_result.state==PLF_IDLE);
 ++cases;
}
static unsigned append(void)
{return phone_log_file_append("calls.fon",head,6,line,7);}
static void prefix(unsigned n)
{CHECK(disk.length>=n);if(n)CHECK(memcmp(disk.data,"ORIGINAL",n)==0);}
static void locked(void)
{
 unsigned before=disk.steps;phone_log_file_snapshot saved=phone_log_file_result;
 CHECK(phone_log_file_result.recovery_required&&phone_log_file_result.state==PLF_UNCERTAIN);
 CHECK(phone_log_file_initialize()==PLF_RECOVERY);
 CHECK(append()==PLF_RECOVERY&&disk.steps==before);
 CHECK(memcmp(&saved,&phone_log_file_result,sizeof(saved))==0);
 CHECK(disk.closes==1);
}
int main(void)
{
 unsigned existing,empty,fault,second,consumes,short_count,before,result;
 for(existing=0;existing<2;++existing)for(empty=0;empty<2;++empty){
  unsigned start=existing&&!empty?8:0;
  setup(existing,empty);CHECK(append()==PLF_OK);
  CHECK(phone_log_file_result.committed&&phone_log_file_result.state==PLF_COMPLETE);
  CHECK(phone_log_file_result.created==!existing&&phone_log_file_result.heading_bytes==(start?0:6));
  CHECK(disk.length==start+7+(start?0:6)&&!disk.opened&&disk.closes==1);
  prefix(start);CHECK(memcmp(disk.data+start,start?line:"HEAD\r\nEVENT\r\n",start?7:13)==0);
  before=disk.steps;CHECK(phone_log_file_initialize()==PLF_OK&&disk.steps==before);
  CHECK(phone_log_file_result.committed);
  for(fault=1;fault<=7;++fault)for(consumes=0;consumes<2;++consumes){
   setup(existing,empty);disk.fail1=fault;disk.prefix=3;disk.close_consumes=consumes;
   result=append();CHECK(result!=PLF_OK&&!phone_log_file_result.committed);
   if(fault==7){CHECK(result==PLF_CLOSE);locked();CHECK(disk.length==start+7+(start?0:6));}
   else{
    CHECK(!phone_log_file_result.recovery_required&&!disk.opened);
    CHECK(disk.length==start);prefix(start);
    CHECK(disk.closes==(fault>=4?1:0));
    CHECK(result==(fault<=2?PLF_INSPECT:fault==3?PLF_OPEN:fault==4?PLF_SEEK:fault==5?PLF_WRITE:PLF_COMMIT));
    CHECK(phone_log_file_result.created==(fault>3&&!existing));
   }
  }
  for(short_count=0;short_count<7;++short_count){
   setup(existing,empty);disk.short_at=5;disk.prefix=short_count;
   CHECK(append()==PLF_WRITE&&!phone_log_file_result.dos_error);
   CHECK(disk.length==start&&!phone_log_file_result.recovery_required);prefix(start);
   before=disk.steps;disk.fail1=disk.fail2=disk.short_at=0;
   CHECK(append()==PLF_OK&&disk.steps==before+7);
   CHECK(disk.length==start+7+(start?0:6));
  }
  for(fault=5;fault<=6;++fault)for(second=fault+1;second<=fault+4;++second){
   setup(existing,empty);disk.fail1=fault;disk.fail2=second;disk.prefix=3;
   CHECK(append()==(fault==5?PLF_WRITE:PLF_COMMIT));locked();prefix(start);
   CHECK(phone_log_file_result.rollback_error==5||phone_log_file_result.close_error==5);
  }
 }
 for(fault=0;fault<2;++fault){
  setup(1,0);disk.fail1=4;disk.fail2=5;disk.close_consumes=fault;
  CHECK(append()==PLF_SEEK);locked();prefix(8);
 }
 for(fault=1;fault<=2;++fault){setup(1,0);disk.canonical_bad=fault;CHECK(append()==PLF_INSPECT&&disk.steps==1);}
 for(fault=1;fault<=0x40;fault<<=1){
  setup(1,0);disk.attributes=fault;
  if(fault&0x59)CHECK(append()==PLF_INSPECT&&disk.steps==2);
  else CHECK(append()==PLF_OK);
 }
 for(fault=0;fault<2;++fault){
  setup(1,0);disk.virtual_end=0xffffffffUL-fault;
  CHECK(append()==PLF_OVERFLOW&&disk.steps==5&&!phone_log_file_result.write_calls);
  CHECK(!phone_log_file_result.recovery_required);prefix(8);
 }
 setup(1,0);
 {
  const char *bad[]={"","NUL","con.log","COM1.FON","AUX","C:\\..\\CALL.FON","LONGNAME1.FON","A?.FON","C:\\CALLS.","C:\\\\CALLS.FON","CLOCK$"};
  phone_log_file_snapshot saved=phone_log_file_result;
  for(fault=0;fault<sizeof(bad)/sizeof(bad[0]);++fault)CHECK(phone_log_file_append(bad[fault],0,0,line,7)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",0,0,0,0)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",0,0,line,257)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",head,250,line,7)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",0,0,&phone_log_file_result,7)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",0,0,&owner,7)==PLF_ARGUMENT);
  CHECK(phone_log_file_append("CALLS.FON",0,0,(void *)(UINTPTR_MAX-2),7)==PLF_ARGUMENT);
  CHECK(!disk.steps&&memcmp(&saved,&phone_log_file_result,sizeof(saved))==0);
 }
 setup(0,1);CHECK(phone_log_file_append("CALLS.FON",line,3,line,7)==PLF_OK);
 CHECK(disk.length==10&&memcmp(disk.data,"EVEEVENT\r\n",10)==0);
 {
  unsigned char maximum[256];unsigned i;
  for(i=0;i<sizeof(maximum);++i)maximum[i]=(unsigned char)i;
  setup(0,1);CHECK(phone_log_file_append("CALLS.FON",0,0,maximum,256)==PLF_OK);
  CHECK(disk.length==256&&memcmp(disk.data,maximum,256)==0);
  setup(0,1);CHECK(phone_log_file_append("CALLS.FON",maximum,249,line,7)==PLF_OK);
  CHECK(disk.length==256&&memcmp(disk.data,maximum,249)==0&&memcmp(disk.data+249,line,7)==0);
  setup(1,0);CHECK(phone_log_file_append("CALLS.FON",maximum,249,line,7)==PLF_OK);
  CHECK(disk.length==15&&memcmp(disk.data+8,line,7)==0);
 }
 printf("PASS %u append cases, %u assertions\n",cases,checks);
 return 0;
}
