#include "directory_resource_cli.h"
#include "../capture/capture_file.h"
#include "../capture/capture_fs.h"
#include <string.h>
typedef char drc_word_abi[sizeof(unsigned)==2?1:-1];
typedef char drc_snapshot_abi[sizeof(directory_resource_cli_snapshot)==138?1:-1];
directory_resource_cli_snapshot directory_resource_cli;
static unsigned cookie=0xd730;
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned external(const void *p,unsigned n)
{return extent(p,n) && separate(p,n,&cookie,2) && separate(p,n,&directory_resource_cli,sizeof(directory_resource_cli));}
unsigned __cdecl directory_resource_cli_initialize(void)
{
 if(cookie==0xd730){memset(&directory_resource_cli,0,sizeof(directory_resource_cli));cookie=0xd731;return 0;}
 return cookie==0xd731 && directory_resource_cli.state<=DRC_FAILED?0:DRC_STATE;
}
static unsigned identity(const char *path,char *output,unsigned *error)
{
 char canonical[128];unsigned n,c;
 for(n=0;n<64 && path[n];++n){}
 if(n==64 || !capture_file_validate_path(path,0))return DRC_PATH;
 memset(canonical,0,sizeof(canonical));*error=capture_fs_canonical(path,canonical);
 if(*error)return DRC_CANONICAL;
 for(n=0;n<128 && canonical[n];++n){
  c=(unsigned char)canonical[n];if(c>='a' && c<='z')c-=32;if(c=='/')c='\\';canonical[n]=(char)c;
 }
 if(n<4 || n>63 || canonical[0]<'A' || canonical[0]>'Z' || canonical[1]!=':' || canonical[2]!='\\' || !capture_file_validate_path(canonical,0))return DRC_PATH;
 memcpy(output,canonical,n+1);return 0;
}
unsigned __cdecl directory_resource_cli_bind(unsigned mask,const char *keyboard,const char *actions)
{
 directory_resource_cli_snapshot stage;unsigned status;
 if(cookie!=0xd731 || directory_resource_cli.state!=DRC_IDLE)return DRC_STATE;
 if(!external(keyboard,64) || !external(actions,64))return DRC_ARGUMENT;
 memset(&stage,0,sizeof(stage));stage.original_mask=mask;
 directory_resource_cli.state=DRC_BINDING;
 stage.failed_resource=512;
 status=mask&512?identity(keyboard,stage.keyboard,&stage.dos_error):0;
 if(!status && (mask&4096)){stage.failed_resource=4096;status=identity(actions,stage.actions,&stage.dos_error);}
 if(status){
  directory_resource_cli.state=DRC_FAILED;directory_resource_cli.status=status;
  directory_resource_cli.original_mask=mask;directory_resource_cli.failed_resource=stage.failed_resource;
  directory_resource_cli.dos_error=stage.dos_error;return status;
 }
 stage.state=DRC_BOUND;stage.failed_resource=0;memcpy(&directory_resource_cli,&stage,sizeof(stage));return 0;
}
unsigned __cdecl directory_resource_cli_request(const unsigned char *record,
 unsigned profile,unsigned psp,directory_resource_request *request)
{
 directory_resource_request stage;
 if(cookie!=0xd731 || directory_resource_cli.state!=DRC_BOUND)return DRC_STATE;
 if(!external(record,114) || !external(request,sizeof(*request)) ||
  !separate(record,114,request,sizeof(*request)) || (profile!=4 && profile!=6) || !psp)return DRC_ARGUMENT;
 memset(&stage,0,sizeof(stage));memcpy(stage.record,record,114);
 stage.profile=profile;stage.psp=psp;stage.cli_mask=directory_resource_cli.original_mask&(512U|4096U);
 memcpy(stage.cli_keyboard,directory_resource_cli.keyboard,64);memcpy(stage.cli_actions,directory_resource_cli.actions,64);
 memcpy(request,&stage,sizeof(stage));return 0;
}
