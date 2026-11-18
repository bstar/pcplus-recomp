#ifndef PCPLUS_TERMINAL_BUILTINS_H
#define PCPLUS_TERMINAL_BUILTINS_H
#ifdef ASPECT_STATE_BUILTINS
#define ASPECT_TERMINAL_VALUE_COUNT 11
#else
#define ASPECT_TERMINAL_VALUE_COUNT 9
#endif
extern unsigned runtime_terminal_values[ASPECT_TERMINAL_VALUE_COUNT];
unsigned __cdecl runtime_terminal_refresh(unsigned);
#ifdef ASPECT_RUNTIME_DIAGNOSTIC
void runtime_terminal_fixture(const unsigned *);
#endif
#endif
