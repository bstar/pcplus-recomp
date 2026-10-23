#include "../src/terminal/hook_transaction.h"
#include "../src/terminal/register_owner.h"
#include "../src/aspect/register_codec.h"
#include <dos.h>
extern unsigned __far __cdecl hook_probe_write(const char *,const void __far *,unsigned);
extern unsigned char __far terminal_baseline_storage[];
extern const char __far hook_probe_names[10][13];
extern unsigned char * __far __cdecl hook_probe_stack(void);
#pragma aux terminal_baseline_storage "terminal_baseline_storage";
static void copy(char *to,unsigned index)
{unsigned i;for(i=0;i<13;++i)to[i]=hook_probe_names[index][i];}
static unsigned write(unsigned index,const void __far *data,unsigned bytes)
{char name[13];copy(name,index);return hook_probe_write(name,data,bytes);}
unsigned __far __cdecl terminal_hook_probe(void)
{
 unsigned i,j,status,failures=0;
 unsigned char bank[830];
 terminal_hook_result results[10],busy;
 char path[64],name[13];
 unsigned char __far *raw=(unsigned char __far *)&terminal_hook_proposal;
 unsigned char *guard=hook_probe_stack();
 for(i=0;i<256;++i)guard[i]=0xa5;
 for(i=0;i<2584;++i)raw[i]='X';
 copy(path,0);copy(name,1);
 /* Seed a previous accepted bank. HOOK receives it directly, without the
  * per-script integer/first-string-byte reset used by ASPECT startup. */
 for(i=0;i<830;++i)terminal_register_owner.accepted[i]=(unsigned char)(128+i%127);
 for(i=0;i<10;++i){terminal_register_owner.accepted[20+i*81]='A'+i;terminal_register_owner.accepted[21+i*81]=0;}
 terminal_register_owner.epoch=17;
 terminal_register_owner.seal=register_seal(terminal_register_owner.accepted,17);
 if(!register_strings(terminal_register_owner.accepted))return 20;
 if(terminal_register_snapshot(bank,bank+20))return 21;
 if(write(2,(const void __far *)bank,830) ||
  write(3,terminal_baseline_storage,1272))return 22;
 for(i=0;i<10;++i){
  if(i==9)copy(path,7);
  status=terminal_hook_execute(path,(long)(i+3),&results[i]);
  if(status!=((i==0||i==5||i==6)?0:(i==1||i==9)?5:i==4?6:7) || results[i].status!=status)failures|=1;
  if(terminal_hook_owner.phase || terminal_hook_owner.segment)failures|=2;
  if(!status){
   if(terminal_hook_phase!=2)failures|=4;
   if(terminal_hook_execute(path,3L,&busy)!=TERMINAL_HOOK_BUSY)failures|=8;
  }else if(terminal_hook_phase)failures|=4;
  name[5]='0'+i;
  if(hook_probe_write(name,&terminal_hook_proposal,2584))return 23;
  if(terminal_hook_discard())failures|=16;
  if(terminal_register_snapshot(bank,bank+20))failures|=32;
  for(j=0;j<830;++j){
   unsigned char value=(unsigned char)(128+j%127);
   if(j>=20 && (j-20)%81==0)value='A'+(j-20)/81;
   if(j>=21 && (j-21)%81==0)value=0;
   if(bank[j]!=value)failures|=64;
  }
  if(terminal_register_owner.epoch!=17)failures|=128;
 }
 if(write(4,(const void __far *)bank,830) ||
  write(5,terminal_baseline_storage,1272) ||
  write(6,(const void __far *)results,sizeof(results)) ||
  write(8,(const void __far *)&failures,2) ||
  write(9,(const void __far *)guard,256))return 24;
 for(i=0;i<256;++i)if(guard[i]!=0xa5)return 26;
 return failures?25:0;
}
