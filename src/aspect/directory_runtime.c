/* Owned directory metadata above the maintained child handoff. */
#include "directory_runtime.h"
#include <string.h>
#if defined(ASPECT_RUNTIME_SERIAL)
#include "serial.h"
#endif
extern unsigned runtime_directory_entry;
extern unsigned char runtime_directory_record[114];
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
static unsigned fixture_entry;
static unsigned char fixture_record[114];
void runtime_directory_fixture(unsigned entry,const unsigned char *record)
{
 fixture_entry=entry;
 if(record)memcpy(fixture_record,record,114);else memset(fixture_record,0,114);
}
#endif
void runtime_directory_reset(void)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 const unsigned char *record;
#endif
 runtime_directory_entry=0;memset(runtime_directory_record,0,114);
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 runtime_directory_entry=fixture_entry;
 memcpy(runtime_directory_record,fixture_record,114);
#elif defined(ASPECT_RUNTIME_SERIAL)
 record=aspect_serial_directory_record();
 runtime_directory_entry=aspect_serial_directory_entry();
 if(record)memcpy(runtime_directory_record,record,114);
#endif
}
