#include "upload_file.h"
#include "upload_fs.h"
#include <string.h>
static unsigned attributes_error,open_error,seek_error,rewind_error,read_error,close_error;
static unsigned attributes_value,actual_limit,read_oversize,seek_wrong;
static unsigned opens,reads,closes,seeks,rewinds;
static unsigned long declared,position;
static unsigned char buffer[10240];
#define CHECK(x) do{if(!(x))return __LINE__;}while(0)
unsigned upload_fs_attributes(const char *p,unsigned *a){(void)p;*a=attributes_value;return attributes_error;}
unsigned upload_fs_open(const char *p,int *h){(void)p;++opens;*h=37;position=0;return open_error;}
unsigned upload_fs_seek_end(int h,unsigned long *n){(void)h;++seeks;*n=declared;position=declared;return seek_error;}
unsigned upload_fs_rewind(int h){(void)h;++rewinds;position=0;return rewind_error;}
unsigned upload_fs_seek(int h,unsigned long offset,unsigned long *actual)
{(void)h;++seeks;*actual=offset+seek_wrong;if(!seek_error)position=*actual;return seek_error;}
unsigned upload_fs_read(int h,void *data,unsigned n,unsigned *actual)
{
 unsigned i;(void)h;++reads;
 *actual=read_oversize ? n+1:actual_limit<n ? actual_limit:n;
 if(!read_oversize)for(i=0;i<*actual;++i)((unsigned char*)data)[i]=(unsigned char)((position+i)*37UL+13);
 position+=*actual;return read_error;
}
unsigned upload_fs_close(int h){(void)h;++closes;return close_error;}
static unsigned reset(void)
{
 if(upload_source_result.handle_uncertain)return UF_RECOVERY;
 if(upload_source_result.handle_open)upload_source_abort();
 attributes_error=open_error=seek_error=rewind_error=read_error=close_error=0;
 attributes_value=read_oversize=seek_wrong=0;actual_limit=10240;opens=reads=closes=seeks=rewinds=0;declared=200;
 return upload_source_initialize();
}
static unsigned ready(void)
{
 if(upload_source_begin("C:/FILES/SOURCE.BIN"))return 1;
 if(strcmp(upload_source_result.path,"C:\\FILES\\SOURCE.BIN"))return 2;
 if(upload_source_open("c:\\files\\source.bin","r")!=1)return 3;
 if(upload_source_close(1) || upload_source_close(1) || closes)return 4;
 if(upload_source_open("C:/FILES/SOURCE.BIN","rb")!=2)return 5;
 return 0;
}
int main(int argc,char **argv)
{
 unsigned i,error,kind=argc>1 ? (unsigned)(argv[1][0]-'0'):0;upload_file_result before;
 if(kind==9){
  CHECK(reset()==UF_OK);CHECK(!ready());close_error=6;
  CHECK(upload_source_abort()==UF_CLOSE);CHECK(closes==1 && upload_source_result.handle_uncertain);
  CHECK(upload_source_abort()==UF_RECOVERY && upload_source_initialize()==UF_RECOVERY && upload_source_begin("OTHER.BIN")==UF_RECOVERY);
  CHECK(upload_source_close(2)==0xffff && closes==1 && upload_source_result.close_error==6);
  return 0;
 }
 CHECK(reset()==UF_OK);before=upload_source_result;
 {const char *bad[]={"","CON","con.txt","C:/DIR/AUX.BIN","COM1.X","LPT9","CLOCK$","A..B","TOOLONGXX.A","FILE.LONG","C:/A/../B","C:/A//B","A B","A?B","C:\\"};
 for(i=0;i<sizeof(bad)/sizeof(bad[0]);++i){CHECK(upload_source_begin(bad[i])==UF_ARGUMENT);CHECK(!memcmp(&before,&upload_source_result,sizeof(before)) && !opens);}}
 for(error=1;error<=8;++error){
  CHECK(reset()==UF_OK);attributes_error=error;CHECK(upload_source_begin("A.BIN")==UF_INSPECT && !opens && !closes);
  CHECK(reset()==UF_OK);open_error=error;CHECK(upload_source_begin("A.BIN")==UF_OPEN && opens==1 && !closes);
  CHECK(reset()==UF_OK);seek_error=error;CHECK(upload_source_begin("A.BIN")==UF_SEEK && closes==1 && !rewinds);
  CHECK(reset()==UF_OK);rewind_error=error;CHECK(upload_source_begin("A.BIN")==UF_SEEK && closes==1 && rewinds==1);
 }
 CHECK(reset()==UF_OK);attributes_value=0x10;CHECK(upload_source_begin("A.BIN")==UF_ARGUMENT && !opens);
 CHECK(reset()==UF_OK);attributes_value=0x08;CHECK(upload_source_begin("A.BIN")==UF_ARGUMENT && !opens);
 CHECK(reset()==UF_OK);CHECK(!ready());before=upload_source_result;
 CHECK(upload_source_begin("OTHER.BIN")==UF_BUSY && !memcmp(&before,&upload_source_result,sizeof(before)) && opens==1);
 CHECK(upload_source_read(buffer,1,200,2)==200 && upload_source_read(buffer,1,200,2)==0 && reads==1);
 CHECK(upload_source_close(2)==0 && upload_source_close(2)==0 && closes==1 && upload_source_finish()==UF_OK);
 CHECK(reset()==UF_OK);CHECK(!ready());before=upload_source_result;i=seeks;
 CHECK(upload_source_seek(201)==UF_ARGUMENT && upload_source_seek(0xffffffffUL)==UF_ARGUMENT);
 CHECK(!memcmp(&before,&upload_source_result,sizeof(before)) && seeks==i);
 CHECK(upload_source_seek(199)==UF_OK && upload_source_read(buffer,1,1,2)==1 && buffer[0]==(unsigned char)(199*37UL+13));
 CHECK(upload_source_seek(0)==UF_OK && upload_source_seek(200)==UF_OK && upload_source_read(buffer,1,1,2)==0);
 CHECK(upload_source_close(2)==0 && closes==1);
 for(error=0;error<=8;++error){
  CHECK(reset()==UF_OK);CHECK(!ready());before=upload_source_result;
  seek_error=error;seek_wrong=error==0;
  CHECK(upload_source_seek(100)==UF_SEEK && upload_source_result.consumed==before.consumed);
  CHECK(upload_source_result.dos_error==error && upload_source_read(buffer,1,1,2)==0xffff);
  CHECK(upload_source_abort()==UF_OK && closes==1);
 }
 for(error=1;error<=8;++error){
  CHECK(reset()==UF_OK);CHECK(!ready());read_error=error;actual_limit=13;
  CHECK(upload_source_read(buffer,1,200,2)==0xffff && upload_source_result.first_status==UF_READ && upload_source_result.consumed==13);
  CHECK(upload_source_finish()==UF_READ && closes==1 && upload_source_abort()==UF_OK && closes==1);
 }
 for(i=0;i<3;++i){
  CHECK(reset()==UF_OK);CHECK(!ready());actual_limit=i ? 199:0;read_oversize=i==2;
  CHECK(upload_source_read(buffer,1,200,2)==0xffff && upload_source_result.first_status==(i==2?UF_READ:UF_SHRINK));
  CHECK(upload_source_finish()!=UF_OK && closes==1);
 }
 for(i=0;i<7;++i){
  CHECK(reset()==UF_OK);CHECK(!ready());
  if(i==0)error=upload_source_read(buffer,2,1,2);
  else if(i==1)error=upload_source_read(buffer,1,10241,2);
  else if(i==2)error=upload_source_read((void*)65530U,1,10,2);
  else if(i==3)error=upload_source_read(&upload_source_result,1,1,2);
  else if(i==4)error=upload_source_read(buffer,1,1,1);
  else if(i==5)error=upload_source_read((void*)0,1,1,2);
  else error=upload_source_read(buffer,1,1,0);
  CHECK(error==0xffff && !reads && upload_source_result.first_status==UF_ARGUMENT);
  CHECK(upload_source_finish()!=UF_OK && closes==1);
 }
 for(i=0;i<4;++i){
  CHECK(reset()==UF_OK);CHECK(!ready());
  if(i==0)error=upload_source_open("OTHER.BIN","rb");
  else if(i==1)error=upload_source_open("C:/FILES/SOURCE.BIN","rt");
  else if(i==2)error=upload_source_open("C:/FILES/SOURCE.BIN","rb");
  else error=upload_source_open((const char*)65535U,"rb");
  CHECK(!error && upload_source_result.first_status && upload_source_finish()!=UF_OK && closes==1);
 }
 CHECK(reset()==UF_OK);CHECK(!ready());CHECK(upload_source_read(buffer,1,200,2)==200);
 CHECK(upload_source_abort()==UF_OK && closes==1 && upload_source_finish()==UF_STATE);
 CHECK(upload_source_close(2)==0xffff && closes==1 && upload_source_finish()!=UF_OK);
 CHECK(reset()==UF_OK);declared=0xfffffff0UL;CHECK(!ready());
 upload_source_result.consumed=0xffffffedUL;position=0xffffffedUL;
 CHECK(upload_source_read(buffer,1,20,2)==3 && upload_source_result.consumed==0xfffffff0UL);
 CHECK(upload_source_read(buffer,1,20,2)==0 && upload_source_finish()==UF_OK);
 return 0;
}
