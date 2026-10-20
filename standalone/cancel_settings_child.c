/* Explicit synthetic settings child for parent confirmation/cancel tests. */
#include <stdio.h>
int main(void)
{
 unsigned char bytes[1264];FILE *f=fopen("PREP.PRM","rb");
 if(!f)return 1;
 if(fread(bytes,1,sizeof(bytes),f)!=sizeof(bytes)||fgetc(f)!=EOF){fclose(f);return 2;}
 if(fclose(f))return 3;f=fopen("TEST.PRM","wb");if(!f)return 4;
 if(fwrite(bytes,1,sizeof(bytes),f)!=sizeof(bytes)){fclose(f);return 5;}
 return fclose(f)?6:0;
}
