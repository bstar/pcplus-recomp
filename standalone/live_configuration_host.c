#include "live_configuration.h"
#include <stdio.h>
#include <string.h>
prm_dos_image live_image;
directory_dos_selection live_selection;
live_configuration_plan live_active,live_candidate;
live_configuration_result live_result;
directory_live_result live_directory_result;
terminal_import_settings live_serial;
modem_import_settings live_modem;
directory_live_plan live_directory;
int main(void)
{
 prm_dos_image original;
 directory_dos_selection selection_before;
 directory_dos_result io;
 live_configuration_plan before;
 if(prm_dos_load("VALID.PRM",&live_image,0)!=PRM_DOS_OK)return 1;
 if(directory_dos_read("VALID.DIR",17,&live_selection,&io)!=DIRECTORY_DOS_OK)return 2;
 memcpy(&original,&live_image,sizeof(original));memcpy(&selection_before,&live_selection,sizeof(selection_before));
 if(live_configuration_decode(&live_image,&live_selection,0,0,0,&live_candidate,&live_result))return 3;
 if(directory_live_read("VALID.PRM","VALID.DIR",17,0,&live_serial,&live_modem,&live_directory,&live_directory_result))return 4;
 if(memcmp(&live_serial,&live_candidate.serial,sizeof(live_serial)) ||
  memcmp(&live_modem,&live_candidate.modem,sizeof(live_modem)) ||
  memcmp(&live_directory,&live_candidate.directory,sizeof(live_directory)))return 5;
 memcpy(&live_active,&live_candidate,sizeof(live_active));
 live_image.bytes[0x1ae]=14;
 if(live_configuration_decode(&live_image,&live_selection,0,15,&live_active,&live_candidate,&live_result))return 6;
 if(live_candidate.change_mask!=LIVE_CHANGE_DISPLAY || live_candidate.serial.normal_attribute!=14)return 7;
 memcpy(&before,&live_candidate,sizeof(before));live_image.bytes[0x198]=2;
 if(live_configuration_decode(&live_image,&live_selection,0,15,&live_active,&live_candidate,&live_result)!=LIVE_CONFIGURATION_DIRECTORY ||
  memcmp(&before,&live_candidate,sizeof(before)))return 8;
 if(memcmp(&selection_before,&live_selection,sizeof(selection_before)))return 9;
 if(prm_dos_load("VALID.PRM",&live_image,0)!=PRM_DOS_OK || memcmp(&original,&live_image,sizeof(original)))return 10;
 puts("LIVE CONFIGURATION PASS");return 0;
}
