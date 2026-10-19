/* Native CRT table/lookup/update with source-owned persistent assignment bytes.
 * The runtime's invocation finish must not retire the process environment.
 * Restore the borrowed CRT vector at process exit, before CRT final cleanup.
 */
#include "environment_runtime.h"
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <malloc.h>
typedef struct assignment {struct assignment *next;char value[1];} assignment;
char **runtime_environment_table;
unsigned runtime_environment_initialized,runtime_environment_owned_entries;
unsigned runtime_environment_alloc_calls;
static char **borrowed;
static assignment *owned;
static unsigned registered;
static void __watcall release_at_exit(void){runtime_environment_release();}
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
unsigned runtime_environment_fail_after=65535U;
#endif
extern char *environment_get_native(const char *name);
extern int environment_put_native(const char *value);
static unsigned admit(void)
{
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 return runtime_environment_alloc_calls++!=runtime_environment_fail_after;
#else
 ++runtime_environment_alloc_calls;return 1;
#endif
}
unsigned runtime_environment_prepare(void)
{
 unsigned count=0;char **table;
 if(runtime_environment_initialized)return 0;
 if(environ)while(environ[count]){if(count>=32765U)return 1;++count;}
 if(!admit())return 1;
 table=_nmalloc((count+1U)*sizeof(char *));if(!table)return 1;
 if(!registered){if(atexit(release_at_exit)){_nfree(table);return 1;}registered=1;}
 if(count)memcpy(table,environ,count*sizeof(char *));table[count]=0;
 borrowed=environ;runtime_environment_table=table;environ=table;
 runtime_environment_initialized=1;return 0;
}
void *runtime_environment_realloc(void *table,unsigned size)
{
 if(!runtime_environment_initialized||table!=runtime_environment_table||!size||!admit())return 0;
 return _nrealloc(table,size);
}
static void collect(void)
{
 assignment **link=&owned,*entry;unsigned i,referenced;
 while((entry=*link)!=0){
  referenced=0;
  for(i=0;runtime_environment_table[i];++i)if(runtime_environment_table[i]==entry->value){referenced=1;break;}
  if(referenced)link=&entry->next;
  else{*link=entry->next;_nfree(entry);--runtime_environment_owned_entries;}
 }
}
char *runtime_environment_get(const char *name)
{
 if(!runtime_environment_initialized)runtime_environment_table=environ;
 return environment_get_native(name);
}
int runtime_environment_put(const char *value)
{
 unsigned length;const char *equal;assignment *entry;int status;
 if(!value||(equal=strchr(value,'='))==0)return -1;
 length=strlen(value);if(length>80U||runtime_environment_prepare())return -1;
 if(equal[1]){
  if(!admit())return -1;
  entry=_nmalloc(offsetof(assignment,value)+length+1U);if(!entry)return -1;
  memcpy(entry->value,value,length+1U);entry->next=owned;owned=entry;
  ++runtime_environment_owned_entries;value=entry->value;
 }
 status=environment_put_native(value);
 environ=runtime_environment_table;collect();return status;
}
void runtime_environment_release(void)
{
 assignment *entry;
 if(!runtime_environment_initialized)return;
 environ=borrowed;borrowed=0;_nfree(runtime_environment_table);runtime_environment_table=0;
 while((entry=owned)!=0){owned=entry->next;_nfree(entry);}
 runtime_environment_initialized=runtime_environment_owned_entries=0;
}
