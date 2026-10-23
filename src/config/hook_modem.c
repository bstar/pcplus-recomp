#include "hook_modem.h"
#include "../terminal/hook_transaction.h"
#include "../terminal/register_owner.h"
extern unsigned __cdecl live_modem_expand(const unsigned char *,unsigned char *,unsigned,unsigned);
extern unsigned __cdecl hook_rate_index(unsigned,unsigned);
extern unsigned __far __cdecl hook_modem_init_plan(const unsigned char *,unsigned);
extern unsigned __far __cdecl terminal_register_context(void);
extern unsigned char terminal_dial_target[64];
extern unsigned terminal_modem_init_wait;
#pragma aux terminal_dial_target "terminal_dial_target";
#pragma aux terminal_modem_init_wait "terminal_modem_init_wait";
typedef char plan_abi[sizeof(hook_modem_plan)==1086?1:-1];
typedef char result_abi[sizeof(hook_modem_result)==4?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned append(unsigned char *to,unsigned *at,const unsigned char *from)
{unsigned i;for(i=0;i<129 && from[i];++i){if(*at>=128)return 1;to[(*at)++]=from[i];}return i==129;}
unsigned __far __cdecl hook_modem_prepare(const hook_return_plan *settings,const unsigned char *target,
 unsigned wait,hook_modem_plan *out,hook_modem_result *result)
{
 hook_modem_plan plan;unsigned char expanded[129];
 const void *objects[4];unsigned sizes[4],i,j,status,at;
 const unsigned char *commands[6];unsigned caps[6];const modem_import_settings *m;
 if(!terminal_register_context())return HOOK_MODEM_ARGUMENT;
 objects[0]=settings;sizes[0]=490;objects[1]=target;sizes[1]=64;
 objects[2]=out;sizes[2]=1086;objects[3]=result;sizes[3]=4;
 for(i=0;i<4;++i){
  if(!extent(objects[i],sizes[i]))return HOOK_MODEM_ARGUMENT;
  for(j=0;j<i;++j)if(!apart(objects[i],sizes[i],objects[j],sizes[j]))return HOOK_MODEM_ARGUMENT;
 }
 result->status=0;result->field=65535U;
 if(wait>1 || settings->modem_active>1){result->status=HOOK_MODEM_ARGUMENT;return result->status;}
 for(i=0;i<1086;++i)((unsigned char *)&plan)[i]=0;
 plan.active=settings->modem_active;
 plan.baud_index=hook_rate_index(settings->serial.baud_low,settings->serial.baud_high);
 if(plan.baud_index>8){result->status=HOOK_MODEM_BAUD;return result->status;}
 if(plan.active){
  m=&settings->modem;plan.pause_character=m->command_pause_character;
  if(plan.pause_character>255){result->status=HOOK_MODEM_ARGUMENT;return result->status;}
  commands[0]=m->initialization;caps[0]=47;commands[1]=m->dial_prefix;caps[1]=25;
  commands[2]=m->dial_suffix;caps[2]=25;commands[3]=m->hangup;caps[3]=25;
  commands[4]=m->answer_on;caps[4]=25;commands[5]=m->answer_off;caps[5]=25;
  for(i=0;i<6;++i)if(live_modem_expand(commands[i],plan.commands[i],caps[i],129)){
   result->status=HOOK_MODEM_COMMAND;result->field=i;return result->status;
  }
  for(i=0;i<11;++i){
   for(j=0;j<16 && m->responses[i][j];++j);
   if(j==16){result->status=HOOK_MODEM_RESPONSE;result->field=6+i;return result->status;}
   for(j=0;j<16;++j)plan.responses[i*16+j]=m->responses[i][j];
  }
  if(wait && hook_modem_init_plan(plan.commands[0],plan.pause_character)){
   result->status=HOOK_MODEM_INITIALIZATION;result->field=19;return result->status;
  }
  status=live_modem_expand(target,expanded,64,129);
  if(status){result->status=HOOK_MODEM_COMMAND;result->field=17;return result->status;}
  at=0;
  if(append(plan.dial,&at,plan.commands[1]) || append(plan.dial,&at,expanded) || append(plan.dial,&at,plan.commands[2])){
   result->status=HOOK_MODEM_DIAL;result->field=18;return result->status;
  }
  plan.dial[at]=0;
 }
 for(i=0;i<1086;++i)((unsigned char *)out)[i]=((const unsigned char *)&plan)[i];
 return 0;
}
unsigned __far __cdecl terminal_hook_prepare_modem(hook_modem_result *result)
{
 hook_return_plan settings;hook_modem_plan plan;unsigned i,status;
 if(!terminal_register_context() || !extent(result,4))return HOOK_MODEM_ARGUMENT;
 result->status=HOOK_MODEM_STATE;result->field=65535U;
 if(terminal_hook_phase!=2 || terminal_hook_owner.phase || terminal_hook_owner.segment || terminal_register_owner.phase)return result->status;
 for(i=0;i<490;++i)((unsigned char *)&settings)[i]=((const unsigned char __far *)&terminal_hook_proposal.settings)[i];
 status=hook_modem_prepare(&settings,terminal_dial_target,terminal_modem_init_wait!=0,&plan,result);
 if(status)return status;
 for(i=0;i<1086;++i)((unsigned char __far *)&terminal_hook_modem_offer)[i]=((const unsigned char *)&plan)[i];
 terminal_hook_phase=3;return 0;
}
