/* Real DOS synthetic drive; no original or installed files. */
#include "download_file.h"
#include <dos.h>
#include <direct.h>
#include <stdio.h>
#include <string.h>
static unsigned failures,cases;
static unsigned char payload[32768];
static void check(int yes,const char *name)
{ ++cases;printf("%s %s\n",yes?"PASS":"FAIL",name);if(!yes)++failures; }
static int text(const char *path,const char *value)
{ FILE *f=fopen(path,"wb");unsigned n;if(!f)return 0;n=fwrite(value,1,strlen(value),f);return !fclose(f) && n==strlen(value); }
int main(void)
{
 unsigned i,attr;char byte=0;FILE *f;
 for(i=0;i<sizeof(payload);++i)payload[i]=(unsigned char)(i*37+19);
 check(transfer_download_begin("RESULT.BIN","STAGE.TMP")==TF_OK,"exclusive new stream opens");
 check(transfer_download_append(payload,32768U)==TF_OK && transfer_download_append(payload,32768U)==TF_OK && transfer_download_append(payload,137)==TF_OK && transfer_download_result.bytes_written==65673UL,"actual DOS binary writes cross64K file boundary");
 check(transfer_download_finish()==TF_OK && transfer_download_result.state==TF_INSTALLED && !transfer_download_result.stage_exists,"successful close precedes actual DOS rename");
 check(_dos_getfileattr("STAGE.TMP",&attr)==2,"installed stage name removed");
 check(transfer_download_begin("RESULT.BIN","STAGE.TMP")==TF_CONFLICT && _dos_getfileattr("STAGE.TMP",&attr)==2,"existing target preserved");
 check(text("KEEP.TMP","preexisting stage"),"prepare foreign stage");
 check(transfer_download_begin("NEW.BIN","KEEP.TMP")==TF_CREATE && transfer_download_abort()==TF_OK,"existing stage never becomes owned");
 check(transfer_download_begin("EMPTY.BIN","EMPTY.TMP")==TF_OK && transfer_download_append(0,0)==TF_OK && transfer_download_finish()==TF_OK,"empty binary file installs");
 check(transfer_download_begin("CANCEL.BIN","CANCEL.TMP")==TF_OK && transfer_download_append(payload,1024)==TF_OK && transfer_download_abort()==TF_OK && _dos_getfileattr("CANCEL.TMP",&attr)==2 && _dos_getfileattr("CANCEL.BIN",&attr)==2,"cancel closes and deletes owned partial without target");
 check(transfer_download_begin("RACE.BIN","RACE.TMP")==TF_OK && transfer_download_append(payload,1024)==TF_OK && text("RACE.BIN","competing target"),"prepare concurrent destination after exclusive stage");
 check(transfer_download_finish()==TF_INSTALL && transfer_download_result.state==TF_CLOSED && transfer_download_result.stage_exists,"actual DOS rename refuses overwrite and retains closed stage");
 check(transfer_download_abort()==TF_OK && _dos_getfileattr("RACE.TMP",&attr)==2,"explicit abort removes only owned stage after install failure");
 f=fopen("RACE.BIN","rb");if(f){fread(&byte,1,1,f);fclose(f);}check(byte=='c',"competing destination remains intact");
 check(_mkdir("DATA")==0 && transfer_download_begin("c:/data/nested.bin","C:\\DATA\\PART.TMP")==TF_OK && transfer_download_append(payload,257)==TF_OK && transfer_download_finish()==TF_OK,"real nested absolute DOS target installs in selected parent");
 check(transfer_download_begin("C:REL.BIN","C:REL.TMP")==TF_OK && transfer_download_append(payload,3)==TF_OK && transfer_download_finish()==TF_OK,"real drive-relative paths retain current DOS directory");
 printf("CASES %u\n",cases);return failures?1:0;
}
