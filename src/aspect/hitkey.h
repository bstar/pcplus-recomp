#ifndef PCPLUS_ASPECT_HITKEY_H
#define PCPLUS_ASPECT_HITKEY_H
extern unsigned runtime_hitkey_value;
unsigned __cdecl runtime_hitkey_refresh(void);
#ifdef ASPECT_RUNTIME_DIAGNOSTIC
void runtime_hitkey_fixture(unsigned,unsigned,unsigned);
extern unsigned runtime_hitkey_fixture_peeks;
#endif
#endif
