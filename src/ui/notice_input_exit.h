#ifndef PCPLUS_NOTICE_INPUT_EXIT_H
#define PCPLUS_NOTICE_INPUT_EXIT_H
/* Capture PSP/static floor immediately before the first input acquisition.
 * An unresolved lease at CLI exit retains the complete child via DOS31. */
unsigned __far __cdecl notice_input_exit_prepare(void);
unsigned __far __cdecl notice_input_exit_finish(unsigned);
#endif
