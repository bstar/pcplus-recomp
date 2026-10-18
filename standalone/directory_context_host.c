#include "directory_live.h"
#include "directory_actions.h"
#include "live_configuration.h"
#include <stdio.h>
#include <string.h>
static directory_live_context retained,fresh,retained_before;
static directory_dos_selection source;
static directory_dos_result io;
static directory_live_result result;
static directory_replace_result accounting;
static terminal_import_settings serial,serial_before;
static modem_import_settings modem,modem_before;
static directory_live_plan plan,plan_before;
static live_configuration_plan candidate;
static live_configuration_result candidate_result;
static prm_dos_image image;
static unsigned char changed_header[250],record_before[114];
#define CHECK(expression) do {if(!(expression)){printf("FAIL line %u\n",__LINE__);return 1;}++checks;}while(0)
int main(void)
{
 unsigned checks=0;FILE *file;
 CHECK(prm_dos_load("VALID.PRM",&image,0)==PRM_DOS_OK);
 CHECK(directory_dos_read("FROZEN.DIR",17,&source,&io)==DIRECTORY_DOS_OK);
 CHECK(directory_live_read_context("VALID.PRM","STATE.DIR",17,1,&serial,&modem,&plan,&result,&retained)==DIRECTORY_LIVE_OK);
 CHECK(!memcmp(&retained.selection,&source,sizeof(source)));
 CHECK(retained.codes==1 && !strcmp(retained.prm_path,"VALID.PRM") && !strcmp(retained.directory_path,"STATE.DIR"));
 CHECK(!strcmp((const char *)plan.target,"9,55-"));
 CHECK(directory_live_context_matches(&retained,"valid.prm","state.dir",17,1)==1);
 CHECK(!directory_live_context_matches(&retained,"OTHER.PRM","STATE.DIR",17,1));
 CHECK(!directory_live_context_matches(&retained,"VALID.PRM","STATE.DIR",18,1));
 CHECK(!directory_live_context_matches(&retained,"VALID.PRM","STATE.DIR",17,0));
 memset(changed_header,0,sizeof(changed_header));changed_header[0]='X';changed_header[25]='Y';
 file=fopen("STATE.DIR","r+b");CHECK(file!=0);
 CHECK(fwrite(changed_header,1,250,file)==250);CHECK(fclose(file)==0);
 /* Source file has changed. The retained selection still supplies old codes;
  * the pure candidate API neither reloads nor opens that source. */
 CHECK(live_configuration_decode(&image,&retained.selection,retained.codes,0,0,&candidate,&candidate_result)==0);
 CHECK(!strcmp((const char *)candidate.directory.target,"9,55-"));
 CHECK(directory_live_read_context("VALID.PRM","STATE.DIR",17,1,&serial,&modem,&plan,&result,&fresh)==DIRECTORY_LIVE_OK);
 CHECK(!strcmp((const char *)plan.target,"X55Y") && !memcmp(fresh.selection.header,changed_header,250));
 CHECK(!memcmp(&retained.selection,&source,sizeof(source)));
 memcpy(record_before,plan.record,114);
 CHECK(directory_save_accounting("STATE.DIR",17,plan.record,2026,10,18,1,&accounting)==DIRECTORY_REPLACE_OK && accounting.installed);
 CHECK(memcmp(plan.record,record_before,114)!=0);
 CHECK(!memcmp(retained.selection.record,source.record,114) && !memcmp(fresh.selection.record,source.record,114));
 memcpy(&serial_before,&serial,sizeof(serial));memcpy(&modem_before,&modem,sizeof(modem));memcpy(&plan_before,&plan,sizeof(plan));
 memcpy(&retained_before,&retained,sizeof(retained));
 CHECK(directory_live_read_context("VALID.PRM","SHORT.DIR",17,1,&serial,&modem,&plan,&result,&retained)==DIRECTORY_LIVE_DIRECTORY_IO);
 CHECK(!memcmp(&retained,&retained_before,sizeof(retained)));
 CHECK(!memcmp(&serial,&serial_before,sizeof(serial)) && !memcmp(&modem,&modem_before,sizeof(modem)) && !memcmp(&plan,&plan_before,sizeof(plan)));
 printf("DIRECTORY CONTEXT PASS %u checks\n",checks);return 0;
}
