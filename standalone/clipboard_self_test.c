#include "clipboard.h"
#include <string.h>
unsigned clipboard_test_checks=0,clipboard_test_failures=0;
static void check(unsigned yes)
{++clipboard_test_checks;if(!yes)++clipboard_test_failures;}
static clipboard_state list,saved;
static unsigned char packet[200],row[132];
static unsigned n,first,past;
unsigned __cdecl clipboard_self_test(void)
{
 unsigned i,status;char name[13],input[13];
 clipboard_test_checks=clipboard_test_failures=0;
 memset(&list,0xa5,sizeof(list));check(clip_initialize(&list)==CLIP_OK && list.count==0 && list.separator==13);
 check(clip_change(&list,CLIP_ADD,0,"foo.zip   ")==CLIP_OK && !strcmp(list.names[0],"FOO.ZIP"));
 saved=list;check(clip_change(&list,CLIP_ADD,0,"fOo.ZiP")==CLIP_DUPLICATE && !memcmp(&list,&saved,sizeof(list)));
 check(clip_change(&list,CLIP_ADD,0,"two.arj")==CLIP_OK);
 check(clip_change(&list,CLIP_EDIT,1,"FOO.ZIP")==CLIP_OK && list.count==2 && !strcmp(list.names[0],list.names[1]));
 check(clip_change(&list,CLIP_EDIT,0,"lower.zip  ")==CLIP_OK && !strcmp(list.names[0],"lower.zip"));
 check(clip_change(&list,CLIP_ADD,0,"lower.zip")==CLIP_OK && list.count==3 && !strcmp(list.names[2],"LOWER.ZIP"));
 check(clip_change(&list,CLIP_EDIT,1,"")==CLIP_OK && list.count==3 && !list.names[1][0]);
 check(clip_change(&list,CLIP_TAG,2,0)==CLIP_OK && list.tags[2]==16);
 check(clip_prepare(&list,CLIP_TAGGED,packet,sizeof(packet),&n)==CLIP_OK && n==11 && !memcmp(packet,"LOWER.ZIP\r\r",11));
 check(clip_prepare(&list,CLIP_ALL,packet,sizeof(packet),&n)==CLIP_OK && n==22 && !memcmp(packet,"lower.zip\r\rLOWER.ZIP\r\r",22));
 check(clip_prepare(&list,CLIP_SINGLE,packet,sizeof(packet),&n)==CLIP_OK && n==10 && !memcmp(packet,"lower.zip\r",10) && list.count==3);
 check(clip_change(&list,CLIP_DELETE,0,0)==CLIP_OK && list.count==2 && !list.names[0][0] && list.tags[1]==16);
 check(clip_prepare(&list,CLIP_SINGLE,packet,sizeof(packet),&n)==CLIP_OK && n==1 && packet[0]==13);
 check(clip_change(&list,CLIP_SEPARATOR,32,0)==CLIP_OK && clip_change(&list,CLIP_PURGE,0,0)==CLIP_OK && list.separator==32 && list.count==0);
 check(clip_prepare(&list,CLIP_ALL,0,0,&n)==CLIP_OK && n==0);
 for(i=0;i<15;++i){memcpy(input,"ABCDEFGH.ZIP",13);input[0]=(char)('A'+i);check(clip_change(&list,CLIP_ADD,0,input)==CLIP_OK);}
 saved=list;check(clip_change(&list,CLIP_ADD,0,0)==CLIP_FULL && !memcmp(&list,&saved,sizeof(list)));
 memset(packet,0xa5,sizeof(packet));n=0x5555;
 check(clip_prepare(&list,CLIP_ALL,packet,195,&n)==CLIP_CAPACITY && n==0x5555 && packet[0]==0xa5);
 check(clip_prepare(&list,CLIP_ALL,packet,196,&n)==CLIP_OK && n==196 && packet[194]==32 && packet[195]==13 && packet[196]==0xa5);
 for(i=0;i<256;++i){list.separator=i;check(clip_prepare(&list,CLIP_ALL,packet,196,&n)==CLIP_OK && n==196 && packet[12]==(unsigned char)i && packet[195]==13);}
 check(clip_change(&list,CLIP_EDIT,0,list.names[1])==CLIP_OK && !strcmp(list.names[0],list.names[1]));
 saved=list;check(clip_change(&list,CLIP_SEPARATOR,256,0)==CLIP_ARGUMENT && !memcmp(&list,&saved,sizeof(list)));
 check(clip_prepare(&list,CLIP_ALL,(unsigned char *)&list,196,&n)==CLIP_ARGUMENT && !memcmp(&list,&saved,sizeof(list)));
 check(clip_prepare(&list,CLIP_ALL,packet,196,&list.count)==CLIP_ARGUMENT && !memcmp(&list,&saved,sizeof(list)));
 memset(list.names[7],'X',13);saved=list;check(clip_change(&list,CLIP_PURGE,0,0)==CLIP_STATE && !memcmp(&list,&saved,sizeof(list)));
 check(clip_initialize(&list)==CLIP_OK && clip_change(&list,CLIP_ADD,0,"")==CLIP_EMPTY);
 memcpy(row,"FIRST.ZIP SECOND.ARJ",21);
 check(clip_extract(row,20,5,name,&first,&past)==CLIP_OK && first==0 && past==9 && !strcmp(name,"FIRST.ZIP"));
 check(clip_extract(row,20,16,name,&first,&past)==CLIP_OK && first==10 && past==20 && !strcmp(name,"SECOND.ARJ"));
 memcpy(row,"TOOLONGAA.ZIP",14);memset(name,'Q',13);first=0x1111;past=0x2222;
 check(clip_extract(row,13,9,name,&first,&past)==CLIP_NO_FILENAME && name[0]=='Q' && first==0x1111 && past==0x2222);
 memcpy(row,"FILENAME.LONGEXT",17);
 check(clip_extract(row,16,8,name,&first,&past)==CLIP_OK && !strcmp(name,"FILENAME.LON") && past==12);
 memcpy(row,"FOO.",5);check(clip_extract(row,4,3,name,&first,&past)==CLIP_NO_FILENAME);
 check(clip_extract(row,133,3,name,&first,&past)==CLIP_ARGUMENT);
 status=clip_extract(row,4,3,(char *)row,&first,&past);check(status==CLIP_ARGUMENT);
 for(i=0;i<256;++i){unsigned want=i>=33 && i<=126 && !strchr(".\"/\\[]:|<>+=;,",i);check(clip_valid_byte(i)==want);}
 return clipboard_test_failures;
}
