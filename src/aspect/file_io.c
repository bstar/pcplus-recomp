#include "file_io.h"
#include <stddef.h>
#include <string.h>
#include <limits.h>
#if defined(ASPECT_FILE_OPEN_PROBE)
#include <dos.h>
#include <io.h>
#include <fcntl.h>
#include <errno.h>
/* Explicit diagnostic build only. Raw DOS logging needs no stdio allocation.
 * A failed fopen is compared with a read-only DOS open of the same path. */
static void open_probe(const char *path,FILE *handle,int saved_errno)
{
    unsigned record[48],i,status,written;int raw,log;
    unsigned char *name=(unsigned char *)(record+7);
    memset(record,0,sizeof(record));record[0]=0x4f46;record[1]=1;
    record[2]=handle!=0;record[3]=(unsigned)saved_errno;record[4]=65535U;
    for(i=0;i<81 && path[i];++i)name[i]=(unsigned char)path[i];
    record[6]=i;
    if(!handle){
        status=_dos_open(path,O_RDONLY|O_BINARY,&raw);record[4]=status;
        if(!status)record[5]=_dos_close(raw);
    }
    status=_dos_open("D:\\FOPEN.BIN",O_WRONLY|O_BINARY,&log);
    if(status)status=_dos_creat("D:\\FOPEN.BIN",0,&log);
    if(!status){
        if(lseek(log,0L,SEEK_END)>=0)_dos_write(log,record,sizeof(record),&written);
        _dos_close(log);
    }
    errno=saved_errno;
}
#endif
#if !defined(__WATCOMC__)
#include <stdint.h>
#endif

#define ASPECT_FILE_MAGIC 0x4153
#define ASPECT_FILE_MAX_POSITION 2147483647L
#if defined(__WATCOMC__)
typedef char aspect_file_pointer_is_near[(sizeof(void *)==2)?1:-1];
typedef char aspect_file_count_offset[(offsetof(aspect_file_prefix,remaining)==2)?1:-1];
typedef char aspect_file_flags_offset[(offsetof(aspect_file_prefix,flags)==6)?1:-1];
#endif

static int valid(aspect_file *file)
{
    if(!file)return 0;
#if defined(__WATCOMC__)
    if((unsigned)file>65535U-sizeof(*file))return 0;
#endif
    return file->magic==ASPECT_FILE_MAGIC;
}
static void reset_window(aspect_file *file)
{
    file->native.cursor=file->window;
    file->native.remaining=0;
    file->buffered=0;
}
static int window_valid(aspect_file *file,int refill)
{
    unsigned consumed;
    if(file->buffered>ASPECT_FILE_WINDOW)return 0;
    /* Pointer comparisons are within the owned window in valid callers. Avoid
     * subtraction until the numeric span is checked on the DOS near ABI. */
#if defined(__WATCOMC__)
    if((unsigned)file->native.cursor<(unsigned)file->window ||
       (unsigned)file->native.cursor>(unsigned)file->window+file->buffered)return 0;
#else
    if((uintptr_t)file->native.cursor<(uintptr_t)file->window ||
       (uintptr_t)file->native.cursor>(uintptr_t)file->window+file->buffered)return 0;
#endif
    consumed=(unsigned)(file->native.cursor-file->window);
    if(refill)return consumed==file->buffered && file->native.remaining==-1;
    return file->native.remaining>=0 &&
           (unsigned)file->native.remaining==file->buffered-consumed;
}
static int fail(aspect_file *file,unsigned status)
{
    file->status=status;
    if(status==ASPECT_FILE_IO || status==ASPECT_FILE_STATE)
        file->native.flags|=ASPECT_FILE_ERROR_FLAG;
    return -1;
}
unsigned aspect_file_init(aspect_file *file)
{
    if(!file)return ASPECT_FILE_ARGUMENT;
#if defined(__WATCOMC__)
    if((unsigned)file>65535U-sizeof(*file))return ASPECT_FILE_ARGUMENT;
#endif
    memset(file,0,sizeof(*file));file->magic=ASPECT_FILE_MAGIC;
    reset_window(file);return ASPECT_FILE_OK;
}
unsigned aspect_file_open(aspect_file *file,const char *path)
{
    FILE *handle;
    if(!valid(file))return ASPECT_FILE_STATE;
    if(file->handle)return ASPECT_FILE_STATE;
    if(!path || !*path)return ASPECT_FILE_ARGUMENT;
    handle=fopen(path,"rb");
#if defined(ASPECT_FILE_OPEN_PROBE)
    open_probe(path,handle,errno);
#endif
    if(!handle){file->status=ASPECT_FILE_IO;return ASPECT_FILE_IO;}
#if defined(ASPECT_FILE_OWNED_WINDOW)
    /* The native reader already owns its256-byte read-ahead window. Avoid a
     * second stdio heap buffer; fread still fills that window in one request.
     * Install before the first read, and never publish a failed stream. */
    if(setvbuf(handle,0,_IONBF,0)){
        fclose(handle);file->status=ASPECT_FILE_IO;return ASPECT_FILE_IO;
    }
#endif
    file->handle=handle;file->native.flags=0;file->status=ASPECT_FILE_OK;
    reset_window(file);return ASPECT_FILE_OK;
}
unsigned aspect_file_close(aspect_file *file)
{
    int result;
    if(!valid(file) || !file->handle)return ASPECT_FILE_STATE;
    result=fclose(file->handle);file->handle=0;reset_window(file);
    if(result){fail(file,ASPECT_FILE_IO);return ASPECT_FILE_IO;}
    file->status=ASPECT_FILE_OK;file->native.flags=0;return ASPECT_FILE_OK;
}
long aspect_file_tell(aspect_file *file)
{
    long physical;
    if(!valid(file) || !file->handle)return -1L;
    if(!window_valid(file,0))return fail(file,ASPECT_FILE_STATE);
    physical=ftell(file->handle);
    if(physical<0 || physical<file->native.remaining)return fail(file,ASPECT_FILE_IO);
#if LONG_MAX > 2147483647L
    if(physical>ASPECT_FILE_MAX_POSITION)return fail(file,ASPECT_FILE_IO);
#endif
    return physical-file->native.remaining;
}
int aspect_file_seek(aspect_file *file,long offset,unsigned origin)
{
    long base,target;
    if(!valid(file) || !file->handle)return -1;
    if(origin>1)return fail(file,ASPECT_FILE_ARGUMENT);
#if LONG_MAX > 2147483647L
    if(offset>ASPECT_FILE_MAX_POSITION || offset<(-ASPECT_FILE_MAX_POSITION-1L))
        return fail(file,ASPECT_FILE_RANGE);
#endif
    base=origin?aspect_file_tell(file):0L;
    if(base<0)return -1;
    if((offset<0 && offset < -base) ||
       (offset>=0 && offset>ASPECT_FILE_MAX_POSITION-base))
        return fail(file,ASPECT_FILE_RANGE);
    target=base+offset;
    if(fseek(file->handle,target,SEEK_SET))return fail(file,ASPECT_FILE_IO);
    reset_window(file);file->native.flags=0;file->status=ASPECT_FILE_OK;
    return 0;
}
int aspect_file_refill(aspect_file *file)
{
    size_t got;
    if(!valid(file) || !file->handle)return -1;
    if(!window_valid(file,1))return fail(file,ASPECT_FILE_STATE);
    got=fread(file->window,1,ASPECT_FILE_WINDOW,file->handle);
    reset_window(file);
    if(!got){
        if(ferror(file->handle))return fail(file,ASPECT_FILE_IO);
        file->native.flags|=ASPECT_FILE_EOF_FLAG;file->status=ASPECT_FILE_EOF;
        return -1;
    }
    file->buffered=(unsigned)got;file->native.cursor=file->window+1;
    file->native.remaining=(int)got-1;file->status=ASPECT_FILE_OK;
    return file->window[0];
}
unsigned aspect_file_read(void *destination,unsigned size,unsigned count,aspect_file *file)
{
    unsigned total,done=0;
    unsigned char *out=(unsigned char *)destination;
    int byte;
    if(!valid(file) || !file->handle)return 0;
    if(!size || !count)return 0;
    if(!destination || count>65535U/size){fail(file,ASPECT_FILE_ARGUMENT);return 0;}
    total=size*count;
#if defined(__WATCOMC__)
    if((unsigned)destination>65535U-total+1U){fail(file,ASPECT_FILE_ARGUMENT);return 0;}
    if((unsigned long)(unsigned)destination<(unsigned long)(unsigned)file+sizeof(*file) &&
       (unsigned long)(unsigned)file<(unsigned long)(unsigned)destination+total){fail(file,ASPECT_FILE_ARGUMENT);return 0;}
#else
    if((uintptr_t)destination<(uintptr_t)file+sizeof(*file) &&
       (uintptr_t)file<(uintptr_t)destination+total){fail(file,ASPECT_FILE_ARGUMENT);return 0;}
#endif
    if(!window_valid(file,0)){fail(file,ASPECT_FILE_STATE);return 0;}
    while(done<total){
        if(file->native.remaining){
            byte=*file->native.cursor++;--file->native.remaining;
        }else{
            --file->native.remaining;byte=aspect_file_refill(file);
            if(byte<0)break;
        }
        out[done++]=(unsigned char)byte;
    }
    if(done<total && file->status==ASPECT_FILE_EOF && done%size)
        file->status=ASPECT_FILE_TRUNCATED;
    if(done==total)file->status=ASPECT_FILE_OK;
    return done/size;
}
