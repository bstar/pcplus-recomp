/* One real native receiver session, controlled peer UART, actual DOS storage. */
#include "download_file.h"
#include <stdio.h>
unsigned __cdecl transfer_storage_prepare(void);
unsigned __cdecl transfer_storage_control(unsigned mode);
unsigned __cdecl transfer_storage_owner_result(void);
unsigned __cdecl transfer_composite_run(void);
extern unsigned transfer_storage_fault;
unsigned __cdecl transfer_storage_begin(void)
{ return transfer_download_begin("OUTPUT.BIN","PART.TMP"); }
int main(int argc,char **argv)
{
 unsigned result,status,mode=argc>1 ? (unsigned char)argv[1][0]:0;
 transfer_storage_fault=mode;
 transfer_storage_prepare();transfer_storage_control(mode);transfer_composite_run();
 result=transfer_storage_owner_result();
 printf("OWNER %u STATE %u FIRST %u BYTES %lu\n",result,transfer_download_result.state,transfer_download_result.first_status,transfer_download_result.bytes_written);
 if(mode=='W'){
  if(result!=1 || transfer_download_result.first_status!=TF_WRITE || transfer_download_result.bytes_written!=10257UL || transfer_download_finish()!=TF_WRITE)return 10;
  status=transfer_download_abort();
  if(status || transfer_download_result.stage_exists || transfer_download_result.handle_open)return 11;
  puts("PASS native ignored final short write cannot install partial");return 0;
 }
 if(mode=='C'){
  if(result!=1 || transfer_download_result.first_status!=TF_CLOSE || !transfer_download_result.handle_uncertain || transfer_download_finish()!=TF_RECOVERY || transfer_download_abort()!=TF_RECOVERY || !transfer_download_result.stage_exists)return 12;
  puts("PASS native ignored close error retains recovery stage without install");return 0;
 }
 if(mode=='X' || mode=='T'){
  if(result!=0 || transfer_download_result.first_status)return 13;
  if(mode=='T' && !transfer_download_result.handle_open)return 14;
  if(transfer_download_abort()!=TF_OK || transfer_download_result.stage_exists || transfer_download_result.handle_open)return 15;
  puts("PASS canceled or timed out native owner closes and discards owned stage");return 0;
 }
 if(result!=1 || transfer_download_result.first_status || transfer_download_result.state!=TF_CLOSED || transfer_download_result.bytes_written!=(mode=='M'?11136UL:11264UL)){
  transfer_download_abort();return 1;
 }
 if(transfer_download_finish()!=TF_OK || transfer_download_result.state!=TF_INSTALLED || transfer_download_result.stage_exists)return 2;
 puts("PASS native receiver periodic and final bytes installed after checked close");return 0;
}
