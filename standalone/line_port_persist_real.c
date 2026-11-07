#include "../src/line_port/persist.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static unsigned checks,failures;
static unsigned char expected[10],replacement[10];
static directory_replace_result result;
static void check(int good){++checks;if(!good){++failures;printf("FAIL %u\n",checks);}}
int main(void)
{
 unsigned i;FILE *file;directory_replace_result prior;
 for(i=0;i<10;++i){expected[i]=(unsigned char)(i*17+3);replacement[i]=expected[i]^0x5a;}
 check(!line_port_persist("C:\\SUB\\TEST.PRM",expected,replacement,&result));
 check(result.installed && !result.stage_exists && !result.original_in_backup && result.source_bytes==1264 && result.bytes_processed==1264);
 check(line_port_persist("C:\\SUB\\TEST.PRM",expected,replacement,&result)==DIRECTORY_REPLACE_STALE);
 check(!result.installed && !result.stage_exists && !result.original_in_backup);
 check(line_port_persist("C:\\SUB\\SHORT.PRM",expected,replacement,&result)==DIRECTORY_REPLACE_SIZE);
 check(!result.stage_exists && !result.installed);
 check(line_port_persist("C:\\SUB\\LONG.PRM",expected,replacement,&result)==DIRECTORY_REPLACE_SIZE);
 check(!result.stage_exists && !result.installed);
 check(line_port_persist("C:\\SUB\\ABSENT.PRM",expected,replacement,&result)==DIRECTORY_REPLACE_INSPECT);
 check(!_dos_setfileattr("C:\\SUB\\READONLY.PRM",_A_RDONLY));
 check(line_port_persist("C:\\SUB\\READONLY.PRM",expected,replacement,&result)==DIRECTORY_REPLACE_INSPECT);
 check(!_dos_setfileattr("C:\\SUB\\READONLY.PRM",_A_NORMAL));
 file=fopen("C:\\SUB\\PCPSTG.$$$","wb");check(file!=0);
 check(fputs("OWNED BY OTHER",file)>=0);check(!fclose(file));
 check(line_port_persist("C:\\SUB\\TEST.PRM",replacement,expected,&result)==DIRECTORY_REPLACE_CONFLICT);
 check(!remove("C:\\SUB\\PCPSTG.$$$"));
 file=fopen("C:\\SUB\\PCPBAK.$$$","wb");check(file!=0);
 check(fputs("KEEP RECOVERY",file)>=0);check(!fclose(file));
 check(line_port_persist("C:\\SUB\\TEST.PRM",replacement,expected,&result)==DIRECTORY_REPLACE_CONFLICT);
 check(!remove("C:\\SUB\\PCPBAK.$$$"));
 memset(&result,0xcc,sizeof(result));prior=result;
 check(line_port_persist("TEST.PRM",expected,replacement,&result)==DIRECTORY_REPLACE_ARGUMENT);
 check(!memcmp(&prior,&result,sizeof(result)));
 check(line_port_persist("C:\\SUB\\..\\TEST.PRM",expected,replacement,&result)==DIRECTORY_REPLACE_ARGUMENT);
 check(line_port_persist("C:\\SUB\\NUL.PRM",expected,replacement,&result)==DIRECTORY_REPLACE_ARGUMENT);
 check(line_port_persist("C:\\SUB\\TEST.PRM",expected,replacement,(directory_replace_result *)expected)==DIRECTORY_REPLACE_ARGUMENT);
 check(line_port_persist("C:\\SUB\\TEST.PRM",replacement,replacement,0)==0);
 printf("REAL %u checks %u failures\n",checks,failures);return failures?1:0;
}
