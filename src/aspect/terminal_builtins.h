#ifndef PCPLUS_TERMINAL_BUILTINS_H
#define PCPLUS_TERMINAL_BUILTINS_H
extern unsigned runtime_terminal_values[9];
unsigned __cdecl runtime_terminal_refresh(unsigned);
#ifdef ASPECT_RUNTIME_DIAGNOSTIC
void runtime_terminal_fixture(const unsigned *);
#endif
#endif
