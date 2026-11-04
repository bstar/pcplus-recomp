/* Synthetic DOS regression children. Never a replacement for real PRMEDIT. */
#include <direct.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv)
{
 FILE *log;
 char current[68];
#ifdef CWD_CHANGE
 char before[68];
 if(!getcwd(before,sizeof(before)) || chdir("D:\\OTHER") || !getcwd(current,sizeof(current)))return 20;
 if(mkdir("WITNESS"))return 21;
 log=fopen("D:\\CWDMOVED.TXT","wt");if(!log)return 22;
 fprintf(log,"before=%s\nafter=%s\n",before,current);
 if(fclose(log))return 23;
 (void)argc;(void)argv;return 0;
#elif defined(CWD_DECOY)
 (void)argc;(void)argv;(void)current;
 log=fopen("D:\\DECOY.TXT","wt");if(!log)return 24;
 fputs("wrong helper executed\n",log);return fclose(log)?25:0;
#else
 FILE *source,*copy;
 unsigned char buffer[128];unsigned n,total=0;
 if(argc!=2 || !getcwd(current,sizeof(current)))return 26;
 log=fopen("D:\\SETUP.TXT","wt");if(!log)return 27;
 fprintf(log,"program=%s\nargument=%s\ncwd=%s\n",argv[0],argv[1],current);
 if(fclose(log))return 28;
 source=fopen(argv[1],"rb");if(!source)return 29;
 copy=fopen("D:\\PRMSEEN.BIN","wb");if(!copy){fclose(source);return 30;}
 while((n=fread(buffer,1,sizeof(buffer),source))!=0){
  total+=n;if(fwrite(buffer,1,n,copy)!=n){fclose(source);fclose(copy);return 31;}
 }
 n=ferror(source);if(fclose(source))n=1;if(fclose(copy))n=1;
 return n || total!=1264?32:0;
#endif
}
