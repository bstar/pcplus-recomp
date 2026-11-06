/* Exact build identity before DOS4B03, normalized image identity before entry.
 * No allocation, PSP, static state or own working frame. expected.h is generated
 * by the source-only module builder; it is not trusted input from the card. */
#include <dos.h>
#include "loader.h"
#include "expected.h"
extern unsigned __cdecl chat_dos_overlay_load(const char *,unsigned);
extern unsigned __cdecl chat_file_open(const char *,int *);
extern unsigned __cdecl chat_file_read(int,void *,unsigned,unsigned *);
extern unsigned __cdecl chat_file_close(int);
static unsigned long crc_byte(unsigned long crc,unsigned value)
{
    unsigned bit;crc^=value;
    for(bit=0;bit<8;++bit)crc=(crc>>1)^((crc&1)?0xedb88320UL:0);
    return crc;
}
static unsigned verify_file(const char *path,chat_word *dos_error)
{
    int handle;unsigned error,got,i,total=0;
    unsigned char bytes[128];unsigned long crc=0xffffffffUL;
    error=chat_file_open(path,&handle);if(error){*dos_error=error;return CHAT_LOAD_OPEN;}
    for(;;){
        error=chat_file_read(handle,bytes,sizeof(bytes),&got);
        if(error){*dos_error=error;chat_file_close(handle);return CHAT_LOAD_READ;}
        if(!got)break;
        if(got>CHAT_EXPECTED_FILE_BYTES-total){chat_file_close(handle);return CHAT_LOAD_IDENTITY;}
        total+=got;for(i=0;i<got;++i)crc=crc_byte(crc,bytes[i]);
    }
    error=chat_file_close(handle);if(error){*dos_error=error;return CHAT_LOAD_READ;}
    return total==CHAT_EXPECTED_FILE_BYTES && (crc^0xffffffffUL)==CHAT_EXPECTED_FILE_CRC32?0:CHAT_LOAD_IDENTITY;
}
unsigned CHAT_FAR __cdecl chat_module_image_valid(unsigned segment)
{
    const unsigned char CHAT_FAR *bytes=(const unsigned char CHAT_FAR *)MK_FP(segment,0);
    unsigned i=0,r=0,value;unsigned long crc=0xffffffffUL;
    if(segment<0x50 || (unsigned long)segment*16+CHAT_EXPECTED_IMAGE_BYTES>0xa0000UL)return 0;
    while(i<CHAT_EXPECTED_IMAGE_BYTES){
        if(r<CHAT_EXPECTED_RELOCATIONS && i==chat_expected_relocations[r]){
            value=(unsigned)((bytes[i]|((unsigned)bytes[i+1]<<8))-segment);
            crc=crc_byte(crc,value&255);crc=crc_byte(crc,value>>8);i+=2;++r;
        }else crc=crc_byte(crc,bytes[i++]);
    }
    return (crc^0xffffffffUL)==CHAT_EXPECTED_IMAGE_CRC32;
}
unsigned CHAT_FAR __cdecl chat_module_load(chat_module_handle *h,chat_session CHAT_FAR *state,const char *path,void CHAT_FAR *storage,unsigned capacity)
{
    unsigned segment=FP_SEG(storage),error,i;
    unsigned long start=(unsigned long)segment*16,at=(unsigned long)FP_SEG(state)*16+FP_OFF(state);
    unsigned char CHAT_FAR *clear=(unsigned char CHAT_FAR *)state;
    chat_module_entry entry;chat_module_request query;
    if(h->busy)return CHAT_LOAD_BUSY;
    if(h->loaded)return CHAT_LOAD_ACTIVE;
    if(!state || !storage || !path || FP_OFF(storage) || capacity<CHAT_EXPECTED_IMAGE_BYTES ||
       start<0x500UL || start+capacity>0xa0000UL || FP_OFF(state)>65535U-sizeof(*state) ||
       at<0x500UL || at+sizeof(*state)>0xa0000UL || (at<start+CHAT_EXPECTED_IMAGE_BYTES && at+sizeof(*state)>start))return CHAT_LOAD_BOUNDS;
    h->dos_error=0;
    error=verify_file(path,&h->dos_error);if(error)return error;
    error=chat_dos_overlay_load(path,segment);
    if(error){h->dos_error=error;return CHAT_LOAD_DOS;}
    if(!chat_module_image_valid(segment))return CHAT_LOAD_IMAGE;
    entry=(chat_module_entry)MK_FP(segment+CHAT_EXPECTED_ENTRY_SEGMENT,CHAT_EXPECTED_ENTRY_OFFSET);
    for(i=0;i<sizeof(*state);++i)clear[i]=0;
    query.api=CHAT_MODULE_API;query.operation=CHAT_MODULE_QUERY;query.state=state;
    if(entry(&query)!=sizeof(*state) || query.result!=sizeof(*state))return CHAT_LOAD_API;
    h->entry=entry;h->state=state;h->loaded=1;h->busy=h->active=0;h->segment=segment;
    return 0;
}
unsigned CHAT_FAR __cdecl chat_module_call(chat_module_handle *h,chat_module_request CHAT_FAR *r)
{
    unsigned result;
    if(h->busy)return CHAT_MODULE_BAD;
    if(!h->loaded || !r || r->api!=CHAT_MODULE_API || r->state!=h->state || r->operation>CHAT_MODULE_MAX_OPERATION)return CHAT_MODULE_BAD;
    h->busy=1;result=h->entry(r);h->busy=0;
    if(r->operation!=CHAT_MODULE_QUERY)h->active=h->state->send.active || h->state->screen.active;
#ifdef CHAT_PRESENTATION
    if(h->state->presentation)h->active=1;
#endif
#ifdef CHAT_TEXT
    if(h->state->text.active)h->active=1;
#endif
    return result;
}
unsigned CHAT_FAR __cdecl chat_module_unload(chat_module_handle *h)
{
    if(h->busy)return CHAT_LOAD_BUSY;
    if(h->active)return CHAT_LOAD_ACTIVE;
    h->entry=0;h->state=0;h->loaded=h->segment=0;return 0;
}
