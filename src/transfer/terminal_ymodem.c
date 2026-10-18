#include "ymodem.h"
#include "batch_download.h"
#include "batch_upload.h"
#include "upload_file.h"
#include <stddef.h>
typedef char batch_blocks_abi[offsetof(ymodem_result,blocks)==6?1:-1];
typedef char batch_files_abi[offsetof(ymodem_result,files)==10?1:-1];
extern char terminal_transfer_filename[64];
extern unsigned terminal_transfer_fault,terminal_transfer_cleanup_status;
extern unsigned terminal_transfer_direction;
void __cdecl terminal_batch_initialize(void)
{
 (void)batch_download_initialize();
 (void)batch_upload_initialize();
}
unsigned __cdecl terminal_batch_store(void)
{
 unsigned status=ymodem_run(terminal_transfer_filename,terminal_transfer_direction);
 if(!status)return 0;
 if(status==YM_END_UNCONFIRMED)return 2;
 if(!terminal_transfer_fault)terminal_transfer_fault=
  status==YM_CANCEL?2:status==YM_TIMEOUT?3:status==YM_IO?3:7;
 if(upload_source_result.handle_uncertain ||
    batch_download_result.file.handle_uncertain ||
    batch_download_result.file.stage_exists)
  terminal_transfer_cleanup_status=1;
 return 1;
}
