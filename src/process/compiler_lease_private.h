/* Private shared layout. No pointers into a lent code bank. */
#ifndef PCPLUS_COMPILER_LEASE_PRIVATE_H
#define PCPLUS_COMPILER_LEASE_PRIVATE_H
#include "compiler_lease.h"
#include <i86.h>
#ifdef COMPILER_LEASE_MODULE
#define COMPILER_LEASE_COMPACT
#define STATE_BYTES 256
#define VERIFY_PARAS 8
#elif defined(COMPILER_LEASE_BANKED)
#define STATE_BYTES 512
#define VERIFY_PARAS 16
#else
#define STATE_BYTES 4352
#define VERIFY_PARAS 256
#endif
#define CHUNK_PARAS 256
#define COOKIE 0x434c
typedef struct {
 unsigned cookie,parent,keep,full,owner,token,phase,handle,crc,dos_error,created,valid,sequence,busy;
#ifdef COMPILER_LEASE_COMPACT
 /* Path construction finishes before verification: these lifetimes do not
  * overlap. Keep the absolute name separate for cleanup after restoration. */
 union {unsigned char buffer[VERIFY_PARAS*16],cwd[64];} scratch;
 unsigned char name[96];
#else
 unsigned char buffer[VERIFY_PARAS*16],name[96],cwd[64];
#endif
} lease_state;
typedef char lease_storage_fits[sizeof(lease_state)<=STATE_BYTES?1:-1];
extern lease_state __far compiler_lease_storage;
#define held compiler_lease_storage
#ifdef COMPILER_LEASE_COMPACT
#define held_buffer held.scratch.buffer
#define held_cwd held.scratch.cwd
#else
#define held_buffer held.buffer
#define held_cwd held.cwd
#endif
extern unsigned __far __cdecl lease_dos_context(void);
extern unsigned __far __cdecl lease_dos_psp(void);
extern unsigned __far __cdecl lease_dos_version(void);
extern unsigned __far __cdecl lease_dos_drive(void);
extern unsigned __far __cdecl lease_dos_error(void);
extern unsigned __far __cdecl lease_dos_resize(unsigned,unsigned);
extern unsigned __far __cdecl lease_dos_create(const unsigned char __far *);
extern unsigned __far __cdecl lease_dos_exists(const unsigned char __far *);
extern unsigned __far __cdecl lease_dos_open(const unsigned char __far *);
extern unsigned __far __cdecl lease_dos_unlink(const unsigned char __far *);
extern unsigned __far __cdecl lease_dos_close(unsigned);
extern unsigned __far __cdecl lease_dos_rewind(unsigned);
extern unsigned __far __cdecl lease_dos_read(unsigned,void __far *,unsigned);
extern unsigned __far __cdecl lease_dos_write(unsigned,const void __far *,unsigned);
extern unsigned __far __cdecl lease_dos_cwd(unsigned char __far *);
#endif
