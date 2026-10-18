#include "setup_document.h"
#include "prm_replace_fs.h"
#include <stdio.h>
#include <string.h>
#include <io.h>
static setup_document doc;
static setup_document_result r;
static prm_dos_image image;
static unsigned fail_cleanup;
unsigned setup_fault_delete(const char *path)
{
 if(fail_cleanup && !strcmp(path,"PRMEDIT.BAK"))return 5;
 return prm_replace_delete(path);
}
int main(void)
{
 char text[64];
 if(setup_document_open("VALID.PRM",&doc,&r)!=SETUP_DOCUMENT_OK)return 1;
 strcpy(text,"65535");if(setup_set(&doc.baseline,&doc.staged,26,text)!=SETUP_OK)return 2;
 fail_cleanup=1;
 if(setup_document_save(&doc,&r)!=SETUP_DOCUMENT_REPLACE ||
  r.replacement.status!=PRM_REPLACE_CLEANUP || !r.replacement.installed ||
  !r.replacement.original_in_backup || r.replacement.stage_exists ||
  !doc.locked || r.replacement.cleanup_error!=5)return 3;
 if(memcmp(&doc.baseline,&doc.staged,sizeof(image)))return 4;
 if(prm_dos_load("VALID.PRM",&image,0)!=PRM_DOS_OK || memcmp(&image,&doc.staged,sizeof(image)))return 5;
 if(access("PRMEDIT.BAK",0))return 6;
 strcpy(text,"350");if(setup_set(&doc.baseline,&doc.staged,26,text)!=SETUP_OK)return 7;
 if(setup_document_save(&doc,&r)!=SETUP_DOCUMENT_LOCKED)return 8;
 if(prm_dos_load("VALID.PRM",&image,0)!=PRM_DOS_OK || image.bytes[0x1a4]!=255 || image.bytes[0x1a5]!=255)return 9;
 puts("SETUP RECOVERY PASS");return 0;
}
