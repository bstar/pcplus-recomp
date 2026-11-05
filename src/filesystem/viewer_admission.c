#include "viewer_file_backend.h"
#include "../capture/capture_file.h"
/* Build alongside the near capture validator (CONFIG_CODE in the terminal).
 * The claim/unclaim entrypoints are already far. Token is never dereferenced. */
unsigned __far __cdecl viewer_admit_validate(const char *path)
{return capture_file_validate_path(path,0);}
unsigned __far __cdecl viewer_admit_claim(const char *path,void *token)
{return capture_file_claim(path,token);}
unsigned __far __cdecl viewer_admit_release(void *token)
{return capture_file_unclaim(token);}
