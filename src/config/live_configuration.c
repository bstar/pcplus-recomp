#include "live_configuration.h"
#include <stddef.h>
#include <string.h>
typedef char word_abi[sizeof(unsigned)==2?1:-1];
typedef char plan_abi[sizeof(live_configuration_plan)==626?1:-1];
typedef char modem_abi[offsetof(live_configuration_plan,modem)==42?1:-1];
typedef char directory_abi[offsetof(live_configuration_plan,directory)==410?1:-1];
typedef char mask_abi[offsetof(live_configuration_plan,change_mask)==624?1:-1];
static unsigned extent(const void *p,unsigned n)
{ return p && (unsigned long)(unsigned)p+n<=65536UL; }
static unsigned disjoint(const void *a,unsigned n,const void *b,unsigned m)
{ return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a; }
static unsigned valid_serial(const terminal_import_settings *s)
{
 static const unsigned bases[]={0x3f8,0x2f8,0x3e8,0x2e8},irqs[]={4,3,4,3};
 static const unsigned long rates[]={300UL,1200UL,2400UL,4800UL,9600UL,19200UL,38400UL,57600UL,115200UL};
 unsigned i;unsigned long rate;
 if(s->port_number<1 || s->port_number>4 || s->parity>4 ||
  (s->data_bits!=7 && s->data_bits!=8) || (s->stop_bits!=1 && s->stop_bits!=2) ||
  s->software_flow>1 || s->hardware_flow>1 || (s->terminal_id!=4 && s->terminal_id!=6) ||
  s->normal_attribute>255 || s->bold_attribute>255 || s->preset_attribute>255 ||
  s->reverse_attribute>255 || s->underline_attribute>255 || s->autowrap>1 ||
  s->scroll_enabled>1 || s->mapping_pause_character>255 || s->translation_mode>2)return 0;
 if(s->io_base!=bases[s->port_number-1] || s->irq!=irqs[s->port_number-1])return 0;
 rate=s->baud_low|((unsigned long)s->baud_high<<16);
 for(i=0;i<9;++i)if(rate==rates[i])return 1;
 return 0;
}
static unsigned string_equal(const unsigned char *a,const unsigned char *b,unsigned size)
{
 unsigned i;
 for(i=0;i<size;++i){if(a[i]!=b[i])return 0;if(!a[i])return 1;}
 return 0; /* Unterminated active metadata cannot equal a bounded candidate. */
}
static unsigned modem_equal(const modem_import_settings *a,const modem_import_settings *b)
{
 unsigned i;
 /* First nine words include delay/pause shared with mapping. BREAK is separate. */
 if(memcmp(a,b,18))return 0;
 if(!string_equal(a->initialization,b->initialization,47) ||
  !string_equal(a->dial_prefix,b->dial_prefix,25) || !string_equal(a->dial_suffix,b->dial_suffix,25) ||
  !string_equal(a->hangup,b->hangup,25) || !string_equal(a->answer_on,b->answer_on,25) ||
  !string_equal(a->answer_off,b->answer_off,25))return 0;
 for(i=0;i<11;++i)if(!string_equal(a->responses[i],b->responses[i],16))return 0;
 return 1;
}
static unsigned differences(const live_configuration_plan *a,const live_configuration_plan *b)
{
 const terminal_import_settings *x=&a->serial,*y=&b->serial;unsigned mask=0;
 if(x->port_number!=y->port_number || x->io_base!=y->io_base || x->irq!=y->irq)mask|=LIVE_CHANGE_PORT;
 if(x->baud_low!=y->baud_low || x->baud_high!=y->baud_high)mask|=LIVE_CHANGE_BAUD;
 if(x->parity!=y->parity || x->data_bits!=y->data_bits || x->stop_bits!=y->stop_bits)mask|=LIVE_CHANGE_LINE;
 if(x->software_flow!=y->software_flow || x->hardware_flow!=y->hardware_flow)mask|=LIVE_CHANGE_FLOW;
 if(x->terminal_id!=y->terminal_id)mask|=LIVE_CHANGE_PROFILE;
 if(x->translation_mode!=y->translation_mode)mask|=LIVE_CHANGE_TRANSLATION;
 if(x->normal_attribute!=y->normal_attribute || x->bold_attribute!=y->bold_attribute ||
  x->preset_attribute!=y->preset_attribute || x->reverse_attribute!=y->reverse_attribute ||
  x->underline_attribute!=y->underline_attribute || x->autowrap!=y->autowrap ||
  x->scroll_enabled!=y->scroll_enabled)mask|=LIVE_CHANGE_DISPLAY;
 if(x->mapping_pause_character!=y->mapping_pause_character ||
  x->mapping_character_delay_units!=y->mapping_character_delay_units)mask|=LIVE_CHANGE_MAPPING;
 if(!modem_equal(&a->modem,&b->modem))mask|=LIVE_CHANGE_MODEM;
 if(a->modem.break_delay_units!=b->modem.break_delay_units)mask|=LIVE_CHANGE_BREAK;
 if(memcmp(&a->directory,&b->directory,sizeof(a->directory)))mask|=LIVE_CHANGE_DIRECTORY;
 if(a->directory.dialing_mode!=b->directory.dialing_mode ||
  !string_equal(a->directory.target,b->directory.target,64))mask|=LIVE_CHANGE_TARGET;
 return mask;
}
unsigned __cdecl live_configuration_decode(const prm_dos_image *image,
 const directory_dos_selection *selection,unsigned codes,unsigned category_mask,
 const live_configuration_plan *active,live_configuration_plan *candidate,
 live_configuration_result *result)
{
 const void *regions[5];unsigned sizes[5],count=0,i,j,status;
 live_configuration_plan stage;directory_live_result directory_result;
 regions[count]=image;sizes[count++]=sizeof(*image);
 if(selection){regions[count]=selection;sizes[count++]=sizeof(*selection);}
 if(active){regions[count]=active;sizes[count++]=sizeof(*active);}
 regions[count]=candidate;sizes[count++]=sizeof(*candidate);
 regions[count]=result;sizes[count++]=sizeof(*result);
 for(i=0;i<count;++i){
  if(!extent(regions[i],sizes[i]))return LIVE_CONFIGURATION_ARGUMENT;
  for(j=0;j<i;++j)if(!disjoint(regions[i],sizes[i],regions[j],sizes[j]))return LIVE_CONFIGURATION_ARGUMENT;
 }
 memset(result,0,sizeof(*result));
 if(codes>1 || (!selection && codes) || category_mask>15 || (!active && category_mask)){
  result->status=LIVE_CONFIGURATION_ARGUMENT;return result->status;
 }
 if(active && !valid_serial(&active->serial)){
  result->status=LIVE_CONFIGURATION_ACTIVE;return result->status;
 }
 memset(&stage,0,sizeof(stage));
 if(selection){
  status=directory_live_decode(image,selection,codes,&stage.serial,&stage.modem,&stage.directory,&directory_result);
  if(status){result->status=LIVE_CONFIGURATION_DIRECTORY;result->source_status=status;return result->status;}
 }else{
  status=terminal_import_decode(image,&stage.serial);
  if(status){result->status=LIVE_CONFIGURATION_SERIAL;result->source_status=status;return result->status;}
  status=modem_import_decode(image,&stage.modem);
  if(status){result->status=LIVE_CONFIGURATION_MODEM;result->source_status=status;return result->status;}
 }
 if(category_mask&1){stage.serial.port_number=active->serial.port_number;stage.serial.io_base=active->serial.io_base;stage.serial.irq=active->serial.irq;}
 if(category_mask&2){stage.serial.baud_low=active->serial.baud_low;stage.serial.baud_high=active->serial.baud_high;}
 if(category_mask&4){stage.serial.parity=active->serial.parity;stage.serial.data_bits=active->serial.data_bits;stage.serial.stop_bits=active->serial.stop_bits;}
 if(category_mask&8){stage.serial.software_flow=active->serial.software_flow;stage.serial.hardware_flow=active->serial.hardware_flow;}
 if(active)stage.change_mask=differences(active,&stage);
 memcpy(candidate,&stage,sizeof(stage));return LIVE_CONFIGURATION_OK;
}
