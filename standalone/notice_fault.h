#ifndef NOTICE_FAULT_DIAGNOSTIC_H
#define NOTICE_FAULT_DIAGNOSTIC_H
void __far __cdecl notice_fault_prepare(void);
unsigned __far __cdecl notice_fault_run(const char *,unsigned);
unsigned __far __cdecl notice_fault_save(void);
const char * __far __cdecl notice_fault_request(void);
unsigned __far __cdecl notice_fault_runtime_run(const char *,unsigned);
void __cdecl notice_fault_raise(unsigned);
#endif
