#include "upload_file.h"
#include <string.h>
static unsigned char buffer[10240];
#define CHECK(x) do{if(!(x))return __LINE__;}while(0)
int main(void)
{
 unsigned n,i;unsigned long offset=0;upload_file_result before;
 CHECK(upload_source_initialize()==UF_OK);
 before=upload_source_result;
 CHECK(upload_source_begin("NUL.TXT")==UF_ARGUMENT);
 CHECK(!memcmp(&before,&upload_source_result,sizeof(before)));
 CHECK(upload_source_begin("SAMPLE.BIN")==UF_OK);
 CHECK(upload_source_result.size==70013UL && upload_source_result.consumed==0);
 CHECK(upload_source_open("sample.bin","r")==1);
 CHECK(upload_source_close(1)==0 && upload_source_close(1)==0);
 CHECK(upload_source_result.handle_open && !upload_source_result.close_calls);
 CHECK(upload_source_open("SAMPLE.BIN","rb")==2);
 while((n=upload_source_read(buffer,1,sizeof(buffer),2))!=0){
  CHECK(n!=0xffff);
  for(i=0;i<n;++i)CHECK(buffer[i]==(unsigned char)((offset+i)*37UL+13));
  offset+=n;
 }
 CHECK(offset==70013UL && upload_source_result.consumed==offset);
 CHECK(upload_source_close(2)==0 && upload_source_close(2)==0);
 CHECK(upload_source_result.close_calls==1 && !upload_source_result.handle_open);
 CHECK(upload_source_finish()==UF_OK && upload_source_finish()==UF_OK);
 CHECK(upload_source_result.state==UF_COMPLETE && !upload_source_result.first_status);
 CHECK(upload_source_initialize()==UF_OK);
 CHECK(upload_source_begin("EMPTY.BIN")==UF_OK);
 CHECK(upload_source_result.size==0);
 CHECK(upload_source_open("EMPTY.BIN","r")==1 && upload_source_close(1)==0);
 CHECK(upload_source_open("EMPTY.BIN","rb")==2);
 CHECK(upload_source_read(buffer,1,sizeof(buffer),2)==0);
 CHECK(upload_source_finish()==UF_OK && upload_source_result.close_calls==1);
 CHECK(upload_source_begin("SUBDIR")==UF_ARGUMENT);
 CHECK(!upload_source_result.handle_open);
 CHECK(upload_source_begin("MISSING.BIN")==UF_INSPECT);
 CHECK(upload_source_initialize()==UF_OK);
 CHECK(upload_source_begin("SAMPLE.BIN")==UF_OK);
 CHECK(upload_source_initialize()==UF_BUSY);
 CHECK(upload_source_open("SAMPLE.BIN","r")==1 && upload_source_close(1)==0);
 CHECK(upload_source_open("SAMPLE.BIN","rb")==2);
 CHECK(upload_source_read(buffer,1,16,2)==16);
 CHECK(upload_source_close(2)==0xffff && upload_source_result.first_status==UF_INCOMPLETE);
 CHECK(upload_source_close(2)==0xffff && upload_source_result.close_calls==1);
 CHECK(upload_source_finish()==UF_INCOMPLETE);
 CHECK(upload_source_abort()==UF_OK && upload_source_result.close_calls==1);
 return 0;
}
