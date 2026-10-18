/* Real DOS-file tests; every path is within a synthetic test drive. */
#include "prm_dos.h"
#include <stdio.h>
#include <string.h>
#include <dos.h>
static prm_dos_image image,original,loaded;
static prm_dos_result result;
static unsigned failures=0;
static void check(int condition,const char *name)
{ printf("%s %s\n",condition ? "PASS" : "FAIL",name);if(!condition)failures++; }
int main(void)
{
 unsigned i,attributes;
 FILE *file;
 for(i=0;i<PRM_DOS_IMAGE_SIZE;i++)image.bytes[i]=(unsigned char)(i*17U+3U);
 original=image;
 check(prm_dos_save("ROUND.PRM",&image,&result)==PRM_DOS_OK && result.bytes_processed==PRM_DOS_IMAGE_SIZE,"save exact synthetic bytes");
 memset(&loaded,0xa5,sizeof(loaded));
 check(prm_dos_load("ROUND.PRM",&loaded,&result)==PRM_DOS_OK && memcmp(&loaded,&image,sizeof(image))==0,"load exact synthetic bytes");
 check(prm_dos_load("ROUND.PRM",&loaded,0)==PRM_DOS_OK,"optional result pointer");
 check(prm_dos_load("MISSING.PRM",&loaded,&result)==PRM_DOS_OPEN && result.dos_error!=0 && memcmp(&loaded,&image,sizeof(image))==0,"missing read leaves destination unchanged");
 check(prm_dos_load("SHORT.PRM",&loaded,&result)==PRM_DOS_SIZE && result.bytes_processed==17 && memcmp(&loaded,&image,sizeof(image))==0,"short read leaves destination unchanged");
 check(prm_dos_load("LONG.PRM",&loaded,&result)==PRM_DOS_SIZE && result.bytes_processed==1265 && memcmp(&loaded,&image,sizeof(image))==0,"oversized read leaves destination unchanged");
 check(prm_dos_load("EMPTY.PRM",&loaded,&result)==PRM_DOS_SIZE && memcmp(&loaded,&image,sizeof(image))==0,"empty read leaves destination unchanged");
 check(prm_dos_save("NO_DIR\\FAIL.PRM",&image,&result)==PRM_DOS_OPEN && result.dos_error!=0,"save missing-directory failure");
 check(prm_dos_save(".",&image,&result)==PRM_DOS_OPEN,"save directory failure");
 check(prm_dos_load(0,&loaded,&result)==PRM_DOS_ARGUMENT && prm_dos_save("",&image,&result)==PRM_DOS_ARGUMENT,"argument validation");
 for(i=0;i<48;i++)if(prm_dos_load("SHORT.PRM",&loaded,&result)!=PRM_DOS_SIZE)break;
 check(i==48 && prm_dos_load("ROUND.PRM",&loaded,&result)==PRM_DOS_OK,"repeated failures release handles");
 check(memcmp(&image,&original,sizeof(image))==0,"source remains unchanged");
 file=fopen("READONLY.PRM","wb");
 if(file){fwrite(image.bytes,1,sizeof(image),file);fclose(file);}
 if(file && !_dos_getfileattr("READONLY.PRM",&attributes) && !_dos_setfileattr("READONLY.PRM",attributes|_A_RDONLY)){
  check(prm_dos_save("READONLY.PRM",&image,&result)==PRM_DOS_OPEN,"read-only save rejection");
  _dos_setfileattr("READONLY.PRM",attributes);
 }else printf("SKIP DOS mapped filesystem does not support read-only attribute\n");
 return failures ? 1 : 0;
}
