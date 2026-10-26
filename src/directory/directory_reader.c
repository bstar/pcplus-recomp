/* Source-owned incremental counterpart to the strict synchronous page reader.
 * No UART, BIOS, heap, original inputs, global buffers or hidden retry loop. */
#include "directory_reader.h"
#include "directory_reader_fs.h"
#include <dos.h>
typedef char reader_word_size[sizeof(unsigned)==2?1:-1];
typedef char reader_page_size[sizeof(directory_dos_page_data)==1394?1:-1];
static unsigned near_extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned long linear(const void __far *p)
{return ((unsigned long)FP_SEG(p)<<4)+FP_OFF(p);}
static unsigned far_extent(const void __far *p,unsigned n)
{return p && (unsigned long)FP_OFF(p)+n<=65536UL && linear(p)+n<=0x100000UL;}
static unsigned separate(const void __far *a,unsigned an,const void __far *b,unsigned bn)
{unsigned long x=linear(a),y=linear(b);return x+an<=y || y+bn<=x;}
static unsigned owner(const directory_reader *r)
{return near_extent(r,sizeof(*r)) && r->magic==DIRECTORY_READER_MAGIC;}
static unsigned available(const directory_reader *r)
{return !r->handle_open && (r->phase==DIRECTORY_READER_IDLE || r->phase==DIRECTORY_READER_DONE);}
unsigned DIRECTORY_READER_CALL directory_reader_initialize(directory_reader *r)
{
 unsigned i;unsigned char *p=(unsigned char *)r;
 if(!near_extent(r,sizeof(*r)))return DIRECTORY_DOS_ARGUMENT;
 if(r->magic==DIRECTORY_READER_MAGIC && !available(r))return DIRECTORY_READER_BUSY;
 for(i=0;i<sizeof(*r);++i)p[i]=0;
 r->magic=DIRECTORY_READER_MAGIC;return 0;
}
unsigned DIRECTORY_READER_CALL directory_reader_begin(directory_reader *r,const char *path,unsigned first,
 directory_dos_page_data __far *stage,directory_dos_page_data __far *destination,
 unsigned char *scratch)
{
 unsigned n,i,j,error;const void __far *p[5];unsigned sizes[5];
 unsigned char __far *bytes=(unsigned char __far *)stage;
 if(!owner(r))return DIRECTORY_DOS_ARGUMENT;
 if(!available(r))return DIRECTORY_READER_BUSY;
 if(first<1 || first>200 || !path || !near_extent(scratch,DIRECTORY_READER_CHUNK) ||
  !far_extent(stage,sizeof(*stage)) || !far_extent(destination,sizeof(*destination)))return DIRECTORY_DOS_ARGUMENT;
 for(n=0;n<=DIRECTORY_DOS_PATH_MAX;++n){
  if(!near_extent(path,n+1))return DIRECTORY_DOS_ARGUMENT;
  if(!path[n])break;
 }
 if(!n || n>DIRECTORY_DOS_PATH_MAX)return DIRECTORY_DOS_ARGUMENT;
 p[0]=(const void __far *)r;sizes[0]=sizeof(*r);
 p[1]=(const void __far *)path;sizes[1]=n+1;
 p[2]=(const void __far *)scratch;sizes[2]=DIRECTORY_READER_CHUNK;
 p[3]=stage;sizes[3]=sizeof(*stage);p[4]=destination;sizes[4]=sizeof(*destination);
 for(i=0;i<5;++i)for(j=0;j<i;++j)
  if(!separate(p[i],sizes[i],p[j],sizes[j]))return DIRECTORY_DOS_ARGUMENT;
 r->status=r->dos_error=r->close_error=r->bytes_processed=0;
 r->first_entry=first;r->count=201-first;if(r->count>10)r->count=10;
 r->stage=stage;r->destination=destination;r->scratch=scratch;
 error=directory_reader_fs_open(path,&r->handle);
 if(error){r->status=DIRECTORY_DOS_OPEN;r->dos_error=error;r->phase=DIRECTORY_READER_DONE;return r->status;}
 r->handle_open=1;r->phase=DIRECTORY_READER_READ;
 for(i=0;i<sizeof(*stage);++i)bytes[i]=0;
 stage->first_entry=first;stage->count=r->count;
 return DIRECTORY_READER_PENDING;
}
static void failed(directory_reader *r,unsigned status,unsigned error)
{if(!r->status){r->status=status;r->dos_error=error;}r->phase=DIRECTORY_READER_CLOSE;}
unsigned DIRECTORY_READER_CALL directory_reader_step(directory_reader *r)
{
 unsigned n,count=0,error,i,position,start,end;
 unsigned char __far *to;
 if(!owner(r))return DIRECTORY_DOS_ARGUMENT;
 if(r->phase==DIRECTORY_READER_DONE || r->phase==DIRECTORY_READER_RECOVERY)return r->status;
 if(r->phase==DIRECTORY_READER_IDLE)return DIRECTORY_DOS_ARGUMENT;
 if(!r->handle_open)return DIRECTORY_READER_BUSY;
 if(r->phase==DIRECTORY_READER_CLOSE){
  error=directory_reader_fs_close(r->handle);r->close_error=error;
  if(error){
   if(!r->status){r->status=DIRECTORY_DOS_CLOSE;r->dos_error=error;}
   r->phase=DIRECTORY_READER_RECOVERY;return r->status;
  }
  r->handle_open=0;r->phase=DIRECTORY_READER_DONE;
  if(!r->status){to=(unsigned char __far *)r->destination;
   for(i=0;i<sizeof(*r->stage);++i)to[i]=((unsigned char __far *)r->stage)[i];}
  return r->status;
 }
 n=r->phase==DIRECTORY_READER_PROBE?1:DIRECTORY_DOS_FILE_SIZE-r->bytes_processed;
 if(n>DIRECTORY_READER_CHUNK)n=DIRECTORY_READER_CHUNK;
 error=directory_reader_fs_read(r->handle,r->scratch,n,&count);
 if(error){failed(r,DIRECTORY_DOS_READ,error);return DIRECTORY_READER_PENDING;}
 if(count>n){failed(r,DIRECTORY_DOS_READ,0);return DIRECTORY_READER_PENDING;}
 if(r->phase==DIRECTORY_READER_PROBE){
  r->bytes_processed+=count;
  if(count)failed(r,DIRECTORY_DOS_SIZE,0);else r->phase=DIRECTORY_READER_CLOSE;
  return DIRECTORY_READER_PENDING;
 }
 if(!count){failed(r,DIRECTORY_DOS_SIZE,0);return DIRECTORY_READER_PENDING;}
 start=DIRECTORY_DOS_HEADER_SIZE+(r->first_entry-1)*DIRECTORY_DOS_RECORD_SIZE;
 end=start+r->count*DIRECTORY_DOS_RECORD_SIZE;
 for(i=0;i<count;++i){position=r->bytes_processed+i;
  if(position<DIRECTORY_DOS_HEADER_SIZE)r->stage->header[position]=r->scratch[i];
  else if(position>=start && position<end)
   ((unsigned char __far *)r->stage->records)[position-start]=r->scratch[i];
 }
 r->bytes_processed+=count;
 if(r->bytes_processed==DIRECTORY_DOS_FILE_SIZE)r->phase=DIRECTORY_READER_PROBE;
 return DIRECTORY_READER_PENDING;
}
unsigned DIRECTORY_READER_CALL directory_reader_cancel(directory_reader *r)
{
 if(!owner(r))return DIRECTORY_DOS_ARGUMENT;
 if(r->phase==DIRECTORY_READER_DONE || r->phase==DIRECTORY_READER_RECOVERY)return r->status;
 if(r->phase==DIRECTORY_READER_IDLE)return DIRECTORY_DOS_ARGUMENT;
 if(!r->handle_open)return DIRECTORY_READER_BUSY;
 if(!r->status)r->status=DIRECTORY_READER_CANCELLED;
 r->phase=DIRECTORY_READER_CLOSE;return DIRECTORY_READER_PENDING;
}
