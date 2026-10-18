#ifndef PCPLUS_XLT_LIVE_H
#define PCPLUS_XLT_LIVE_H
#include "xlt_dos.h"
enum { XLT_LIVE_STATE=7 };
/* Foreground-only DOS16 near-cdecl, DS=SS. Bind before the settings child;
 * capture current and optional PCPLUS-directory canonical paths (max63 bytes).
 * No table open or active-state mutation. Invalid fallback does not hide a
 * valid current-file selection. New bind drops previous staged work. */
unsigned __cdecl xlt_live_bind(unsigned psp);
/* Stage0/2 without file IO, or stage1 with exact256-byte checked read. Only
 * missing current files may fall back. Required result8 must be nonwrapping
 * and outside private storage. Argument errors leave result/staging intact;
 * a valid failed attempt drops readiness and preserves active table/state. */
unsigned __cdecl xlt_live_stage(unsigned mode,xlt_dos_result *result);
/* Caller owns quiescent terminal input/UART handoff. Consume a matching stage;
 * copy table for mode1, leave unused table bytes alone for0/2. No DOS calls.
 * Caller commits mode/enabled/mask together after success and before resuming
 * input. Output256 must be nonwrapping and outside private storage. No active
 * globals are read or changed here. Wrong/missing stage returns STATE. */
unsigned __cdecl xlt_live_commit(unsigned mode,unsigned char *table);
/* Startup only: reset binding, stage exact mode1 table (explicit path or the
 * default current/PCPLUS lookup), and commit. Modes0/2 do no filesystem IO.
 * Remember the chosen canonical source for a later explicit reload. Invalid
 * arguments leave all state alone; a valid failed initialization unbinds it. */
unsigned __cdecl xlt_live_initialize(unsigned psp,unsigned mode,const char *path,
 unsigned char *table,xlt_dos_result *result);
/* Foreground input/UART handoff required. 0 stages the frozen active path,
 * 1 accepts into table256, 2 cancels this API's stage. table must be NULL for
 * 0/2; result8 is always required. No fallback after source selection. Active
 * mode/mask are caller-owned and must remain mode1/FF throughout acceptance. */
unsigned __cdecl xlt_live_reload(unsigned action,unsigned char *table,xlt_dos_result *result);
#endif
