/* Keep the ordinary CLI in _TEXT; all added observation/run work is banked. */
#include "runtime.h"
#include "notice_fault.h"
#define aspect_runtime_run notice_fault_run
#define main ordinary_main
#include "../src/aspect/runner.c"
#undef main
#undef aspect_runtime_run
extern unsigned notice_fault_report[];
int main(int argc,char **argv)
{
 int status;
 notice_fault_prepare();status=ordinary_main(argc,argv);
 notice_fault_report[28]=(unsigned)status;
 if(notice_fault_save())return 90;
 return status;
}
