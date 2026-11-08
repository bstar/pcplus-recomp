/* Actual DOS exact snapshots with bounded injected platform errors. */
#include <dos.h>
#include <io.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include "runtime.h"
#include "buffer_snapshot.h"
extern unsigned _psp;
static unsigned checks,failures,mode,close_calls;
static unsigned char bytes[6][512],jft[20];
static char saved[80];
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL %u mode%u\n",checks,mode);}}
unsigned __watcall snapshot_create(const char *p,unsigned attr,int *h)
{if(mode==1){mode=0;return 5;}return _dos_creatnew(p,attr,h);}
unsigned __watcall snapshot_write(int h,const void __far *p,unsigned n,unsigned *done)
{
 if(mode==2){mode=0;*done=0;return 5;}
 if(mode==3){mode=0;return _dos_write(h,p,n-1,done);}
 return _dos_write(h,p,n,done);
}
unsigned __watcall snapshot_read(int h,void __far *p,unsigned n,unsigned *done)
{
 if(mode==4){mode=0;*done=0;return 5;}
 if(mode==5){mode=0;return _dos_read(h,p,n-1,done);}
 return _dos_read(h,p,n,done);
}
unsigned __watcall snapshot_close(int h)
{
 ++close_calls;
 if(mode==9)return 5;
 if(mode==10){_dos_close(h);return 5;}
 if(mode==6){mode=0;return 5;}
 if(mode==7){unsigned s;mode=0;s=_dos_close(h);return s?s:5;}
 return _dos_close(h);
}
int __watcall snapshot_remove(const char *p)
{if(mode==8){mode=0;return -1;}return remove(p);}
static unsigned same_handles(void)
{unsigned i;for(i=0;i<20;++i)if(jft[i]!=((unsigned char __far *)MK_FP(_psp,0x18))[i])return 0;return 1;}
static void create(unsigned count)
{
 unsigned i;ck(aspect_buffer_snapshot_begin(count)==0);
 strcpy(saved,aspect_buffer_snapshot_path());
 for(i=0;i<count;++i)ck(aspect_buffer_snapshot_save(i,bytes[i])==0);
 ck(aspect_buffer_snapshot_seal()==0);ck(same_handles());
}
static void verify(unsigned count)
{
 unsigned i;for(i=0;i<count;++i)ck(aspect_buffer_snapshot_compare(i,bytes[i])==0);
 ck(aspect_buffer_snapshot_finish()==0);ck(!aspect_buffer_snapshot_active()&&same_handles());
 if(count)ck(access(saved,0)!=0);
}
static void damage(long offset,unsigned char value)
{
 int h=open(saved,O_RDWR|O_BINARY);ck(h>=0);if(h<0)return;
 ck(lseek(h,offset,SEEK_SET)==offset);ck(write(h,&value,1)==1);ck(close(h)==0);
}
int main(int argc,char **argv)
{
 unsigned i,j,n,which;int truncator;FILE *f;unsigned char old;
 for(i=0;i<20;++i)jft[i]=((unsigned char __far *)MK_FP(_psp,0x18))[i];
 for(i=0;i<6;++i)for(j=0;j<512;++j)bytes[i][j]=(unsigned char)(i*73U+j*29U+(j>>3));
 if(argc>1){
  unsigned before;
  ck(aspect_buffer_snapshot_begin(1)==0);ck(aspect_buffer_snapshot_save(0,bytes[0])==0);
  mode=argv[1][0]=='9'?9:10;
  ck(aspect_buffer_snapshot_seal()==ASPECT_RUN_IO&&aspect_buffer_snapshot_active());
  before=close_calls;f=fopen("FOREIGN.BIN","wb");ck(f!=0);if(!f)return 95;
  ck(aspect_buffer_snapshot_discard()==ASPECT_RUN_IO&&close_calls==before);
  ck(aspect_buffer_snapshot_begin(1)==ASPECT_RUN_STATE);
  ck(fputs("SAFE",f)!=EOF&&fflush(f)==0);ck(fclose(f)==0);
  printf("QUARANTINE %u checks %u failures\n",checks,failures);return failures?1:0;
 }
 ck(aspect_buffer_snapshot_save(0,bytes[0])==ASPECT_RUN_STATE);
 ck(aspect_buffer_snapshot_begin(7)==ASPECT_RUN_STATE);
 for(n=0;n<=6;++n){create(n);verify(n);}
 f=fopen("LPS00000.TMP","wb");ck(f!=0);if(!f)return 99;fputs("KEEP",f);ck(fclose(f)==0);
 create(6);ck(strstr(saved,"LPS00001.TMP")!=0);verify(6);
 f=fopen("LPS00000.TMP","rb");ck(f!=0);if(!f)return 98;
 for(i=0;i<4;++i)ck(fgetc(f)=="KEEP"[i]);ck(fgetc(f)==EOF);ck(fclose(f)==0);ck(remove("LPS00000.TMP")==0);
 for(i=0;i<6;++i)for(which=0;which<4;++which){
  unsigned at=which==0?0:which==1?63:which==2?64:511;
  create(6);damage(7L+(long)i*513L+at,bytes[i][at]^1);
  for(j=0;j<i;++j)ck(aspect_buffer_snapshot_compare(j,bytes[j])==0);
  ck(aspect_buffer_snapshot_compare(i,bytes[i])==ASPECT_RUN_STATE);
  ck(aspect_buffer_snapshot_finish()==ASPECT_RUN_STATE);ck(!aspect_buffer_snapshot_active()&&same_handles());
 }
 create(1);old=bytes[0][511];bytes[0][511]^=1;
 ck(aspect_buffer_snapshot_compare(0,bytes[0])==ASPECT_RUN_STATE);bytes[0][511]=old;
 ck(aspect_buffer_snapshot_finish()==ASPECT_RUN_STATE);
 create(1);damage(0,'X');ck(aspect_buffer_snapshot_compare(0,bytes[0])==ASPECT_RUN_STATE);
 ck(aspect_buffer_snapshot_finish()==ASPECT_RUN_STATE);
 create(1);damage(6,5);ck(aspect_buffer_snapshot_compare(0,bytes[0])==ASPECT_RUN_STATE);
 ck(aspect_buffer_snapshot_finish()==ASPECT_RUN_STATE);
 create(1);f=fopen(saved,"ab");ck(f!=0);if(!f)return 97;fputc('X',f);ck(fclose(f)==0);
 ck(aspect_buffer_snapshot_compare(0,bytes[0])==0);ck(aspect_buffer_snapshot_finish()==ASPECT_RUN_IO);
 create(1);truncator=open(saved,O_WRONLY|O_BINARY);ck(truncator>=0);
 if(truncator<0)return 96;ck(chsize(truncator,0)==0);ck(close(truncator)==0);
 ck(aspect_buffer_snapshot_compare(0,bytes[0])==ASPECT_RUN_IO);ck(aspect_buffer_snapshot_finish()==ASPECT_RUN_IO);
 for(i=1;i<=3;++i){mode=i;ck(aspect_buffer_snapshot_begin(1)==ASPECT_RUN_IO);ck(!aspect_buffer_snapshot_active()&&same_handles());}
 for(i=2;i<=3;++i){
  ck(aspect_buffer_snapshot_begin(1)==0);mode=i;ck(aspect_buffer_snapshot_save(0,bytes[0])==ASPECT_RUN_IO);
  ck(aspect_buffer_snapshot_discard()==0&&same_handles());
 }
 for(i=4;i<=5;++i){create(1);mode=i;ck(aspect_buffer_snapshot_compare(0,bytes[0])==ASPECT_RUN_IO);ck(aspect_buffer_snapshot_finish()==ASPECT_RUN_IO&&same_handles());}
 for(i=6;i<=7;++i){
  ck(aspect_buffer_snapshot_begin(1)==0);ck(aspect_buffer_snapshot_save(0,bytes[0])==0);
  mode=i;ck(aspect_buffer_snapshot_seal()==ASPECT_RUN_IO);ck(aspect_buffer_snapshot_discard()==0&&same_handles());
 }
 create(1);ck(aspect_buffer_snapshot_compare(0,bytes[0])==0);mode=8;
 ck(aspect_buffer_snapshot_finish()==ASPECT_RUN_IO&&aspect_buffer_snapshot_active()&&same_handles());
 ck(aspect_buffer_snapshot_begin(1)==ASPECT_RUN_STATE);ck(aspect_buffer_snapshot_discard()==0&&!aspect_buffer_snapshot_active());
 ck(same_handles());printf("SNAPSHOTS %u checks %u failures\n",checks,failures);return failures?1:0;
}
