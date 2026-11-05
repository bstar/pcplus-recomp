#ifndef PCPLUS_VIEWER_DECODE_H
#define PCPLUS_VIEWER_DECODE_H

/* Foreground DOS16, DS=SS. No DOS/BIOS/CRT calls or persistent storage.
 * Caller supplies writable nonoverlapping state/page storage; both may be far.
 * Page is a flat width*rows array of character bytes, initially spaces.
 * Native binary fgets chunks: at most133 bytes including LF, clipped to width,
 * NUL terminates display only, trailing unsigned bytes<=32 are trimmed.
 * No ANSI processing, tab expansion or wrapping at the display width.
 * feed consumes at most256 bytes and stops at a page boundary. Unused source
 * bytes remain caller-owned. position is the next raw file offset; never wraps.
 * finish supplies actual EOF, including a partial final chunk. A full page is
 * not an EOF indication. Reinitialize with its next offset for the next page.
 * Argument errors change no storage. Overflow latches until reinitialization.
 * All passed spans must be valid caller allocations, fit their16-bit offsets
 * and lie below1MB. Segment aliases/overlaps are rejected by linear address.
 */
enum { VIEWER_MORE=0, VIEWER_PAGE=1, VIEWER_EOF=2,
       VIEWER_ARGUMENT=3, VIEWER_OVERFLOW=4 };
typedef struct viewer_decode_state {
 unsigned cookie,width,rows,row,chunk,shown,kept,nul,phase;
 unsigned long position;
 unsigned char __far *page;
} viewer_decode_state;
unsigned __far __cdecl viewer_decode_init(viewer_decode_state __far *,
 unsigned char __far *,unsigned,unsigned,unsigned,unsigned long);
unsigned __far __cdecl viewer_decode_feed(viewer_decode_state __far *,
 const unsigned char __far *,unsigned,unsigned __far *);
unsigned __far __cdecl viewer_decode_finish(viewer_decode_state __far *);
#endif
