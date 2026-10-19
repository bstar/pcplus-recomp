#include "transfer_import.h"
#include <stddef.h>
#include <string.h>
typedef char transfer_auto_at_zero[offsetof(transfer_import_settings,auto_download)==0?1:-1];
typedef char transfer_path_at_two[offsetof(transfer_import_settings,download_directory)==2?1:-1];
typedef char transfer_settings_size[sizeof(transfer_import_settings)==66?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned slash(unsigned c){return c=='/' || c=='\\';}
static unsigned leaf(const char *p,unsigned n)
{
 unsigned i,c,base=0,ext=0,dot=0;char stem[9];
 if(!n || n>12)return 0;
 for(i=0;i<n;++i){
  c=fold((unsigned char)p[i]);
  if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++ext>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base || (dot && !ext))return 0;stem[base]=0;
 if(!strcmp(stem,"CON") || !strcmp(stem,"AUX") || !strcmp(stem,"PRN") || !strcmp(stem,"NUL") || !strcmp(stem,"CLOCK$"))return 0;
 return !(base==4 && stem[3]>='1' && stem[3]<='9' && (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)));
}
unsigned __cdecl transfer_import_path(const char *p,unsigned capacity)
{
 unsigned n,start=0,end;
 if(!capacity || capacity>64 || !extent(p,capacity))return 0;
 for(n=0;n<capacity && p[n];++n);if(n==capacity)return 0;
 if(!n)return 1;
 if(n>=2 && p[1]==':'){
  if(fold((unsigned char)p[0])<'A' || fold((unsigned char)p[0])>'Z')return 0;
  start=2;if(start==n)return 1;
 }
 if(slash((unsigned char)p[start])){++start;if(start==n)return 1;}
 if(p[start]=='.' && (start+1==n || (start+2==n && slash((unsigned char)p[start+1]))))return 1;
 for(end=start;end<=n;++end){
  if(end==n || slash((unsigned char)p[end])){
   if(!leaf(p+start,end-start))return 0;
   if(end==n || end+1==n)return 1;
   start=end+1;
  }
 }
 return 0;
}
unsigned __cdecl transfer_import_decode(const prm_dos_image *image,transfer_import_settings *out)
{
 transfer_import_settings stage;unsigned n=0;
 if(!extent(image,sizeof(*image)) || !extent(out,sizeof(*out)) ||
  !separate(image,sizeof(*image),out,sizeof(*out)))return TRANSFER_IMPORT_ARGUMENT;
 if(!transfer_import_path((const char *)image->bytes+0x31c,64))return TRANSFER_IMPORT_PATH;
 memset(&stage,0,sizeof(stage));stage.auto_download=(image->bytes[0x42c] || image->bytes[0x42d])?1:0;
 if(!image->bytes[0x31c])stage.download_directory[0]='.';
 else {while(image->bytes[0x31c+n]){stage.download_directory[n]=(char)image->bytes[0x31c+n];++n;}}
 memcpy(out,&stage,sizeof(stage));return TRANSFER_IMPORT_OK;
}
