/* Real DOS boundaries plus declared final-write/close fault injection. */
#define transfer_fs_write transfer_storage_dos_write
#define transfer_fs_close transfer_storage_dos_close
#include "../src/transfer/download_fs.c"
#undef transfer_fs_write
#undef transfer_fs_close
unsigned transfer_storage_fault;
static unsigned writes;
unsigned transfer_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{
 ++writes;
 /* Second native write is the EOT tail after the10240-byte periodic flush. */
 if(transfer_storage_fault=='W' && writes==2 && count>17)
  return transfer_storage_dos_write(handle,data,17,written);
 return transfer_storage_dos_write(handle,data,count,written);
}
unsigned transfer_fs_close(int handle)
{
 unsigned error=transfer_storage_dos_close(handle);
 return !error && transfer_storage_fault=='C' ? 5:error;
}
