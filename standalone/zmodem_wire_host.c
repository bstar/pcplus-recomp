#include "zmodem_wire.h"
#include <stdio.h>
#include <string.h>
static unsigned char input[1024],expected[2060],output[2060],payload[1026];
static zw_decoder s,saved;
static unsigned checks,failures;
static void ck(unsigned good,const char *label)
{++checks;if(!good){++failures;printf("FAIL %u %s\n",checks,label);}}
static unsigned word(FILE *f)
{unsigned lo=(unsigned)fgetc(f);return lo|((unsigned)fgetc(f)<<8);}
int main(void)
{
 FILE *f;unsigned kind,format,control,ending,n,length,i,status,events,vectors=0,scenarios=0;
 f=fopen("VECTORS.BIN","rb");if(!f)return 1;
 while((kind=(unsigned)fgetc(f))!=0xffffU){
  format=(unsigned)fgetc(f);control=(unsigned)fgetc(f);ending=(unsigned)fgetc(f);
  length=word(f);n=word(f);
  if(length>1024 || n>2060 || fread(input,1,length,f)!=length || fread(expected,1,n,f)!=n)return 2;
  memset(output,0xa5,sizeof(output));
  status=kind?zw_data_encode(format,input,length,ending,control,output,sizeof(output)):zw_header_encode(format,input,control,output,sizeof(output));
  ck(status==n && !memcmp(expected,output,n),"independent wire encoder vector");
  ck(output[n]==0xa5,"encoder exact output span");
  memset(output,0xa5,sizeof(output));
  status=kind?zw_data_encode(format,input,length,ending,control,output,n-1):zw_header_encode(format,input,control,output,n-1);
  ck(!status && output[0]==0xa5 && output[n-1]==0xa5,"short output atomic");
  memset(payload,0xa5,sizeof(payload));ck(zw_init(&s,payload+1,1024,control)==0,"initialize");
  s.format=format;if(kind)ck(zw_data(&s)==0,"start data");
  events=0;
  for(i=0;i<n;++i){
   status=zw_feed(&s,expected[i]);
   if(status){++events;ck(status==(kind?ZW_DATA:ZW_HEADER),"decoder event");}
  }
  ck(events==1,"one complete packet");
  ck(kind?(s.count==length && s.ending==ending && !memcmp(payload+1,input,length)):!memcmp(s.header,input,5),"independent wire decoder vector");
  ck(payload[0]==0xa5 && payload[1025]==0xa5,"decoder guards");++vectors;
 }
 fclose(f);
 f=fopen("STREAMS.BIN","rb");if(!f)return 1;
 while((format=(unsigned)fgetc(f))!=0xffffU){
  control=(unsigned)fgetc(f);kind=(unsigned)fgetc(f);length=word(f);n=word(f);ending=word(f);
  if(!length || length>1024 || n>2060 || ending>1024 || fread(expected,1,n,f)!=n || fread(input,1,ending,f)!=ending)return 2;
  memset(payload,0xa5,sizeof(payload));zw_init(&s,payload+1,length,control);s.format=format;if(kind)zw_data(&s);
  events=0;
  for(i=0;i<n;++i){
   status=zw_feed(&s,expected[i]);
   if(status){ck(events<ending && status==input[events],"independent stream event");++events;}
  }
  ck(events==ending,"independent stream event count");
  for(i=length+1;i<sizeof(payload);++i)if(payload[i]!=0xa5)break;
  ck(payload[0]==0xa5 && i==sizeof(payload),"stream capacity guards");++scenarios;
 }
 fclose(f);
 ck(zw_init(&s,(unsigned char *)0xfff0,1024,0)==ZW_ARGUMENT,"near payload wrap");
 ck(zw_init((zw_decoder *)0xfff0,payload,1024,0)==ZW_ARGUMENT,"near state wrap");
 ck(zw_init(&s,(unsigned char *)&s,1,0)==ZW_ARGUMENT,"state payload alias");
 ck(!zw_header_encode(ZW_BIN16,(unsigned char *)0xfffe,0,output,24),"near header wrap");
 ck(!zw_data_encode(ZW_BIN32,(unsigned char *)0xfff0,1024,ZW_CRCW,0,output,2060),"near data wrap");
 ck(!zw_data_encode(ZW_BIN32,input,1024,ZW_CRCW,0,(unsigned char *)0xfff0,2060),"near output wrap");
 zw_init(&s,payload,1024,0);saved=s;
 ck(zw_feed(&s,256)==ZW_ARGUMENT && !memcmp(&s,&saved,sizeof(s)),"bad byte atomic");
 for(i=0;i<5;++i)ck(zw_feed(&s,24)==(i==4?ZW_CANCEL:ZW_MORE),"five CAN cancel");
 ck(zw_feed(&s,'X')==ZW_CANCEL,"cancel sticky");
 printf("%u vectors; %u streams; %u checks; %u failures\n",vectors,scenarios,checks,failures);
 return failures?1:0;
}
