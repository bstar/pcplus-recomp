/* Actual DOS diagnostic: scripted wire, far callbacks, real filesystem.
 * Receive callbacks compose the maintained exclusive checked download owner.
 * Source callbacks here are diagnostic stdio, not the terminal source adapter.
 */
#include "zmodem.h"
#include "download_file.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef char far_callback_abi[sizeof(((zm_ops *)0)->read_byte)==4?1:-1];
typedef char word_abi[sizeof(unsigned)==2?1:-1];
static zm_session session;
static FILE *incoming,*outgoing,*source,*list;
static unsigned fault,uncertain,physical_closes;
static unsigned ZM_FAR __cdecl read_byte(void *ctx,unsigned seconds)
{
 int lo,hi;(void)ctx;(void)seconds;
 lo=fgetc(incoming);if(lo==EOF)return ZM_WAIT;
 hi=fgetc(incoming);if(hi==EOF)return ZM_BROKEN;
 return (unsigned)lo|((unsigned)hi<<8);
}
static unsigned ZM_FAR __cdecl write_wire(void *ctx,const void *data,unsigned n)
{(void)ctx;return fwrite(data,1,n,outgoing)!=n;}
static unsigned ZM_FAR __cdecl next(void *ctx,char *name,zw_u32 *size)
{
 char text[32];long end;unsigned n;(void)ctx;
 if(!list || !fgets(text,sizeof(text),list))return ZM_DONE;
 n=strcspn(text,"\r\n");if(!n || n>12)return ZM_FILE;text[n]=0;
 source=fopen(text,"rb");if(!source)return ZM_FILE;
 if(fseek(source,0,SEEK_END) || (end=ftell(source))<0 || fseek(source,0,SEEK_SET))return ZM_FILE;
 strcpy(name,text);*size=(zw_u32)end;return 0;
}
static unsigned ZM_FAR __cdecl seek_file(void *ctx,zw_u32 offset)
{(void)ctx;return fault==1 || offset>0x7fffffffUL || fseek(source,(long)offset,SEEK_SET)!=0;}
static unsigned ZM_FAR __cdecl read_file(void *ctx,void *data,unsigned n,unsigned *got)
{(void)ctx;if(fault==2)return 1;*got=fread(data,1,n,source);return ferror(source)!=0;}
static unsigned ZM_FAR __cdecl close_source(void *ctx,unsigned complete)
{
 FILE *owned=source;int r;(void)ctx;(void)complete;
 if(uncertain)return 1;if(!owned)return 0;
 source=0;++physical_closes;r=fclose(owned);
 if(r || fault==3){uncertain=1;return 1;}return 0;
}
static unsigned ZM_FAR __cdecl open_received(void *ctx,const batch_header_result *meta)
{
 unsigned r;(void)ctx;
 r=transfer_download_begin(meta->name,"PCZRX.$$$");
 return r==TF_CONFLICT?ZM_DONE:r?ZM_FILE:0;
}
static unsigned ZM_FAR __cdecl write_received(void *ctx,const void *data,unsigned n)
{(void)ctx;return fault==4?1:transfer_download_append(data,n);}
static unsigned ZM_FAR __cdecl commit_received(void *ctx)
{(void)ctx;if(fault==5){transfer_download_seal();return 1;}return transfer_download_finish();}
static unsigned ZM_FAR __cdecl abort_received(void *ctx)
{(void)ctx;return transfer_download_abort();}
static const zm_ops ops={read_byte,write_wire,next,seek_file,read_file,close_source,
 open_received,write_received,commit_received,abort_received};
int main(int argc,char **argv)
{
 unsigned r;
 if(argc<2)return 1;if(argc>2)fault=(unsigned)atoi(argv[2]);
 incoming=fopen("IN.BIN","rb");outgoing=fopen("OUT.BIN","wb");
 if(!incoming || !outgoing)return 2;
 list=fopen("LIST.TXT","r");
 r=argc>3?zm_run_profile(&session,&ops,0,argv[1][0]=='S',0,(unsigned)atoi(argv[3])):
  zm_run(&session,&ops,0,argv[1][0]=='S');
 fclose(incoming);fclose(outgoing);if(list)fclose(list);
 printf("status=%u files=%lu bytes=%lu cleanup=%u owned=%u closes=%u uncertain=%u stage=%u workspace=%u ops=%u\n",
  r,session.files,session.bytes,session.cleanup_status,session.owned,physical_closes,uncertain,transfer_download_result.stage_exists,sizeof(session),sizeof(ops));
 return 0;
}
