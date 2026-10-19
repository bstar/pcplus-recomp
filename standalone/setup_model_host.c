#include "setup_model.h"
#include "transfer_import.h"
#include <stdio.h>
#include <string.h>
prm_dos_image setup_baseline,setup_staged;
char setup_text[SETUP_TEXT_SIZE];
unsigned setup_bad;
transfer_import_settings setup_transfer;
int main(void)
{
 unsigned i;
 if(prm_dos_load("VALID.PRM",&setup_baseline,0)!=PRM_DOS_OK)return 1;
 memcpy(&setup_staged,&setup_baseline,sizeof(setup_staged));
 if(setup_validate(&setup_staged,&setup_bad)!=SETUP_OK)return 2;
 if(transfer_import_decode(&setup_staged,&setup_transfer)!=TRANSFER_IMPORT_OK)return 9;
 for(i=0;i<SETUP_FIELD_COUNT;++i){
  if(!setup_field(i) || setup_get(&setup_baseline,i,setup_text,sizeof(setup_text))!=SETUP_OK)return 3;
  if(setup_set(&setup_baseline,&setup_staged,i,setup_text)!=SETUP_OK)return 4;
  if(memcmp(&setup_baseline,&setup_staged,sizeof(setup_staged)))return 5;
 }
 strcpy(setup_text,"115200");
 if(setup_set(&setup_baseline,&setup_staged,1,setup_text)!=SETUP_OK)return 6;
 if(setup_staged.bytes[2]!=8 || setup_staged.bytes[3]!=0)return 7;
 strcpy(setup_text,"65536");
 if(setup_set(&setup_baseline,&setup_staged,26,setup_text)!=SETUP_VALUE)return 8;
 puts("SETUP MODEL PASS");return 0;
}
