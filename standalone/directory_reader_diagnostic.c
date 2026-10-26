/* Real DOS files; faults are injected around the actual production FS layer.
 * Each mode is a fresh process on synthetic owned media. */
#include "../src/directory/directory_reader.h"
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
unsigned __cdecl directory_reader_real_open(const char *,int *);
unsigned __cdecl directory_reader_real_read(int,void *,unsigned,unsigned *);
unsigned __cdecl directory_reader_real_close(int);
static unsigned mode,checks,opens,reads,closes,max_read,max_operations;
static unsigned char scratch[512],saved_jft[20];
static directory_reader state;
static unsigned char __far *memory;
#define PAGE_SIZE 1394U
#define BLOCK_SIZE (PAGE_SIZE+32U)
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL mode%u line%u status%u phase%u DOS%u close%u\n",mode,__LINE__,state.status,state.phase,state.dos_error,state.close_error);return 1;}}while(0)
unsigned __cdecl directory_reader_fs_open(const char *path,int *handle)
{++opens;return directory_reader_real_open(path,handle);}
unsigned __cdecl directory_reader_fs_read(int handle,void *data,unsigned n,unsigned *count)
{
 ++reads;if(n>max_read)max_read=n;
 if((mode==7||mode==13||mode==15)&&reads==3)return 5;
 if(mode==19){*count=n+1;return 0;}
 if(mode==18&&reads==2){*count=0;return 0;}
 if(mode==3&&n>17)n=17;
 if(mode==16&&n>511)n=511;
 return directory_reader_real_read(handle,data,n,count);
}
unsigned __cdecl directory_reader_fs_close(int handle)
{
 unsigned status;++closes;
 if(mode==9)return 6;
 status=directory_reader_real_close(handle);
 if((mode==8||mode==15)&&!status)return 6;
 return status;
}
static unsigned char pattern(unsigned position)
{return (unsigned char)(position*37U+11U);}
static unsigned unchanged(const directory_dos_page_data __far *page)
{
 unsigned i;const unsigned char __far *p=(const unsigned char __far *)page;
 for(i=0;i<PAGE_SIZE;++i)if(p[i]!=0xa5)return 0;
 return 1;
}
static unsigned guards(void)
{
 unsigned i;
 for(i=0;i<16;++i)if(memory[i]!=0x6c || memory[16+PAGE_SIZE+i]!=0x6c ||
  memory[BLOCK_SIZE+i]!=0x6c || memory[BLOCK_SIZE+16+PAGE_SIZE+i]!=0x6c)return 0;
 return 1;
}
static unsigned page_matches(const directory_dos_page_data __far *page,unsigned first)
{
 unsigned i,count=201-first,start=250+(first-1)*114;
 const unsigned char __far *records=(const unsigned char __far *)page->records;
 if(count>10)count=10;
 if(page->first_entry!=first || page->count!=count)return 0;
 for(i=0;i<250;++i)if(page->header[i]!=pattern(i))return 0;
 for(i=0;i<1140;++i)if(records[i]!=(i<count*114?pattern(start+i):0))return 0;
 return 1;
}
int main(int argc,char **argv)
{
 unsigned segment,i,first=1,status,before,previous,steps=0,expected=0;
 unsigned words[14],phase,held,count;int other;
 unsigned char __far *jft;directory_dos_page_data __far *stage;
 directory_dos_page_data __far *page;
 directory_reader saved;char long_path[128];FILE *file;union REGS regs;
 if(argc!=2)return 1;mode=(unsigned)atoi(argv[1]);if(mode>21)return 1;
 CHECK(_dos_allocmem((2*BLOCK_SIZE+15)/16,&segment)==0);
 memory=(unsigned char __far *)MK_FP(segment,0);
 for(i=0;i<2*BLOCK_SIZE;++i)memory[i]=0x6c;
 stage=(directory_dos_page_data __far *)(memory+16);
 page=(directory_dos_page_data __far *)(memory+BLOCK_SIZE+16);
 for(i=0;i<PAGE_SIZE;++i)((unsigned char __far *)page)[i]=0xa5;
 regs.h.ah=0x62;intdos(&regs,&regs);jft=(unsigned char __far *)MK_FP(regs.x.bx,0x18);
 for(i=0;i<20;++i)saved_jft[i]=jft[i];
 CHECK(directory_reader_initialize(&state)==0);
 CHECK(directory_reader_step(&state)==DIRECTORY_DOS_ARGUMENT);
 if(mode==1)first=191;if(mode==2)first=200;
 if(mode==14){
  saved=state;memset(long_path,'A',sizeof(long_path));
  CHECK(directory_reader_begin(&state,"FILE.DIR",0,stage,page,scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,"FILE.DIR",201,stage,page,scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,"",1,stage,page,scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,long_path,1,stage,page,scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,"FILE.DIR",1,page,page,scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,"FILE.DIR",1,stage,(directory_dos_page_data __far *)MK_FP(segment+1,0),scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,"FILE.DIR",1,stage,(directory_dos_page_data __far *)&state,scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,"FILE.DIR",1,stage,(directory_dos_page_data __far *)MK_FP(segment,65530),scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,"FILE.DIR",1,stage,(directory_dos_page_data __far *)MK_FP(0xffff,16),scratch)==DIRECTORY_DOS_ARGUMENT);
  CHECK(directory_reader_begin(&state,"FILE.DIR",1,stage,page,(unsigned char *)65530)==DIRECTORY_DOS_ARGUMENT);
  CHECK(!opens&&!reads&&!closes&&memcmp(&saved,&state,sizeof(state))==0&&unchanged(page));
  goto finished;
 }
 status=directory_reader_begin(&state,"FILE.DIR",first,stage,page,scratch);
 CHECK(unchanged(page));
 if(mode==6){CHECK(status==DIRECTORY_DOS_OPEN&&state.dos_error==2&&!state.handle_open);goto finished;}
 CHECK(status==DIRECTORY_READER_PENDING&&opens==1&&!reads&&!closes);
 saved=state;
 CHECK(directory_reader_begin(&state,"FILE.DIR",first,stage,page,scratch)==DIRECTORY_READER_BUSY);
 CHECK(directory_reader_initialize(&state)==DIRECTORY_READER_BUSY);
 CHECK(memcmp(&state,&saved,sizeof(state))==0&&opens==1);
 if(mode==10)CHECK(directory_reader_cancel(&state)==DIRECTORY_READER_PENDING);
 while(status==DIRECTORY_READER_PENDING){
  CHECK(++steps<1600);before=opens+reads+closes;previous=state.bytes_processed;
  phase=state.phase;
  status=directory_reader_step(&state);
  count=opens+reads+closes-before;if(count>max_operations)max_operations=count;
  CHECK(count<=1&&state.bytes_processed-previous<=512&&guards());
  if(status!=0)CHECK(unchanged(page));
  if(mode==11&&reads==2&&state.phase==DIRECTORY_READER_READ)
   CHECK(directory_reader_cancel(&state)==DIRECTORY_READER_PENDING);
  if(mode==12&&state.phase==DIRECTORY_READER_PROBE)
   CHECK(directory_reader_cancel(&state)==DIRECTORY_READER_PENDING);
  if(mode==13&&state.status==DIRECTORY_DOS_READ&&phase==DIRECTORY_READER_READ)
   CHECK(directory_reader_cancel(&state)==DIRECTORY_READER_PENDING);
  if(mode==20&&state.phase==DIRECTORY_READER_CLOSE&&!state.status)
   CHECK(directory_reader_cancel(&state)==DIRECTORY_READER_PENDING);
 }
 if(mode==4||mode==5||mode==17||mode==18)expected=DIRECTORY_DOS_SIZE;
 if(mode==7||mode==13||mode==15||mode==19)expected=DIRECTORY_DOS_READ;
 if(mode==8||mode==9)expected=DIRECTORY_DOS_CLOSE;
 if(mode==10||mode==11||mode==12||mode==20)expected=DIRECTORY_READER_CANCELLED;
 CHECK(status==expected&&state.status==expected&&closes==1&&max_read<=512);
 if(!status){CHECK(page_matches(page,first));CHECK(state.bytes_processed==23050);}
 else CHECK(unchanged(page));
 if(mode==15)CHECK(state.dos_error==5&&state.close_error==6);
 before=opens+reads+closes;
 CHECK(directory_reader_step(&state)==status);
 CHECK(directory_reader_cancel(&state)==status);
 CHECK(opens+reads+closes==before);
 if(state.close_error){
  CHECK(state.phase==DIRECTORY_READER_RECOVERY&&state.handle_open);
  saved=state;
  CHECK(directory_reader_initialize(&state)==DIRECTORY_READER_BUSY);
  CHECK(directory_reader_begin(&state,"FILE.DIR",first,stage,page,scratch)==DIRECTORY_READER_BUSY);
  CHECK(memcmp(&state,&saved,sizeof(state))==0);
  if(mode==9)CHECK(directory_reader_real_close(state.handle)==0);
  else{
   /* Close reported failure after actually releasing its handle. A new file
    * reuses that number; repeated reader calls must never close it. */
   CHECK(directory_reader_real_open("FILE.DIR",&other)==0&&other==state.handle);
   CHECK(directory_reader_step(&state)==status&&directory_reader_cancel(&state)==status);
   CHECK(directory_reader_real_read(other,scratch,1,&count)==0&&count==1&&scratch[0]==pattern(0));
   CHECK(directory_reader_real_close(other)==0);
  }
 }else CHECK(!state.handle_open&&state.phase==DIRECTORY_READER_DONE);
 if(mode==21){
  CHECK(directory_reader_initialize(&state)==0);
  status=directory_reader_begin(&state,"FILE.DIR",200,stage,page,scratch);
  while(status==DIRECTORY_READER_PENDING)status=directory_reader_step(&state);
  CHECK(status==0&&page_matches(page,200)&&opens==2&&closes==2);
 }
finished:
 held=state.handle_open;
 CHECK(guards());
 for(i=0;i<20;++i)CHECK(jft[i]==saved_jft[i]);
 words[0]=mode;words[1]=state.status;words[2]=state.phase;words[3]=state.dos_error;
 words[4]=state.close_error;words[5]=state.bytes_processed;words[6]=steps;
 words[7]=opens;words[8]=reads;words[9]=closes;words[10]=max_read;
 words[11]=max_operations;words[12]=held;words[13]=checks;
 file=fopen("RESULT.BIN","wb");CHECK(file!=0);
 CHECK(fwrite(words,2,14,file)==14&&fclose(file)==0);
 file=fopen("PAGE.BIN","wb");CHECK(file!=0);
 for(i=0;i<PAGE_SIZE;++i)CHECK(fputc(((unsigned char __far *)page)[i],file)!=EOF);
 CHECK(fclose(file)==0&&_dos_freemem(segment)==0);
 printf("PASS mode%u checks%u steps%u\n",mode,checks,steps);return 0;
}
