/* Observable real-file tests; native composition only on8086 DOS. */
#include <stdio.h>
#include <string.h>
#include <limits.h>
#include "file_io.h"

#define FILE_BYTES 72016UL
aspect_file stream_owner;
static unsigned long checks;
static unsigned failures;
static unsigned char bytes[520];
static void ck(unsigned condition)
{
    ++checks;
    if(!condition){++failures;printf("FAIL %lu status=%u\n",checks,stream_owner.status);}
}
static unsigned char pattern(unsigned long position)
{
    return (unsigned char)(position*37UL+(position>>8));
}
static int fixture(void)
{
    FILE *out;
    unsigned i,n;
    unsigned long position=0;
    static unsigned char target[4]={0x80,0x06,0x01,0};
    static unsigned char second_target[4]={0x90,0x06,0x01,0};
    static unsigned char local_a[2]={4,0},local_b[2]={8,0};
    out=fopen("FLOW.DAT","wb");if(!out)return 0;
    while(position<FILE_BYTES){
        n=(unsigned)((FILE_BYTES-position)>256UL?256UL:FILE_BYTES-position);
        for(i=0;i<n;++i)bytes[i]=pattern(position+i);
        if(fwrite(bytes,1,n,out)!=n){fclose(out);return 0;}
        position+=n;
    }
    if(fseek(out,0x20L,SEEK_SET)||fwrite(target,1,4,out)!=4||
       fseek(out,0x10680L,SEEK_SET)||fwrite(local_a,1,2,out)!=2||
       fwrite(second_target,1,4,out)!=4||
       fseek(out,0x10690L,SEEK_SET)||fwrite(local_b,1,2,out)!=2){fclose(out);return 0;}
    return fclose(out)==0;
}
static void basic_file(void)
{
    unsigned i,n;
    long before;
    static long positions[]={0,1,254,255,256,65534L,65535L,65536L,67200L,72015L,72016L,72017L};
    ck(aspect_file_init(&stream_owner)==ASPECT_FILE_OK);
    ck(aspect_file_close(&stream_owner)==ASPECT_FILE_STATE);
    ck(aspect_file_open(&stream_owner,"MISSING.XYZ")==ASPECT_FILE_IO);
    ck(aspect_file_open(&stream_owner,"FLOW.DAT")==ASPECT_FILE_OK);
    ck(aspect_file_open(&stream_owner,"FLOW.DAT")==ASPECT_FILE_STATE);
    ck(aspect_file_tell(&stream_owner)==0);
    ck(aspect_file_read(bytes,1,255,&stream_owner)==255);
    /* Header cursor may subsequently be advanced by native word readers. */
    ck(stream_owner.native.remaining==1);
    ck(aspect_file_tell(&stream_owner)==255);
    ck(aspect_file_seek(&stream_owner,-1L,1)==0);
    ck(aspect_file_tell(&stream_owner)==254);
    ck(aspect_file_read(bytes,1,4,&stream_owner)==4);
    for(i=0;i<4;++i)ck(bytes[i]==pattern(254UL+i));
    for(i=0;i<sizeof(positions)/sizeof(positions[0]);++i){
        ck(aspect_file_seek(&stream_owner,positions[i],0)==0);
        ck(aspect_file_tell(&stream_owner)==positions[i]);
        bytes[0]=0xa5;n=aspect_file_read(bytes,1,1,&stream_owner);
        if(positions[i]<(long)FILE_BYTES){ck(n==1);ck(bytes[0]==(positions[i]==67200L?4:pattern((unsigned long)positions[i])));}
        else{ck(n==0);ck(bytes[0]==0xa5);ck(stream_owner.native.flags&ASPECT_FILE_EOF_FLAG);}
    }
    ck(aspect_file_seek(&stream_owner,100L,0)==0);
    before=aspect_file_tell(&stream_owner);
    ck(aspect_file_seek(&stream_owner,-1L,0)==-1);ck(aspect_file_tell(&stream_owner)==before);
    ck(aspect_file_seek(&stream_owner,0L,2)==-1);ck(aspect_file_tell(&stream_owner)==before);
    ck(aspect_file_seek(&stream_owner,2147483647L,1)==-1);ck(aspect_file_tell(&stream_owner)==before);
#if LONG_MAX > 2147483647L
    ck(aspect_file_seek(&stream_owner,4294967296L,0)==-1);ck(aspect_file_tell(&stream_owner)==before);
#endif
    ck(aspect_file_read(&stream_owner,1,1,&stream_owner)==0);ck(aspect_file_tell(&stream_owner)==before);
    ck(aspect_file_read(bytes,65535U,2,&stream_owner)==0);ck(aspect_file_tell(&stream_owner)==before);
    ck(aspect_file_read(bytes,0,1,&stream_owner)==0);ck(aspect_file_tell(&stream_owner)==before);
    /* Corrupt only the owned descriptor, then recover by an absolute seek. */
    stream_owner.native.remaining=32767;
    ck(aspect_file_read(bytes,1,1,&stream_owner)==0);ck(stream_owner.status==ASPECT_FILE_STATE);
    ck(aspect_file_seek(&stream_owner,before,0)==0);ck(aspect_file_tell(&stream_owner)==before);
    ck(aspect_file_seek(&stream_owner,(long)FILE_BYTES-5L,0)==0);
    memset(bytes,0xa5,8);ck(aspect_file_read(bytes,2,3,&stream_owner)==2);
    for(i=0;i<5;++i)ck(bytes[i]==pattern(FILE_BYTES-5UL+i));
    ck(bytes[5]==0xa5);ck(stream_owner.status==ASPECT_FILE_TRUNCATED);
    ck(aspect_file_tell(&stream_owner)==(long)FILE_BYTES);
    ck(aspect_file_seek(&stream_owner,65536L,0)==0);
    ck(!(stream_owner.native.flags&ASPECT_FILE_EOF_FLAG));
    ck(aspect_file_read(bytes,4,3,&stream_owner)==3);
    for(i=0;i<12;++i)ck(bytes[i]==pattern(65536UL+i));
    ck(aspect_file_close(&stream_owner)==ASPECT_FILE_OK);
    ck(aspect_file_close(&stream_owner)==ASPECT_FILE_STATE);
}

#if defined(__WATCOMC__)
extern unsigned flow_depth,flow_frame,stack_pointer,ended,file_fault,abi_bad;
extern unsigned value_low,value_high,context_guard[7],exit_state;
extern unsigned char stack_arena[0x3aca+1];
extern unsigned run_file_flow(unsigned operation,unsigned low,unsigned high);
static void reset_native(void)
{
    flow_depth=0;flow_frame=(unsigned)stack_arena;stack_pointer=(unsigned)stack_arena;
    ended=file_fault=abi_bad=exit_state=0;
}
static unsigned native(unsigned operation,unsigned long argument)
{
    unsigned result=run_file_flow(operation,(unsigned)argument,(unsigned)(argument>>16));
    ck(abi_bad==0);ck(context_guard[0]==0xa55a);ck(context_guard[6]==0x5aa5);
    return result;
}
static void native_files(void)
{
    unsigned i;
    unsigned long want;
    ck(aspect_file_open(&stream_owner,"FLOW.DAT")==ASPECT_FILE_OK);reset_native();
    ck(aspect_file_read(bytes,1,255,&stream_owner)==255);
    ck(native(0,0)==0);want=(unsigned long)pattern(255UL)|((unsigned long)pattern(256UL)<<8);
    ck(value_low==(unsigned)want);ck(aspect_file_tell(&stream_owner)==257L);
    ck(aspect_file_seek(&stream_owner,65535L,0)==0);ck(native(1,0)==0);
    want=0;for(i=0;i<4;++i)want|=(unsigned long)pattern(65535UL+i)<<(8*i);
    ck(value_low==(unsigned)want);ck(value_high==(unsigned)(want>>16));
    ck(aspect_file_tell(&stream_owner)==65539L);
    ck(native(2,0x10690UL)==0);ck(aspect_file_tell(&stream_owner)==0x10690L);
    ck(aspect_file_seek(&stream_owner,0x20L,0)==0);
    ck(native(5,0)==0);ck(flow_depth==1);ck(aspect_file_tell(&stream_owner)==0x10680L);
    ck(stack_pointer==(unsigned)stack_arena+6);ck(flow_frame==stack_pointer);
    ck(native(8,0)==0);ck(stack_pointer==(unsigned)stack_arena+10);
    /* A second framed call saves a return position above64KiB. */
    ck(native(5,0)==0);ck(flow_depth==2);ck(aspect_file_tell(&stream_owner)==0x10690L);
    ck(native(8,0)==0);ck(stack_pointer==(unsigned)stack_arena+24);
    ck(native(7,0)==0);ck(flow_depth==1);ck(aspect_file_tell(&stream_owner)==0x10686L);
    ck(stack_pointer==(unsigned)stack_arena+10);
    ck(native(7,0)==0);ck(flow_depth==0);ck(aspect_file_tell(&stream_owner)==0x24L);
    ck(stack_pointer==(unsigned)stack_arena);ck(flow_frame==(unsigned)stack_arena);
    ck(native(6,0)==0);ck(ended==1);
    ck(aspect_file_seek(&stream_owner,0x20L,0)==0);ck(native(9,0)==0);
    ck(aspect_file_tell(&stream_owner)==0x10680L);ck(flow_depth==0);
    ck(aspect_file_seek(&stream_owner,(long)FILE_BYTES-1L,0)==0);reset_native();
    ck(native(0,0)==1);ck(file_fault==1);ck(exit_state==0xffff);
    ck(aspect_file_tell(&stream_owner)==(long)FILE_BYTES);
    ck(aspect_file_seek(&stream_owner,(long)FILE_BYTES-3L,0)==0);reset_native();
    ck(native(1,0)==1);ck(file_fault==1);ck(stream_owner.status==ASPECT_FILE_TRUNCATED);
    ck(aspect_file_tell(&stream_owner)==(long)FILE_BYTES);
    ck(aspect_file_seek(&stream_owner,100L,0)==0);reset_native();
    ck(native(3,0xffffffffUL)==1);ck(file_fault==2);ck(stream_owner.status==ASPECT_FILE_RANGE);
    ck(aspect_file_tell(&stream_owner)==100L);ck(flow_depth==1);
    ck(stack_pointer==(unsigned)stack_arena+4); /* Native call changed state before failed seek. */
    ck(aspect_file_close(&stream_owner)==ASPECT_FILE_OK);reset_native();
    ck(native(3,0)==1);ck(file_fault==3);ck(stack_pointer==(unsigned)stack_arena);
    ck(flow_depth==1); /* Owner must discard partially changed state after abort. */
}
#endif

int main(void)
{
    FILE *done;
    ck(fixture());if(failures)return 2;
    basic_file();
#if defined(__WATCOMC__)
    native_files();
#endif
    done=fopen("DONE.TXT","w");if(!done)return 2;
    fprintf(done,"ASPECT_FILE %lu checks %u failures\n",checks,failures);fclose(done);
    printf("ASPECT_FILE %lu checks %u failures\n",checks,failures);
    return failures?1:0;
}
