#include <string.h>
#include <dos.h>
#include "../src/capture/capture_fs.h"
#include "meta_resource_faults.h"
extern unsigned meta_resource_real_canonical(const char *,char *);
extern unsigned meta_resource_real_attributes(const char *,unsigned *);
unsigned resource_fault,resource_calls,resource_canonical_calls,resource_attribute_calls;
void resource_reset(unsigned mode){resource_fault=mode;resource_calls=resource_canonical_calls=resource_attribute_calls=0;}
unsigned capture_fs_canonical(const char *path,char *out)
{++resource_calls;++resource_canonical_calls;if(resource_fault==1)return 5;if(resource_fault==3){memset(out,'A',128);return 0;}if(resource_fault==4){strcpy(out,"C:\\A");return 0;}return meta_resource_real_canonical(path,out);}
unsigned capture_fs_attributes(const char *path,unsigned *attr)
{unsigned e;++resource_calls;++resource_attribute_calls;if(resource_fault==2)return 5;e=meta_resource_real_attributes(path,attr);if(!e && resource_fault==5)*attr|=_A_SUBDIR;return e;}
