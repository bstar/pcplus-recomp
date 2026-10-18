/* Synthetic test child: edit the mapped mode, then change DOS's shared CWD. */
#include <direct.h>
#include <stdio.h>
int main(int argc,char **argv)
{
 FILE *file;unsigned char mode[2]={1,0};unsigned ok;
 if(argc!=2)return 20;
 file=fopen(argv[1],"r+b");if(!file)return 21;
 ok=!fseek(file,0x1e0L,SEEK_SET) && fwrite(mode,1,2,file)==2;
 if(fclose(file))ok=0;if(!ok)return 22;
 if(chdir("OTHER"))return 23;
 return 0;
}
