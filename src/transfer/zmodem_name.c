#include "zmodem_name.h"
#include <string.h>
static unsigned extent(const void *p,unsigned n)
{
#ifdef __WATCOMC__
 return p && (unsigned long)(unsigned)p+n<=65536UL;
#else
 return p && (uintptr_t)p<=UINTPTR_MAX-n;
#endif
}
static unsigned apart(const void *a,unsigned an,const void *b,unsigned bn)
{
#ifdef __WATCOMC__
 return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;
#else
 return (uintptr_t)a+an<=(uintptr_t)b || (uintptr_t)b+bn<=(uintptr_t)a;
#endif
}
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned safe(unsigned c)
{return (c>='A' && c<='Z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",c)!=0;}
unsigned __cdecl zm_name_decode(const unsigned char *block,unsigned count,
 unsigned char *scratch,batch_header_result *result)
{
 batch_header_result stage;batch_header_u32 crc=0xffffffffUL;
 unsigned n,end,i,j,c,dot=0,ext,alias_length,status;char alias[13];
 static const char hex[]="0123456789ABCDEF";
 if(!count || count>1024 || !extent(block,count) || !extent(scratch,1024) || !extent(result,sizeof(*result)) ||
  !apart(block,count,scratch,1024) || !apart(block,count,result,sizeof(*result)) || !apart(scratch,1024,result,sizeof(*result)))return BH_ARGUMENT;
 for(n=0;n<count && block[n];++n){
  c=block[n];if(n==ZM_WIRE_NAME_MAX || c<32 || c==127 || c=='/' || c=='\\' || c==':')return BH_NAME;
 }
 if(!n || (n==1 && block[0]=='.') || (n==2 && block[0]=='.' && block[1]=='.'))return BH_NAME;
 if(n==count)return BH_FORMAT;
 for(end=n+1;end<count && block[end];++end){}
 if(end==count)return BH_FORMAT;
 for(i=end+1;i<count;++i)if(block[i])return BH_FORMAT;
 memset(scratch,0,1024);memcpy(scratch,block,count);
 status=batch_header_decode(scratch,1024,&stage);
 if(status==BH_OK){memcpy(result,&stage,sizeof(stage));return BH_OK;}
 if(status!=BH_NAME)return status;
 for(i=0;i<n;++i){
  c=fold(block[i]);if(c=='.')dot=i;
  crc^=c;for(j=0;j<8;++j)crc=(crc>>1)^((crc&1)?0xedb88320UL:0);
 }
 crc^=0xffffffffUL;
 for(i=0;i<8;++i){alias[7-i]=hex[(unsigned)(crc&15)];crc>>=4;}
 alias[8]='.';ext=dot?n-dot-1:0;
 if(ext>3)ext=0;
 for(i=0;i<ext;++i)if(!safe(fold(block[dot+1+i]))){ext=0;break;}
 if(ext){for(i=0;i<ext;++i)alias[9+i]=(char)fold(block[dot+1+i]);alias_length=9+ext;}
 else{memcpy(alias+9,"DAT",3);alias_length=12;}
 alias[alias_length]=0;
 if(alias_length+1+(end-n)>1024)return BH_FORMAT;
 memset(scratch,0,1024);memcpy(scratch,alias,alias_length);
 memcpy(scratch+alias_length+1,block+n+1,end-n);
 status=batch_header_decode(scratch,1024,&stage);
 if(status)return status;
 if(stage.flags&BH_EXTENSION)stage.extension_offset=(unsigned short)(stage.extension_offset+n-alias_length);
 memcpy(result,&stage,sizeof(stage));return BH_OK;
}
