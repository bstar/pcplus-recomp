#include "setup_document.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <io.h>
static setup_document doc,before;
static setup_document_result r;
static prm_dos_image disk,original;
static char text[64];
#define CHECK(expression) do {if(!(expression)){printf("FAIL line %u\n",__LINE__);return 1;}++checks;}while(0)
int main(void)
{
 unsigned checks=0;
 memset(&doc,0xa5,sizeof(doc));memcpy(&before,&doc,sizeof(doc));
 CHECK(setup_document_open("MISSING.PRM",&doc,&r)==SETUP_DOCUMENT_LOAD);
 CHECK(!memcmp(&doc,&before,sizeof(doc)));
 CHECK(setup_document_open("SHORT.PRM",&doc,&r)==SETUP_DOCUMENT_LOAD);
 CHECK(!memcmp(&doc,&before,sizeof(doc)));
 CHECK(setup_document_open("CON.PRM",&doc,&r)==SETUP_DOCUMENT_ARGUMENT);
 CHECK(setup_document_open("PRMEDIT.BAK",&doc,&r)==SETUP_DOCUMENT_ARGUMENT);
 CHECK(setup_document_open("../VALID.PRM",&doc,&r)==SETUP_DOCUMENT_ARGUMENT);
 CHECK(setup_document_open("VALID.PRM",&doc,&r)==SETUP_DOCUMENT_OK);
 memcpy(&original,&doc.baseline,sizeof(original));
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_OK);
 CHECK(r.io.bytes_processed==0 && !r.replacement.installed);
 strcpy(text,"65535");CHECK(setup_set(&doc.baseline,&doc.staged,26,text)==SETUP_OK);
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_OK && r.replacement.installed);
 CHECK(!memcmp(&doc.baseline,&doc.staged,sizeof(disk)));
 CHECK(prm_dos_load("VALID.PRM",&disk,0)==PRM_DOS_OK && !memcmp(&disk,&doc.staged,sizeof(disk)));
 CHECK(disk.bytes[0x1a4]==255 && disk.bytes[0x1a5]==255);
 memcpy(&disk,&original,sizeof(disk));disk.bytes[0x1a4]=255;disk.bytes[0x1a5]=255;
 CHECK(!memcmp(&disk,&doc.staged,sizeof(disk)));
 /* External change to an OPAQUE byte must also stop an overwrite. */
 disk.bytes[0x400]^=1;CHECK(prm_dos_save("VALID.PRM",&disk,0)==PRM_DOS_OK);
 strcpy(text,"350");CHECK(setup_set(&doc.baseline,&doc.staged,26,text)==SETUP_OK);
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_CHANGED && !r.replacement.installed);
 CHECK(prm_dos_load("VALID.PRM",&original,0)==PRM_DOS_OK && !memcmp(&disk,&original,sizeof(disk)));
 CHECK(setup_document_open("VALID.PRM",&doc,&r)==SETUP_DOCUMENT_OK);
 strcpy(text,"350");CHECK(setup_set(&doc.baseline,&doc.staged,26,text)==SETUP_OK);
 CHECK(_dos_setfileattr("VALID.PRM",_A_RDONLY)==0);
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_REPLACE && !r.replacement.installed && !doc.locked);
 CHECK(_dos_setfileattr("VALID.PRM",_A_NORMAL)==0);
 CHECK(prm_dos_save("PRMEDIT.BAK",&disk,0)==PRM_DOS_OK);
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_REPLACE && r.replacement.status==PRM_REPLACE_CONFLICT);
 CHECK(prm_dos_load("PRMEDIT.BAK",&original,0)==PRM_DOS_OK && !memcmp(&disk,&original,sizeof(disk)));
 CHECK(remove("PRMEDIT.BAK")==0);
 CHECK(prm_dos_save("PRMEDIT.$$$",&disk,0)==PRM_DOS_OK);
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_REPLACE && r.replacement.status==PRM_REPLACE_STAGE_OPEN);
 CHECK(prm_dos_load("PRMEDIT.$$$",&original,0)==PRM_DOS_OK && !memcmp(&disk,&original,sizeof(disk)));
 CHECK(remove("PRMEDIT.$$$")==0);
 doc.staged.bytes[0x198]=2;
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_INVALID && r.bad_field==5);
 doc.staged.bytes[0x198]=0;doc.locked=1;
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_LOCKED);
 doc.locked=0;
 CHECK(remove("VALID.PRM")==0);
 CHECK(setup_document_save(&doc,&r)==SETUP_DOCUMENT_LOAD);
 CHECK(access("VALID.PRM",0)!=0);
 CHECK(prm_dos_save("VALID.PRM",&disk,0)==PRM_DOS_OK);
 printf("SETUP DOCUMENT PASS %u checks\n",checks);return 0;
}
