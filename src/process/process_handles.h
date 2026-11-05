#ifndef PCPLUS_PROCESS_HANDLES_H
#define PCPLUS_PROCESS_HANDLES_H
/* DOS3+ private-handle inheritance bracket. Existing parent SFT references and
 * CRT buffers remain owned; only selected parent JFT entries are hidden while
 * DOS constructs the child. Call end before any parent stream IO, on failure
 * as well as success. This is lifetime isolation, not DOS memory security. */
#if defined(PROCESS_HANDLES_BANKED)
#define PROCESS_HANDLES_FAR __far
/* Retained code-bank variant. DS=SS, IF1/DF0; no DGROUP state allocation. */
unsigned __far __cdecl process_handles_active_query(void);
#else
#define PROCESS_HANDLES_FAR
extern unsigned process_handles_active;
#endif
unsigned PROCESS_HANDLES_FAR __cdecl process_handles_begin(const unsigned *descriptors,unsigned count);
unsigned PROCESS_HANDLES_FAR __cdecl process_handles_end(void);
#if defined(ASPECT_EXTERNAL_UNWIND) || defined(PROCESS_HANDLES_BANKED)
unsigned PROCESS_HANDLES_FAR __cdecl process_handles_recover(void);
#endif
#endif
