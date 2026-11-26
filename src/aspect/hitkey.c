/* Fresh normalized WORD; diagnostic input is a declared peek boundary. */
#include "hitkey.h"
#ifdef ASPECT_HITKEY_PARENT
#include "resident_render.h"
#else
extern unsigned __cdecl aspect_hitkey_native(void);
#endif
unsigned runtime_hitkey_value;
#ifdef ASPECT_RUNTIME_DIAGNOSTIC
static unsigned fixture_enabled,fixture_available,fixture_word;
unsigned runtime_hitkey_fixture_peeks;
extern unsigned __cdecl runtime_keyboard_peek(void);
void runtime_hitkey_fixture(unsigned enabled,unsigned available,unsigned word)
{fixture_enabled=enabled;fixture_available=available;fixture_word=word;runtime_hitkey_fixture_peeks=0;}
unsigned __cdecl runtime_hitkey_peek(void)
{
 if(!fixture_enabled)return runtime_keyboard_peek();
 ++runtime_hitkey_fixture_peeks;
 return fixture_available?(fixture_word?fixture_word:0x100):0;
}
#endif
unsigned __cdecl runtime_hitkey_refresh(void)
{
#ifdef ASPECT_HITKEY_PARENT
 return aspect_render_hitkey_query(&runtime_hitkey_value);
#else
 runtime_hitkey_value=aspect_hitkey_native();return 0;
#endif
}
