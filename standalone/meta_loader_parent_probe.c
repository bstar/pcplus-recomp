/* Startup-only full-parent diagnostic. Owns an unused retained arena before
 * UART enable; never installed as a normal command. All IO uses owned fixtures. */
#include <dos.h>
#include "meta_loader.h"
#include "meta_editor.h"
#include "../src/capture/capture_file.h"
unsigned __far __cdecl capture_file_claim(const char *,void *);
#define CODE __based(__segname("_CODE"))
static const char CODE name_text[]="METAPRB.KEY";
static const char CODE path_text[]="C:\\METAPRB.KEY";
unsigned __far __cdecl meta_editor_open_far(meta_editor __far *,unsigned,const unsigned char __far *,const char __far *,const char __far *,unsigned);
unsigned __far __cdecl meta_editor_key_far(meta_editor __far *,unsigned);
unsigned __far __cdecl meta_editor_step_far(meta_editor __far *,unsigned);
unsigned __far __cdecl meta_editor_stop_far(meta_editor __far *);
unsigned __cdecl meta_probe_write(const unsigned __far *,unsigned);
#define CHECK(x) do {++checks;if(!(x)){error=__LINE__;goto done;}}while(0)
static unsigned pump(void)
{unsigned i,e;for(i=0;i<2000 && (meta_loader_inspect(0)==META_LOAD_READING || meta_loader_inspect(0)==META_LOAD_FIXING);++i){e=meta_loader_step(1);if(e)return e;}return meta_loader_inspect(0)==META_LOAD_READY?0:1;}
unsigned __far __cdecl meta_loader_parent_probe(unsigned psp,unsigned char __far *arena)
{
 meta_editor __far *s=(meta_editor __far *)arena;unsigned char __far *records=arena+13000;
 unsigned checks=0,error=0,i,n,report[8];char name[64],path[64];
 CHECK(FP_OFF(arena)==0);
 for(i=0;i<64;++i){name[i]=i<sizeof(name_text)?name_text[i]:0;path[i]=i<sizeof(path_text)?path_text[i]:0;}
 for(i=0;i<540;++i)records[i]=0;for(i=0;i<10;++i)records[i*54]=3;
 CHECK(!meta_loader_begin(psp,1) && !pump() && !meta_loader_enter());
 CHECK(!meta_editor_open_far(s,psp,records,name,path,0x0607));
 CHECK(!meta_editor_step_far(s,1) && s->phase==META_EDITOR_DIALOG);
 CHECK(meta_loader_release()==META_LOAD_BUSY);
 CHECK(capture_file_claim(path,(void *)0x7b7b)==CF_BUSY);
 CHECK(!meta_editor_key_far(s,'R') && !meta_editor_key_far(s,13) && !meta_editor_key_far(s,'x') && !meta_editor_key_far(s,13));
 CHECK(s->dialog.records[2]=='x' && !meta_editor_key_far(s,'S'));
 for(n=0;s->phase!=META_EDITOR_DIALOG && n<8;++n)CHECK(!meta_editor_step_far(s,1));
 CHECK(s->phase==META_EDITOR_DIALOG && s->owner.write.installed);
 CHECK(!meta_editor_stop_far(s));
 for(n=0;s->phase!=META_EDITOR_CLOSED && n<8;++n)CHECK(!meta_editor_step_far(s,1));
 CHECK(s->phase==META_EDITOR_CLOSED && !meta_loader_release());
 /* Exercise the actual resident KEY reader in the next fresh module. Bind
  * reads saved baseline while deliberately preserving unsaved live records. */
 for(i=0;i<24000;++i)arena[16384+i]=0xcc;
 CHECK(!meta_loader_begin(psp,1) && !pump() && !meta_loader_enter());
 CHECK(!meta_editor_open_far(s,psp,records,name,path,0x0607));
 CHECK(!meta_editor_step_far(s,1) && s->owner.baseline[2]=='x' && s->dialog.records[2]==0);
 CHECK(!meta_editor_stop_far(s));
 for(n=0;s->phase!=META_EDITOR_CLOSED && n<8;++n)CHECK(!meta_editor_step_far(s,1));
 CHECK(s->phase==META_EDITOR_CLOSED && !meta_loader_release());
 done:
 report[0]=0x4d50;report[1]=1;report[2]=checks;report[3]=error;report[4]=meta_loader_inspect(0);report[5]=meta_loader_inspect(1);report[6]=meta_loader_inspect(2);report[7]=meta_loader_inspect(META_LOAD_BYTES);
 if(meta_probe_write(report,sizeof(report)))return 254;
 return error;
}
