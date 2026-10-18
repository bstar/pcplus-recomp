/* Newly authored validated plan for proved fields; original evidence retained
 * in docs/MODEM_CONFIGURATION.md. Not a recovered original decoder or dialer. */
#include "modem_import.h"
#include <stddef.h>
#include <string.h>
#define ABI(member,at) typedef char abi_##member[(offsetof(modem_import_settings,member)==at)?1:-1]
ABI(dial_timeout_seconds,0);ABI(redial_pause_seconds,2);ABI(autobaud,4);
ABI(abort_drop_dtr,6);ABI(initialize_while_connected,8);ABI(dial_cycle_limit,10);
ABI(command_character_delay_units,12);ABI(command_pause_character,14);
ABI(dial_abort_character,16);ABI(initialization,18);ABI(dial_prefix,65);
ABI(dial_suffix,90);ABI(hangup,115);ABI(answer_on,140);ABI(answer_off,165);
ABI(responses,190);ABI(break_delay_units,366);
typedef char abi_settings_size[sizeof(modem_import_settings)==MODEM_IMPORT_SIZE?1:-1];
typedef char abi_word_size[sizeof(unsigned)==2?1:-1];
static unsigned word(const prm_dos_image *image,unsigned offset)
{ return image->bytes[offset]|((unsigned)image->bytes[offset+1]<<8); }
static unsigned extent(const void *pointer,unsigned length)
{ return pointer && (unsigned long)(unsigned)pointer+length<=65536UL; }
static unsigned disjoint(const void *left,unsigned left_size,const void *right,unsigned right_size)
{
 unsigned long a=(unsigned)left,b=(unsigned)right;
 return a+left_size<=b || b+right_size<=a;
}
static unsigned bounded(const unsigned char *text,unsigned capacity,unsigned caret)
{
 unsigned length=0,i;
 while(length<capacity && text[length])++length;
 if(length==capacity)return 0;
 if(!caret)return 1;
 for(i=0;i<length;++i){
  if(text[i]=='^'){
   if(++i==length)return 0;
   if(text[i]=='^' && i+1<length && text[i+1]=='^')++i;
  }
 }
 return 1;
}
modem_import_status __cdecl modem_import_decode(const prm_dos_image *image,
 modem_import_settings *destination)
{
 static const unsigned command_offsets[]={0x18,0x47,0x60,0x79,0x92,0xab};
 static const unsigned command_sizes[]={47,25,25,25,25,25};
 modem_import_settings candidate;
 unsigned i;
 if(!extent(image,sizeof(*image)) || !extent(destination,sizeof(*destination)) ||
  !disjoint(image,sizeof(*image),destination,sizeof(*destination)))return MODEM_IMPORT_ARGUMENT;
 candidate.dial_timeout_seconds=word(image,0x0a);
 candidate.redial_pause_seconds=word(image,0x0c);
 candidate.autobaud=word(image,0x0e);
 candidate.abort_drop_dtr=word(image,0x10);
 candidate.initialize_while_connected=word(image,0x14);
 candidate.dial_cycle_limit=word(image,0x16);
 candidate.command_character_delay_units=word(image,0x1e4);
 candidate.command_pause_character=image->bytes[0x1e2];
 candidate.dial_abort_character=image->bytes[0x12];
 candidate.break_delay_units=word(image,0x1a4);
 if(candidate.autobaud>1 || candidate.abort_drop_dtr>1 ||
  candidate.initialize_while_connected>1)return MODEM_IMPORT_BOOLEAN;
 /* Maintained engine uses32-bit deadlines. These are its positive/signed
  * input bounds, not a reproduction of the original16-bit elapsed counters. */
 if(!candidate.dial_timeout_seconds || candidate.dial_timeout_seconds>32767U ||
  candidate.redial_pause_seconds>32767U || candidate.dial_cycle_limit>32767U ||
  candidate.command_character_delay_units>32767U)return MODEM_IMPORT_RANGE;
 for(i=0;i<6;++i)
  if(!bounded(image->bytes+command_offsets[i],command_sizes[i],1))return MODEM_IMPORT_COMMAND;
 for(i=0;i<MODEM_IMPORT_RESPONSE_COUNT;++i)
  if(!bounded(image->bytes+0xc4+i*MODEM_IMPORT_RESPONSE_SIZE,MODEM_IMPORT_RESPONSE_SIZE,0))return MODEM_IMPORT_RESPONSE;
 memcpy(candidate.initialization,image->bytes+0x18,47);
 memcpy(candidate.dial_prefix,image->bytes+0x47,25);
 memcpy(candidate.dial_suffix,image->bytes+0x60,25);
 memcpy(candidate.hangup,image->bytes+0x79,25);
 memcpy(candidate.answer_on,image->bytes+0x92,25);
 memcpy(candidate.answer_off,image->bytes+0xab,25);
 memcpy(candidate.responses,image->bytes+0xc4,sizeof(candidate.responses));
 memcpy(destination,&candidate,sizeof(candidate));
 return MODEM_IMPORT_OK;
}
modem_import_status __cdecl modem_import_read(const char *path,
 modem_import_settings *destination,prm_dos_result *io)
{
 prm_dos_image image;
 if(io && (!extent(io,sizeof(*io)) ||
  (destination && !disjoint(io,sizeof(*io),destination,sizeof(*destination)))))return MODEM_IMPORT_ARGUMENT;
 if(!path || !*path || !extent(destination,sizeof(*destination))){
  if(io){io->status=PRM_DOS_ARGUMENT;io->dos_error=0;io->close_error=0;io->bytes_processed=0;}
  return MODEM_IMPORT_ARGUMENT;
 }
 if(prm_dos_load(path,&image,io)!=PRM_DOS_OK)return MODEM_IMPORT_IO;
 return modem_import_decode(&image,destination);
}
