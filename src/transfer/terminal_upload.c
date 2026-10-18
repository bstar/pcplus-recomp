/* Maintained foreground owner around the recovered ordinary sender. */
#include "upload_file.h"
extern char terminal_transfer_filename[64];
extern unsigned terminal_transfer_fault,terminal_transfer_cleanup_status;
extern unsigned terminal_transfer_native_status;
extern unsigned terminal_upload_file_size_low,terminal_upload_file_size_high;
extern unsigned long terminal_upload_accepted_bytes;
unsigned __cdecl terminal_transfer_native_call(const char *path);
void __cdecl terminal_upload_initialize(void)
{ (void)upload_source_initialize(); }
static void file_fault(void)
{ if(!terminal_transfer_fault)terminal_transfer_fault=7; }
unsigned __cdecl terminal_upload_open(const char *path,const char *mode)
{
 unsigned token=upload_source_open(path,mode);
 if(!token)file_fault();return token;
}
unsigned __cdecl terminal_upload_read(void *data,unsigned size,unsigned count,unsigned token)
{
 unsigned result=upload_source_read(data,size,count,token);
 if(result==0xffff)file_fault();return result;
}
unsigned __cdecl terminal_upload_close(unsigned token)
{
 unsigned result;
 /* The native owner also calls fclose while aborting a prefetched source.
  * Incomplete input is expected on protocol failure, not a new disk error.
  * Use actual ACKed bytes: the native attempted-block counter is unreliable. */
 if(token==2 && terminal_upload_accepted_bytes<upload_source_result.size){
  result=upload_source_abort();
  if(result){file_fault();return 0xffff;}
  if(!terminal_transfer_fault)terminal_transfer_fault=
   terminal_transfer_native_status==11?2:terminal_transfer_native_status==15?4:3;
  return 0;
 }
 result=upload_source_close(token);
 if(result)file_fault();return result;
}
unsigned __cdecl terminal_upload_store(void)
{
 unsigned status,native;
 status=upload_source_begin(terminal_transfer_filename);
 if(status){
  file_fault();
  if(upload_source_result.handle_uncertain)terminal_transfer_cleanup_status=UF_RECOVERY;
  return 1;
 }
 /* Native remaining-size arithmetic is signed32; padded totals must also fit. */
 if(upload_source_result.size>0x7ffffbffUL){file_fault();goto abort;}
 terminal_upload_file_size_low=(unsigned)upload_source_result.size;
 terminal_upload_file_size_high=(unsigned)(upload_source_result.size>>16);
 native=terminal_transfer_native_call(upload_source_result.path);
 if(native!=1 || terminal_transfer_fault || upload_source_result.first_status ||
    terminal_upload_accepted_bytes<upload_source_result.size){
  if(!terminal_transfer_fault)terminal_transfer_fault=upload_source_result.first_status?7:
   terminal_transfer_native_status==11?2:terminal_transfer_native_status==15?4:3;
  goto abort;
 }
 status=upload_source_finish();
 if(!status)return 0;
 file_fault();
abort:
 status=upload_source_abort();
 if(status)terminal_transfer_cleanup_status=status;
 return 1;
}
unsigned __cdecl terminal_upload_cleanup(void)
{
 if(upload_source_result.handle_uncertain)return UF_RECOVERY;
 return upload_source_result.handle_open ? upload_source_abort():UF_OK;
}
