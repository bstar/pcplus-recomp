/* Separate-CS diagnostic only. Exercise the exact bank kernel below the
 * fault wrapper, including DTA save/restore and renamed CRT conventions. */
#include <dos.h>
#include <string.h>
#include "meta_scan_fs.h"
#ifdef META_BANK_TEST_FAULTS
#define key_file_attr key_real_attr
#define key_file_open key_real_open
#define key_file_create key_real_create
#define key_file_read key_real_read
#define key_file_write key_real_write
#define key_file_close key_real_close
#define key_file_rename key_real_rename
#define key_file_delete key_real_delete
#endif
#include "key_file_fs.h"
static void __far *get_dta(void);
#pragma aux get_dta = "mov ah,2fh" "int 21h" "mov ax,bx" "mov dx,es" value [dx ax] modify [ax bx dx es];
static void set_dta(void __far *);
#pragma aux set_dta = "push ds" "mov ds,dx" "mov dx,ax" "mov ah,1ah" "int 21h" "pop ds" parm [ax dx] modify [ax dx];
static unsigned segments(void);
#pragma aux segments = "mov ax,ds" "mov dx,ss" "cmp ax,dx" "mov ax,0" "jne short unequal" "inc ax" "unequal:" value [ax] modify [ax dx];
static unsigned get_es(void);
#pragma aux get_es = "mov ax,es" value [ax];
static void set_es(unsigned);
#pragma aux set_es = "mov es,ax" parm [ax] modify [es];
#define CHECK(x) do {++checks;if(!(x))return __LINE__;}while(0)
unsigned __far __cdecl meta_bank_kernel_probe(unsigned __far *total)
{
 unsigned checks=0,i,n,error,attr,oldes;int h=-1,k=-1;
 unsigned char input[128],output[128],sentinel[128];
 struct find_t first,second;
 void __far *previous=get_dta();
 CHECK(sizeof(struct find_t)==43 && segments());
 for(i=0;i<128;++i)input[i]=(unsigned char)(i^0xa5);
 /* These aliases have the generic Watcom ABI, not the compiler's special
  * CRT-clobber knowledge. Include stack count0 and nonzero with guards. */
 oldes=get_es();set_es(0xb800);
 _fmemset(output,0x5a,128);CHECK(get_es()==0xb800);
 _fmemcpy(output+1,input+1,126);CHECK(get_es()==0xb800);
 CHECK(output[0]==0x5a && output[127]==0x5a && !_fmemcmp(output+1,input+1,126) && get_es()==0xb800);
 _fmemcpy(output,input,0);CHECK(output[0]==0x5a && get_es()==0xb800);
 CHECK(_fmemcmp(output,input,0)==0 && get_es()==0xb800);
 CHECK(_fstrcmp("ABC","ABC")==0 && get_es()==0xb800);
 set_es(oldes);
 key_file_delete("C:\\LAB\\KERNEL.TST");key_file_delete("C:\\LAB\\SECOND.TST");
 CHECK(!key_file_create("C:\\LAB\\KERNEL.TST",0,&h));
 CHECK(!key_file_write(h,input,128,&n) && n==128);
 CHECK(!key_file_close(h));h=-1;
 CHECK(!key_file_attr("C:\\LAB\\KERNEL.TST",&attr) && !(attr&0x19));
 CHECK(key_file_create("C:\\LAB\\KERNEL.TST",0,&h)!=0 && h==-1);
 CHECK(key_file_open("C:\\LAB\\KERNEL.TST",1,&h)==1 && h==-1);
 CHECK(key_file_open("C:\\LAB\\KERNEL.TST",0x100,&h)==1 && h==-1);
 CHECK(!key_file_open("C:\\LAB\\KERNEL.TST",0,&h));
 CHECK(!key_file_read(h,output,128,&n) && n==128 && !memcmp(input,output,128));
 CHECK(!key_file_read(h,output,128,&n) && n==0 && !key_file_close(h));h=-1;
 CHECK(!key_file_open("C:\\LAB\\KERNEL.TST",0x80,&h) && !key_file_close(h));h=-1;
 CHECK(!key_file_create("C:\\LAB\\SECOND.TST",0,&k) && !key_file_close(k));
 CHECK(key_file_rename("C:\\LAB\\KERNEL.TST","C:\\LAB\\SECOND.TST")!=0);
 CHECK(!key_file_open("C:\\LAB\\KERNEL.TST",0,&h));
 CHECK(!key_file_read(h,output,128,&n) && n==128 && !memcmp(input,output,128) && !key_file_close(h));h=-1;
 /* Two interleaved DOS continuations, with an independent selected DTA. */
 memset(sentinel,0x7d,sizeof(sentinel));set_dta(sentinel);
 memset(&first,0,sizeof(first));memset(&second,0,sizeof(second));
 CHECK(!meta_scan_fs_first("C:\\LAB\\*.TST",&first));
 CHECK(get_dta()==(void __far *)sentinel);
 CHECK(!meta_scan_fs_first("C:\\LAB\\KERNEL.*",&second));
 CHECK(get_dta()==(void __far *)sentinel);
 CHECK(!meta_scan_fs_next(&first));
 CHECK(get_dta()==(void __far *)sentinel);
 CHECK(meta_scan_fs_next(&second)==18 && get_dta()==(void __far *)sentinel);
 CHECK(meta_scan_fs_next(&first)==18 && get_dta()==(void __far *)sentinel);
 error=meta_scan_fs_first("C:\\LAB\\NOFILE.ZZZ",&first);
 CHECK((error==2 || error==18) && get_dta()==(void __far *)sentinel);
 CHECK(meta_scan_fs_first("C:\\MISSING\\*.TST",&first)!=0 && get_dta()==(void __far *)sentinel);
 for(i=0;i<128;++i)CHECK(sentinel[i]==0x7d);
 set_dta(previous);CHECK(get_dta()==previous && segments());
 CHECK(!key_file_delete("C:\\LAB\\SECOND.TST"));
 CHECK(!key_file_rename("C:\\LAB\\KERNEL.TST","C:\\LAB\\SECOND.TST"));
 CHECK(key_file_attr("C:\\LAB\\KERNEL.TST",&attr)==2);
 CHECK(!key_file_delete("C:\\LAB\\SECOND.TST"));
 CHECK(key_file_delete("C:\\LAB\\SECOND.TST")==2);
 *total=checks;return 0;
}
