/* Maintained validation/application model for source-proved 2.01 fields.
 * CONFIGURATION.md and STARTUP_CONFIGURATION.md retain original provenance. */
#include "terminal_import.h"
#include <stddef.h>
#include <string.h>
#define ORIGINAL_BASE 0x1b84U
#define OFFSET(ds) ((ds)-ORIGINAL_BASE)
#define WORD_ABI(member,offset) typedef char abi_##member[(offsetof(terminal_import_settings,member)==offset) ? 1 : -1]
WORD_ABI(port_number,0);WORD_ABI(baud_low,2);WORD_ABI(baud_high,4);
WORD_ABI(parity,6);WORD_ABI(data_bits,8);WORD_ABI(stop_bits,10);
WORD_ABI(software_flow,12);WORD_ABI(hardware_flow,14);WORD_ABI(terminal_id,16);
WORD_ABI(normal_attribute,18);WORD_ABI(bold_attribute,20);WORD_ABI(preset_attribute,22);
WORD_ABI(reverse_attribute,24);WORD_ABI(underline_attribute,26);
WORD_ABI(autowrap,28);WORD_ABI(scroll_enabled,30);WORD_ABI(io_base,32);WORD_ABI(irq,34);
WORD_ABI(mapping_pause_character,36);WORD_ABI(mapping_character_delay_units,38);
WORD_ABI(translation_mode,40);
typedef char abi_settings_size[sizeof(terminal_import_settings)==42 ? 1 : -1];
static unsigned word(const prm_dos_image *image,unsigned at)
{ return image->bytes[at]|((unsigned)image->bytes[at+1]<<8); }
terminal_import_status __cdecl terminal_import_decode(const prm_dos_image *image,
 terminal_import_settings *destination)
{
 static const unsigned long rates[]={300UL,1200UL,2400UL,4800UL,9600UL,19200UL,38400UL,57600UL,115200UL};
 static const unsigned bases[]={0x3f8,0x2f8,0x3e8,0x2e8};
 static const unsigned irqs[]={4,3,4,3};
 terminal_import_settings candidate;
 unsigned port,baud;
 unsigned long rate;
 if(!image || !destination)return TERMINAL_IMPORT_ARGUMENT;
 port=word(image,0);baud=word(image,2);
 if(port>3 || baud>8)return TERMINAL_IMPORT_SERIAL;
 candidate.port_number=port+1;
 rate=rates[baud];candidate.baud_low=(unsigned)rate;
 candidate.baud_high=(unsigned)(rate>>16);
 candidate.parity=word(image,4);candidate.stop_bits=word(image,6);
 candidate.data_bits=word(image,8);
 candidate.io_base=word(image,OFFSET(0x1cf8)+port*2);
 candidate.irq=word(image,OFFSET(0x1d08)+port*2);
 if(candidate.parity>4 || (candidate.stop_bits!=1 && candidate.stop_bits!=2) ||
  (candidate.data_bits!=7 && candidate.data_bits!=8) ||
  candidate.io_base!=bases[port] || candidate.irq!=irqs[port])return TERMINAL_IMPORT_SERIAL;
 candidate.software_flow=word(image,OFFSET(0x1d1c));
 candidate.hardware_flow=word(image,OFFSET(0x1d1e));
 if(candidate.software_flow>1 || candidate.hardware_flow>1)return TERMINAL_IMPORT_FLOW;
 candidate.terminal_id=word(image,OFFSET(0x1d18));
 if(candidate.terminal_id!=4 && candidate.terminal_id!=6)return TERMINAL_IMPORT_PROFILE;
 candidate.normal_attribute=word(image,OFFSET(0x1d32));
 candidate.bold_attribute=word(image,OFFSET(0x1d34));
 candidate.preset_attribute=word(image,OFFSET(0x1d36));
 candidate.reverse_attribute=word(image,OFFSET(0x1d38));
 candidate.underline_attribute=word(image,OFFSET(0x1d3a));
 candidate.autowrap=word(image,OFFSET(0x1d20));
 candidate.scroll_enabled=word(image,OFFSET(0x1d22));
 candidate.mapping_pause_character=image->bytes[0x1e2];
 candidate.mapping_character_delay_units=word(image,0x1e4);
 candidate.translation_mode=word(image,OFFSET(0x1d64));
 if(candidate.translation_mode>2)return TERMINAL_IMPORT_TRANSLATION;
 if(candidate.normal_attribute>255 || candidate.bold_attribute>255 ||
  candidate.preset_attribute>255 || candidate.reverse_attribute>255 ||
  candidate.underline_attribute>255 || candidate.autowrap>1 ||
  candidate.scroll_enabled>1)return TERMINAL_IMPORT_DISPLAY;
 /* Saved live current-attribute and cursor/mode words are intentionally unused. */
 memcpy(destination,&candidate,sizeof(candidate));return TERMINAL_IMPORT_OK;
}
terminal_import_status __cdecl terminal_import_read(const char *path,
 terminal_import_settings *destination,prm_dos_result *io)
{
 prm_dos_image image;
 if(!destination){
  if(io){io->status=PRM_DOS_ARGUMENT;io->dos_error=0;io->close_error=0;io->bytes_processed=0;}
  return TERMINAL_IMPORT_ARGUMENT;
 }
 if(prm_dos_load(path,&image,io)!=PRM_DOS_OK)return TERMINAL_IMPORT_IO;
 return terminal_import_decode(&image,destination);
}
