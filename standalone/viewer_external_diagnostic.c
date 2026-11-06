#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "../src/filesystem/viewer_external.h"
static unsigned char prm[1264],before[1264];
static char parameters[49],output[116],saved[116];
static unsigned checks,failures;
#define CHECK(x) do{checks++;if(!(x)){failures++;printf("FAIL line=%u check=%u\n",__LINE__,checks);}}while(0)
static void test(unsigned n,unsigned m,unsigned capacity,unsigned want)
{
 unsigned i,length=0xaaaa,status;char expected[114];
 memset(prm,0xa5,sizeof(prm));memset(parameters,'F',sizeof(parameters));
 for(i=0;i<n;++i)prm[VIEWER_EXTERNAL_PRM_OFFSET+i]=(unsigned char)(i%2?'Q':0x80);
 if(n<65)prm[VIEWER_EXTERNAL_PRM_OFFSET+n]=0;
 if(m<49)parameters[m]=0;
 memset(output,0x5a,sizeof(output));memcpy(saved,output,sizeof(output));memcpy(before,prm,sizeof(prm));
 status=viewer_external_build(prm,parameters,output+1,capacity,&length);CHECK(status==want);
 CHECK(!memcmp(prm,before,sizeof(prm)));CHECK(output[0]==0x5a&&output[115]==0x5a);
 if(want){CHECK(length==0xaaaa);CHECK(!memcmp(output,saved,sizeof(output)));}
 else{
  for(i=0;i<n;++i)expected[i]=(char)prm[VIEWER_EXTERNAL_PRM_OFFSET+i];
  expected[n]=' ';for(i=0;i<m;++i)expected[n+1+i]='F';expected[n+1+m]=0;
  CHECK(length==n+1+m);CHECK(!memcmp(output+1,expected,length+1));
  CHECK(!memcmp(output+length+2,saved+length+2,sizeof(output)-length-2));
 }
}
int main(void)
{
 unsigned n,m,capacity,want,length=0xaaaa;FILE *f;
 for(n=0;n<=65;++n)for(m=0;m<=49;++m)for(capacity=1;capacity<=114;capacity+=113){
  want=n==65?VEXT_CONFIG:!n?VEXT_DISABLED:m==49?VEXT_PARAMETERS:n+1+m+1>capacity?VEXT_CAPACITY:VEXT_OK;
  test(n,m,capacity,want);
 }
 memset(prm,0,sizeof(prm));prm[VIEWER_EXTERNAL_PRM_OFFSET]='X';parameters[0]=0;memset(output,0x5a,sizeof(output));
 CHECK(viewer_external_build(prm,parameters,output,0,&length)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(prm,parameters,output,115,&length)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(prm,parameters,(char *)prm,114,&length)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(prm,parameters,parameters,49,&length)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(prm,parameters,output,114,(unsigned *)output)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(prm,parameters,output,114,(unsigned *)prm)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(MK_FP(0x5000,0xff00),parameters,output,114,&length)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(prm,MK_FP(0xffff,0x10),output,114,&length)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(prm,parameters,MK_FP(0x5000,0xfff0),114,&length)==VEXT_ARGUMENT);
 CHECK(viewer_external_build(prm,parameters,output,114,MK_FP(0x5000,0xffff))==VEXT_ARGUMENT);
 CHECK(length==0xaaaa&&output[0]==0x5a);
 f=fopen("RESULT.TXT","wb");if(!f)return 20;fprintf(f,"%u %u\r\n",checks,failures);if(fclose(f))return 21;
 printf("%u checks %u failures\n",checks,failures);return failures?1:0;
}
