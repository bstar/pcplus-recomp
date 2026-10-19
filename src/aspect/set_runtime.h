#ifndef PCPLUS_ASPECT_SET_RUNTIME_H
#define PCPLUS_ASPECT_SET_RUNTIME_H
void runtime_set_reset(void);
unsigned runtime_set_status_refresh(void);
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
extern unsigned runtime_set_observed[11],runtime_set_refresh_count;
#endif
#endif
