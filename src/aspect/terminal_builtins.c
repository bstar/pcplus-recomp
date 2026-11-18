/* Fresh owned WORD snapshots, supplied by a read-only parent request or model. */
#include "terminal_builtins.h"
#include "runtime.h"
#ifdef ASPECT_TERMINAL_QUERY
#include "resident_render.h"
#endif
unsigned runtime_terminal_values[9];
#ifdef ASPECT_RUNTIME_DIAGNOSTIC
static unsigned fixture[9],ready;
void runtime_terminal_fixture(const unsigned *values)
{unsigned i;ready=values!=0;if(values)for(i=0;i<9;++i)fixture[i]=values[i];}
#endif
unsigned __cdecl runtime_terminal_refresh(unsigned selector)
{
 unsigned index,value=0,status=ASPECT_RUN_UNSUPPORTED;
 if(selector==0)index=0;
 else if(selector>=12&&selector<=19)index=selector-11;
 else return ASPECT_RUN_OPERAND;
#ifdef ASPECT_RUNTIME_DIAGNOSTIC
 if(ready){value=fixture[index];status=0;}
#elif defined(ASPECT_TERMINAL_QUERY)
 status=aspect_render_terminal_query(index,&value);
#endif
 if(!status)runtime_terminal_values[index]=value;
 return status;
}
