#ifndef PCPLUS_PROCESS_HANDLES_H
#define PCPLUS_PROCESS_HANDLES_H
/* DOS3+ private-handle inheritance bracket. Existing parent SFT references and
 * CRT buffers remain owned; only selected parent JFT entries are hidden while
 * DOS constructs the child. Call end before any parent stream IO, on failure
 * as well as success. This is lifetime isolation, not DOS memory security. */
unsigned __cdecl process_handles_begin(const unsigned *descriptors,unsigned count);
unsigned __cdecl process_handles_end(void);
extern unsigned process_handles_active;
#if defined(ASPECT_EXTERNAL_UNWIND)
unsigned __cdecl process_handles_recover(void);
#endif
#endif
