#include "hook_return.h"
#include <string.h>
typedef char return_plan_abi[sizeof(hook_return_plan)==490?1:-1];
typedef char return_result_abi[sizeof(hook_return_result)==8?1:-1];
extern unsigned __cdecl live_modem_expand(const unsigned char *,unsigned char *,unsigned,unsigned);
static unsigned context(void);
#pragma aux context = "mov ax,ds" "mov dx,ss" "cmp ax,dx" "jne bad" "pushf" "pop ax" "and ax,0x600" "cmp ax,0x200" "jne bad" "mov ax,1" "jmp done" "bad: xor ax,ax" "done:" value [ax] modify [dx];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned word(const prm_dos_image *p,unsigned at)
{return p->bytes[at]|((unsigned)p->bytes[at+1]<<8);}
static unsigned text_equal(const unsigned char *a,const unsigned char *b,unsigned n)
{unsigned i;for(i=0;i<n;++i){if(a[i]!=b[i])return 0;if(!a[i])return 1;}return 0;}
static unsigned allowed(unsigned at,unsigned port,unsigned modem)
{
 if(at<10 || (at>=0x194 && at<0x196) || (at>=0x198 && at<0x1a0) ||
  (at>=0x1a4 && at<0x1a6) || (at>=0x1ae && at<0x1b8) ||
  (at>=0x1bc && at<0x1be) || (at>=0x1e0 && at<0x1e3) ||
  (at>=0x1e4 && at<0x1e6) || (at>=0x31c && at<0x35c) ||
  (at>=0x42c && at<0x42e) || (at>=0x4e4 && at<0x4e8) ||
  (at>=0x4ea && at<0x4ec))return 1;
 if(port<4 && ((at>=0x174+port*2 && at<0x176+port*2) ||
  (at>=0x184+port*2 && at<0x186+port*2)))return 1;
 return modem && ((at>=10 && at<0x13) || (at>=0x14 && at<0x174));
}
static unsigned commands(const modem_import_settings *m)
{
 unsigned char buffer[129];unsigned i;
 const unsigned char *p[6];unsigned n[6];
 p[0]=m->initialization;n[0]=47;p[1]=m->dial_prefix;n[1]=25;
 p[2]=m->dial_suffix;n[2]=25;p[3]=m->hangup;n[3]=25;
 p[4]=m->answer_on;n[4]=25;p[5]=m->answer_off;n[5]=25;
 for(i=0;i<6;++i)if(live_modem_expand(p[i],buffer,n[i],129))return 0;
 for(i=0;i<11;++i)if(live_modem_expand(m->responses[i],buffer,16,129))return 0;
 return 1;
}
static unsigned decode(const prm_dos_image *p,unsigned active,hook_return_plan *out,hook_return_result *r)
{
 unsigned code;
 code=terminal_import_decode(p,&out->serial);
 if(code){r->source_status=code;return HOOK_RETURN_SERIAL;}
 if(active){
  code=modem_import_decode(p,&out->modem);
  if(code){r->source_status=code;return HOOK_RETURN_MODEM;}
  if(!commands(&out->modem))return HOOK_RETURN_EXPANSION;
 }else{
  unsigned i;unsigned char *raw=(unsigned char *)&out->modem;
  for(i=0;i<sizeof(out->modem);++i)raw[i]=0;
  out->modem.break_delay_units=word(p,0x1a4);
  out->modem.command_pause_character=out->serial.mapping_pause_character;
  out->modem.command_character_delay_units=out->serial.mapping_character_delay_units;
 }
 code=transfer_import_decode(p,&out->transfer);
 if(code){r->source_status=code;return HOOK_RETURN_TRANSFER;}
 out->modem_active=active;out->sound_enabled=word(p,0x1bc)!=0;
 out->mouse_x=word(p,0x4e4);out->mouse_y=word(p,0x4e6);
 if(out->mouse_x<1 || out->mouse_x>999 || out->mouse_y<1 || out->mouse_y>999)return HOOK_RETURN_CONTROLS;
 return 0;
}
static unsigned modem_equal(const modem_import_settings *a,const modem_import_settings *b)
{
 unsigned i;
 if(memcmp(a,b,18))return 0;
 if(!text_equal(a->initialization,b->initialization,47) || !text_equal(a->dial_prefix,b->dial_prefix,25) ||
  !text_equal(a->dial_suffix,b->dial_suffix,25) || !text_equal(a->hangup,b->hangup,25) ||
  !text_equal(a->answer_on,b->answer_on,25) || !text_equal(a->answer_off,b->answer_off,25))return 0;
 for(i=0;i<11;++i)if(!text_equal(a->responses[i],b->responses[i],16))return 0;
 return 1;
}
static unsigned changes(const hook_return_plan *a,const hook_return_plan *b)
{
 const terminal_import_settings *x=&a->serial,*y=&b->serial;unsigned mask=0;
 if(x->port_number!=y->port_number || x->io_base!=y->io_base || x->irq!=y->irq)mask|=LIVE_CHANGE_PORT;
 if(x->baud_low!=y->baud_low || x->baud_high!=y->baud_high)mask|=LIVE_CHANGE_BAUD;
 if(x->parity!=y->parity || x->data_bits!=y->data_bits || x->stop_bits!=y->stop_bits)mask|=LIVE_CHANGE_LINE;
 if(x->software_flow!=y->software_flow || x->hardware_flow!=y->hardware_flow)mask|=LIVE_CHANGE_FLOW;
 if(x->terminal_id!=y->terminal_id)mask|=LIVE_CHANGE_PROFILE;
 if(x->normal_attribute!=y->normal_attribute || x->bold_attribute!=y->bold_attribute ||
  x->preset_attribute!=y->preset_attribute || x->reverse_attribute!=y->reverse_attribute ||
  x->underline_attribute!=y->underline_attribute || x->autowrap!=y->autowrap || x->scroll_enabled!=y->scroll_enabled)mask|=LIVE_CHANGE_DISPLAY;
 if(x->mapping_pause_character!=y->mapping_pause_character || x->mapping_character_delay_units!=y->mapping_character_delay_units)mask|=LIVE_CHANGE_MAPPING;
 if(x->translation_mode!=y->translation_mode)mask|=LIVE_CHANGE_TRANSLATION;
 if(x->clipboard_separator!=y->clipboard_separator)mask|=LIVE_CHANGE_CLIPBOARD;
 if(a->modem_active && !modem_equal(&a->modem,&b->modem))mask|=LIVE_CHANGE_MODEM;
 if(a->modem.break_delay_units!=b->modem.break_delay_units)mask|=LIVE_CHANGE_BREAK;
 if(a->transfer.auto_download!=b->transfer.auto_download ||
  !text_equal((const unsigned char *)a->transfer.download_directory,(const unsigned char *)b->transfer.download_directory,64))mask|=LIVE_CHANGE_TRANSFER;
 if(a->sound_enabled!=b->sound_enabled)mask|=HOOK_CHANGE_SOUND;
 if(a->mouse_x!=b->mouse_x || a->mouse_y!=b->mouse_y)mask|=LIVE_CHANGE_MOUSE;
 return mask;
}
unsigned __far __cdecl hook_return_validate(const prm_dos_image *before,const prm_dos_image *after,
 unsigned modem_active,hook_return_plan *out,hook_return_result *result)
{
 const void *objects[4];unsigned sizes[4],i,j,status;hook_return_plan old,stage;
 if(!context())return HOOK_RETURN_ARGUMENT;
 objects[0]=before;sizes[0]=sizeof(*before);objects[1]=after;sizes[1]=sizeof(*after);
 objects[2]=out;sizes[2]=sizeof(*out);objects[3]=result;sizes[3]=sizeof(*result);
 for(i=0;i<4;++i){
  if(!extent(objects[i],sizes[i]))return HOOK_RETURN_ARGUMENT;
  for(j=0;j<i;++j)if(!apart(objects[i],sizes[i],objects[j],sizes[j]))return HOOK_RETURN_ARGUMENT;
 }
 result->status=result->source_status=0;result->input_index=0;result->offset=65535U;
 if(modem_active>1){result->status=HOOK_RETURN_ARGUMENT;return result->status;}
 status=decode(before,modem_active,&old,result);
 if(status){result->status=status;return status;}
 result->input_index=2;stage.raw_changed=0;
 for(i=0;i<1264;++i)if(before->bytes[i]!=after->bytes[i]){
  if(!allowed(i,word(after,0),modem_active)){
   result->status=HOOK_RETURN_UNSUPPORTED;result->offset=i;return result->status;
  }
  stage.raw_changed=1;
 }
 result->input_index=1;status=decode(after,modem_active,&stage,result);
 if(status){result->status=status;return status;}
 stage.change_mask=changes(&old,&stage);
 memcpy(out,&stage,sizeof(stage));result->input_index=2;return HOOK_RETURN_OK;
}
