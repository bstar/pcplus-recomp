/* Actual DOS filesystem contract checks, confined to a synthetic test drive. */
#include "prm_replace.h"
#include "prm_replace_fs.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static prm_dos_image image,loaded;
static prm_replace_result result;
static unsigned failures;
static void check(int yes,const char *s){printf("%s %s\n",yes ? "PASS" : "FAIL",s);if(!yes)failures++;}
static int write_text(const char *path,const char *text)
{FILE *f=fopen(path,"wb");unsigned n;if(!f)return 0;n=fwrite(text,1,strlen(text),f);return !fclose(f) && n==strlen(text);}
static int has_text(const char *path,const char *text)
{char bytes[64];unsigned n;FILE *f=fopen(path,"rb");if(!f)return 0;n=fread(bytes,1,sizeof(bytes),f);fclose(f);return n==strlen(text) && !memcmp(bytes,text,n);}
int main(void)
{
 unsigned i,attributes;
 for(i=0;i<1264;i++)image.bytes[i]=(unsigned char)(i*29+5);
 check(write_text("TARGET.PRM","Old opaque configuration"),"create synthetic old target");
 check(prm_dos_replace("TARGET.PRM","STAGE.TMP","BACKUP.BAK",&image,&result)==PRM_REPLACE_OK && result.installed,"replace existing opaque target");
 check(prm_dos_load("TARGET.PRM",&loaded,0)==PRM_DOS_OK && !memcmp(&loaded,&image,sizeof(image)),"new target has exact source image");
 check(_dos_getfileattr("STAGE.TMP",&attributes)==2 && _dos_getfileattr("BACKUP.BAK",&attributes)==2,"success removes stage and backup");
 check(write_text("CAND.TMP","keep stage"),"create preexisting stage fixture");
 check(prm_dos_replace("TARGET.PRM","CAND.TMP","CAND.BAK",&image,&result)==PRM_REPLACE_STAGE_OPEN && has_text("CAND.TMP","keep stage"),"exclusive stage creation preserves existing file");
 check(write_text("CAND.BAK","keep backup"),"create preexisting backup fixture");
 check(prm_dos_replace("TARGET.PRM","STAGE.TMP","CAND.BAK",&image,&result)==PRM_REPLACE_CONFLICT && has_text("CAND.BAK","keep backup"),"existing backup prevents replacement");
 check(prm_dos_replace("NEW.PRM","STAGE.TMP","BACKUP.BAK",&image,0)==PRM_REPLACE_OK && prm_dos_load("NEW.PRM",&loaded,0)==PRM_DOS_OK && !memcmp(&loaded,&image,sizeof(image)),"new target installation and optional result pointer");
 check(write_text("FROM.TMP","source") && write_text("TO.TMP","destination"),"create real DOS rename collision fixtures");
 check(prm_replace_rename("FROM.TMP","TO.TMP")!=0 && has_text("FROM.TMP","source") && has_text("TO.TMP","destination"),"DOS rename never overwrites existing destination");
 check(prm_replace_delete("FROM.TMP")==0 && _dos_getfileattr("FROM.TMP",&attributes)==2,"owned scratch delete uses actual DOS error contract");
 if(!_dos_getfileattr("TARGET.PRM",&attributes) && !_dos_setfileattr("TARGET.PRM",attributes|_A_RDONLY)){
  check(prm_dos_replace("TARGET.PRM","STAGE.TMP","BACKUP.BAK",&image,&result)==PRM_REPLACE_INSPECT && !result.installed,"read-only target rejected");
  _dos_setfileattr("TARGET.PRM",attributes);
 }else printf("SKIP mapped filesystem read-only attribute\n");
 check(prm_dos_replace("target.prm","TARGET.PRM","BACKUP.BAK",&image,&result)==PRM_REPLACE_ARGUMENT,"case alias rejected");
 check(prm_dos_replace("TARGET.PRM","STAGE.TMP","BACKUP.BAK",0,&result)==PRM_REPLACE_ARGUMENT,"null source rejected");
 return failures ? 1 : 0;
}
