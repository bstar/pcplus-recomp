#ifndef PCPLUS_VIEWER_FILE_BACKEND_H
#define PCPLUS_VIEWER_FILE_BACKEND_H
/* Internal near DOS boundaries in FILE_CODE. Out parameters publish only on
 * success; read buffer may be altered on a DOS error. DS=SS preserved. */
unsigned __cdecl viewer_kernel_canonical(const char *,char *);
unsigned __cdecl viewer_kernel_attributes(const char *,unsigned *);
unsigned __cdecl viewer_kernel_open(const char *,unsigned *);
unsigned __cdecl viewer_kernel_device(unsigned,unsigned *);
unsigned __cdecl viewer_kernel_read(unsigned,void __far *,unsigned,unsigned *);
unsigned __cdecl viewer_kernel_seek(unsigned,unsigned long,unsigned long *);
unsigned __cdecl viewer_kernel_close(unsigned);
/* Pure far bridges to existing canonical capture validation/reservation.
 * No DOS IO or reentry into this owner is allowed by the reservation probe. */
unsigned __far __cdecl viewer_admit_validate(const char *);
unsigned __far __cdecl viewer_admit_claim(const char *,void *);
unsigned __far __cdecl viewer_admit_release(void *);
#endif
