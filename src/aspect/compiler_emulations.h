/* Original compiler kind32 names in native selector order. Compiler only:
 * accepting a name does not establish an implemented runtime emulation. */
#ifndef ASPECT_COMPILER_EMULATIONS_H
#define ASPECT_COMPILER_EMULATIONS_H
#include <string.h>
static int aspect_compiler_emulation(const char *name)
{
 static const char *names[]={"tty","vt52","vt100","vt102","vt220","vt320","ansi","ibmpc","wyse75","att605","att4410","tv922","h19","ibm3101","ibm3161","dgd100","dgd200","dgd210","adds60","adds90","adm3","adm5","adm31","esprit3","ibm3270","tv910","tv912","tv920","tv925","tv950","tv955","wyse50","wyse100"};
 unsigned i;
 for(i=0;i<sizeof(names)/sizeof(names[0]);++i)if(!strcmp(name,names[i]))return (int)i;
 return -1;
}
#endif
