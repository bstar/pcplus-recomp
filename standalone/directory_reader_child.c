/* Real EXEC witness: inspect the supplied handle before opening any file. */
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv)
{
 unsigned status,count=0,report[3];unsigned char value=0;FILE *file;
 if(argc!=3)return 2;
 status=_dos_read(atoi(argv[1]),&value,1,&count);
 report[0]=status;report[1]=count;report[2]=value;
 file=fopen("CHILD.BIN","wb");if(!file)return 3;
 if(fwrite(report,2,3,file)!=3||fclose(file))return 4;
 if(status!=(unsigned)atoi(argv[2]))return 5;
 return status?(count!=0):(count!=1||value!=11);
}
