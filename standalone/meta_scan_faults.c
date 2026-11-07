#include <string.h>
#include "meta_scan_fs.h"
#include "meta_scan_faults.h"
extern unsigned __cdecl meta_scan_real_first(const char *,struct find_t *);
extern unsigned __cdecl meta_scan_real_next(struct find_t *);
unsigned scan_fault,scan_calls,scan_firsts,scan_nexts;
void scan_reset(unsigned mode){scan_fault=mode;scan_calls=scan_firsts=scan_nexts=0;}
unsigned __cdecl meta_scan_fs_first(const char *p,struct find_t *f)
{
 unsigned e;++scan_calls;++scan_firsts;if(scan_fault==1)return 5;
 e=meta_scan_real_first(p,f);if(!e){
  if(scan_fault==3)strcpy(f->name,"BAD.XXX");
  if(scan_fault==4)memcpy(f->name,"ABCDEFGH.KEYX",13);
  if(scan_fault==5)f->attrib|=_A_SUBDIR;
  if(scan_fault==6)strcpy(f->name,"B/D.KEY");
 }return e;
}
unsigned __cdecl meta_scan_fs_next(struct find_t *f)
{++scan_calls;++scan_nexts;if(scan_fault==2)return 5;return meta_scan_real_next(f);}
