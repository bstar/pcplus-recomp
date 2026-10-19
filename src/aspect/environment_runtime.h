#ifndef ASPECT_ENVIRONMENT_RUNTIME_H
#define ASPECT_ENVIRONMENT_RUNTIME_H
extern char **runtime_environment_table;
extern unsigned runtime_environment_initialized,runtime_environment_owned_entries;
extern unsigned runtime_environment_alloc_calls;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
extern unsigned runtime_environment_fail_after;
#endif
unsigned runtime_environment_prepare(void);
void runtime_environment_release(void);
char *runtime_environment_get(const char *name);
int runtime_environment_put(const char *value);
void *runtime_environment_realloc(void *table,unsigned size);
#endif
