#include "prm_projection.h"
#include <string.h>
typedef char projection_word_abi[sizeof(unsigned)==2?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static void put(prm_dos_image *p,unsigned at,unsigned value)
{p->bytes[at]=(unsigned char)value;p->bytes[at+1]=(unsigned char)(value>>8);}
static unsigned text(prm_dos_image *p,unsigned at,const unsigned char *s,unsigned cap)
{
 unsigned n;for(n=0;n<cap && s[n];++n);
 if(n==cap)return 0;
 memcpy(p->bytes+at,s,n+1);return 1;
}
unsigned __cdecl prm_project_active(const prm_dos_image *baseline,
 const terminal_import_settings *serial,const modem_import_settings *modem,
 const transfer_import_settings *transfer,prm_dos_image *out)
{
 static const unsigned long rates[]={300UL,1200UL,2400UL,4800UL,9600UL,19200UL,38400UL,57600UL,115200UL};
 const void *objects[5];unsigned sizes[5],i,j,baud;unsigned long rate;
 prm_dos_image stage;terminal_import_settings decoded_serial;
 modem_import_settings decoded_modem;transfer_import_settings decoded_transfer;
 objects[0]=baseline;sizes[0]=sizeof(*baseline);
 objects[1]=serial;sizes[1]=sizeof(*serial);
 objects[2]=modem;sizes[2]=sizeof(*modem);
 objects[3]=transfer;sizes[3]=sizeof(*transfer);
 objects[4]=out;sizes[4]=sizeof(*out);
 for(i=0;i<5;++i){
  if(!extent(objects[i],sizes[i]))return PRM_PROJECT_ARGUMENT;
  for(j=0;j<i;++j)if(!apart(objects[i],sizes[i],objects[j],sizes[j]))return PRM_PROJECT_ARGUMENT;
 }
 if(serial->port_number<1 || serial->port_number>4 || serial->mapping_pause_character>255)return PRM_PROJECT_SERIAL;
 if(modem->command_pause_character>255 || modem->dial_abort_character>255)return PRM_PROJECT_MODEM;
 if(serial->mapping_pause_character!=modem->command_pause_character ||
  serial->mapping_character_delay_units!=modem->command_character_delay_units)return PRM_PROJECT_SHARED;
 rate=serial->baud_low|((unsigned long)serial->baud_high<<16);
 for(baud=0;baud<9 && rates[baud]!=rate;++baud);
 if(baud==9)return PRM_PROJECT_SERIAL;
 if(transfer->auto_download>1 || !transfer_import_path(transfer->download_directory,64))return PRM_PROJECT_TRANSFER;
 memcpy(&stage,baseline,sizeof(stage));
 put(&stage,0,serial->port_number-1);put(&stage,2,baud);
 put(&stage,4,serial->parity);put(&stage,6,serial->stop_bits);put(&stage,8,serial->data_bits);
 put(&stage,0x174+(serial->port_number-1)*2,serial->io_base);
 put(&stage,0x184+(serial->port_number-1)*2,serial->irq);
 put(&stage,0x198,serial->software_flow);put(&stage,0x19a,serial->hardware_flow);
 put(&stage,0x194,serial->terminal_id);put(&stage,0x19c,serial->autowrap);put(&stage,0x19e,serial->scroll_enabled);
 put(&stage,0x1ae,serial->normal_attribute);put(&stage,0x1b0,serial->bold_attribute);
 put(&stage,0x1b2,serial->preset_attribute);put(&stage,0x1b4,serial->reverse_attribute);put(&stage,0x1b6,serial->underline_attribute);
 put(&stage,0x1e0,serial->translation_mode);put(&stage,0x4ea,serial->clipboard_separator);
 stage.bytes[0x1e2]=(unsigned char)serial->mapping_pause_character;
 put(&stage,0x1e4,serial->mapping_character_delay_units);
 if(terminal_import_decode(&stage,&decoded_serial) || memcmp(serial,&decoded_serial,sizeof(*serial)))return PRM_PROJECT_SERIAL;
 put(&stage,0x0a,modem->dial_timeout_seconds);put(&stage,0x0c,modem->redial_pause_seconds);
 put(&stage,0x0e,modem->autobaud);put(&stage,0x10,modem->abort_drop_dtr);
 stage.bytes[0x12]=(unsigned char)modem->dial_abort_character;
 put(&stage,0x14,modem->initialize_while_connected);put(&stage,0x16,modem->dial_cycle_limit);
 put(&stage,0x1a4,modem->break_delay_units);
 if(!text(&stage,0x18,modem->initialization,47) || !text(&stage,0x47,modem->dial_prefix,25) ||
  !text(&stage,0x60,modem->dial_suffix,25) || !text(&stage,0x79,modem->hangup,25) ||
  !text(&stage,0x92,modem->answer_on,25) || !text(&stage,0xab,modem->answer_off,25))return PRM_PROJECT_MODEM;
 for(i=0;i<11;++i)if(!text(&stage,0xc4+i*16,modem->responses[i],16))return PRM_PROJECT_MODEM;
 if(modem_import_decode(&stage,&decoded_modem))return PRM_PROJECT_MODEM;
 if(!transfer->auto_download)put(&stage,0x42c,0);
 else if(!stage.bytes[0x42c] && !stage.bytes[0x42d])put(&stage,0x42c,1);
 if(stage.bytes[0x31c] || strcmp(transfer->download_directory,"."))
  if(!text(&stage,0x31c,(const unsigned char *)transfer->download_directory,64))return PRM_PROJECT_TRANSFER;
 if(transfer_import_decode(&stage,&decoded_transfer))return PRM_PROJECT_TRANSFER;
 memcpy(out,&stage,sizeof(stage));return PRM_PROJECT_OK;
}
