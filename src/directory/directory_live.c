/* New DOS integration over the proved original file/record/field layout. */
#include "directory_live.h"
#include <stddef.h>
#include <string.h>
unsigned __cdecl directory_number_expand(const unsigned char *number,
 const unsigned char *codes,unsigned char *destination,unsigned mode);
#define ABI(member,at) typedef char abi_##member[(offsetof(directory_live_plan,member)==at)?1:-1]
ABI(entry_number,0);ABI(dialing_mode,2);ABI(protocol_index,4);ABI(duplex,6);
ABI(codes,8);ABI(name,10);ABI(target,35);
ABI(reserved,99);ABI(record,100);
typedef char abi_plan[sizeof(directory_live_plan)==214?1:-1];
typedef char abi_context_size[sizeof(directory_live_context)==496?1:-1];
typedef char abi_context_codes[offsetof(directory_live_context,codes)==366?1:-1];
typedef char abi_context_prm[offsetof(directory_live_context,prm_path)==368?1:-1];
typedef char abi_context_directory[offsetof(directory_live_context,directory_path)==432?1:-1];
typedef char abi_result[sizeof(directory_live_result)==10?1:-1];
typedef char abi_word[sizeof(unsigned)==2?1:-1];
static unsigned extent(const void *pointer,unsigned length)
{ return pointer && (unsigned long)(unsigned)pointer+length<=65536UL; }
static unsigned disjoint(const void *left,unsigned left_size,const void *right,unsigned right_size)
{
 unsigned long a=(unsigned)left,b=(unsigned)right;
 return a+left_size<=b || b+right_size<=a;
}
static unsigned path_size(const char *path)
{
 unsigned i;
 if(!path)return 0;
 for(i=0;i<64;++i){
  if(!extent(path,i+1))return 0;
  if(!path[i])return i?i+1:0;
 }
 return 0;
}
static unsigned bounded(const unsigned char *text,unsigned capacity)
{
 unsigned i;
 for(i=0;i<capacity;++i)if(!text[i])return 1;
 return 0;
}
static unsigned blank(const unsigned char *text)
{ return !text[0] || text[0]==' '; }
static void put_word(prm_dos_image *image,unsigned at,unsigned value)
{ image->bytes[at]=(unsigned char)value;image->bytes[at+1]=(unsigned char)(value>>8); }
static unsigned literal(const unsigned char *target)
{
 unsigned char c;
 while((c=*target++)!=0){
  if((c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0' && c<='9'))continue;
  if(!strchr(".:/-_@[]%?=&",c))return 0;
 }
 return 1;
}
static unsigned caret(const unsigned char *target)
{
 unsigned i;
 for(i=0;target[i];++i){
  if(target[i]=='^'){
   if(!target[++i])return 0;
   if(target[i]=='^' && target[i+1]=='^')++i;
  }
 }
 return 1;
}
directory_live_status __cdecl directory_live_decode(const prm_dos_image *source,
 const directory_dos_selection *selection,unsigned codes,
 terminal_import_settings *serial,modem_import_settings *modem,
 directory_live_plan *plan,directory_live_result *result)
{
 prm_dos_image image;
 terminal_import_settings serial_stage;
 modem_import_settings modem_stage;
 directory_live_plan plan_stage;
 const unsigned char *record;
 unsigned status,i,port;
 static const unsigned binding_offsets[]={0x34,0x56,0x5f};
 static const unsigned binding_sizes[]={9,9,9};
 const void *outputs[3];unsigned sizes[3],j;
 outputs[0]=serial;outputs[1]=modem;outputs[2]=plan;
 sizes[0]=sizeof(*serial);sizes[1]=sizeof(*modem);sizes[2]=sizeof(*plan);
 if(!extent(source,sizeof(*source)) || !extent(selection,sizeof(*selection)) ||
  !disjoint(source,sizeof(*source),selection,sizeof(*selection)) ||
  !selection->entry_number || selection->entry_number>200 || codes>1)return DIRECTORY_LIVE_ARGUMENT;
 for(i=0;i<3;++i){
  if(!extent(outputs[i],sizes[i]) || !disjoint(outputs[i],sizes[i],source,sizeof(*source)) ||
   !disjoint(outputs[i],sizes[i],selection,sizeof(*selection)))return DIRECTORY_LIVE_ARGUMENT;
  for(j=0;j<i;++j)if(!disjoint(outputs[i],sizes[i],outputs[j],sizes[j]))return DIRECTORY_LIVE_ARGUMENT;
 }
 if(result){
  if(!extent(result,sizeof(*result)) || !disjoint(result,sizeof(*result),source,sizeof(*source)) ||
   !disjoint(result,sizeof(*result),selection,sizeof(*selection)))return DIRECTORY_LIVE_ARGUMENT;
  for(i=0;i<3;++i)if(!disjoint(result,sizeof(*result),outputs[i],sizes[i]))return DIRECTORY_LIVE_ARGUMENT;
  memset(result,0,sizeof(*result));
 }
 memcpy(&image,source,sizeof(image));
 if(terminal_import_decode(&image,&serial_stage)!=TERMINAL_IMPORT_OK){status=DIRECTORY_LIVE_SERIAL;goto done;}
 record=selection->record;
 if(!bounded(record,25) || !bounded(record+0x19,21)){status=DIRECTORY_LIVE_RECORD;goto done;}
 if(!bounded(record+0x4b,11)){status=DIRECTORY_LIVE_RECORD;goto done;}
 for(i=0;i<3;++i){
  if(!bounded(record+binding_offsets[i],binding_sizes[i])){status=DIRECTORY_LIVE_RECORD;goto done;}
  if(!blank(record+binding_offsets[i])){status=DIRECTORY_LIVE_BINDING;goto done;}
 }
 if(record[0x4a]>1){status=DIRECTORY_LIVE_MODE;goto done;}
 if(record[0x33]!=0){status=DIRECTORY_LIVE_DUPLEX;goto done;}
 port=record[0x68];
 if(port>4){status=DIRECTORY_LIVE_SERIAL;goto done;}
 if(port)put_word(&image,0,port-1);
 put_word(&image,2,record[0x2e]|((unsigned)record[0x2f]<<8));
 put_word(&image,4,record[0x30]);put_word(&image,6,record[0x32]);
 put_word(&image,8,record[0x31]);put_word(&image,0x194,record[0x49]);
 if(terminal_import_decode(&image,&serial_stage)!=TERMINAL_IMPORT_OK){status=DIRECTORY_LIVE_SERIAL;goto done;}
 memset(&plan_stage,0,sizeof(plan_stage));
 plan_stage.entry_number=selection->entry_number;plan_stage.dialing_mode=record[0x4a];
 plan_stage.protocol_index=record[0x48];plan_stage.duplex=record[0x33];plan_stage.codes=codes;
 memcpy(plan_stage.name,record,25);
 memcpy(plan_stage.record,record,114);
 memset(&modem_stage,0,sizeof(modem_stage));
 /* BREAK is a line action even for DIRECT; retain its raw word without
  * validating modem commands/responses that DIRECT deliberately skips. */
 modem_stage.break_delay_units=image.bytes[0x1a4]|((unsigned)image.bytes[0x1a5]<<8);
 if(!plan_stage.dialing_mode){
  if(modem_import_decode(&image,&modem_stage)!=MODEM_IMPORT_OK){status=DIRECTORY_LIVE_MODEM;goto done;}
  if(directory_number_expand(record+0x19,selection->header,plan_stage.target,codes)){
   status=DIRECTORY_LIVE_TARGET;goto done;
  }
  if(!plan_stage.target[0] || (codes?!caret(plan_stage.target):!literal(plan_stage.target))){status=DIRECTORY_LIVE_TARGET;goto done;}
 }
 memcpy(serial,&serial_stage,sizeof(serial_stage));
 memcpy(modem,&modem_stage,sizeof(modem_stage));
 memcpy(plan,&plan_stage,sizeof(plan_stage));
 status=DIRECTORY_LIVE_OK;
done:
 if(result)result->status=status;
 return status;
}

/* File owner retains the original read order and error details. Pure decoding
 * never opens files; live callers can retain their current selected record. */
directory_live_status __cdecl directory_live_read_context(const char *prm_path,
 const char *directory_path,unsigned entry,unsigned codes,
 terminal_import_settings *serial,modem_import_settings *modem,
 directory_live_plan *plan,directory_live_result *result,directory_live_context *context)
{
 prm_dos_image image;
 directory_live_context context_stage;
 directory_dos_selection selection;
 directory_dos_result directory_io;
 prm_dos_result prm_io;
 terminal_import_settings serial_probe;
 unsigned prm_length,directory_length,status;
 prm_length=path_size(prm_path);directory_length=path_size(directory_path);
 if(!prm_length || !directory_length || !entry || entry>200 || codes>1 ||
  !extent(serial,sizeof(*serial)) || !extent(modem,sizeof(*modem)) ||
  !extent(plan,sizeof(*plan)) || !disjoint(serial,sizeof(*serial),modem,sizeof(*modem)) ||
  !disjoint(serial,sizeof(*serial),plan,sizeof(*plan)) ||
  !disjoint(modem,sizeof(*modem),plan,sizeof(*plan)))return DIRECTORY_LIVE_ARGUMENT;
 if(result && (!extent(result,sizeof(*result)) ||
  !disjoint(result,sizeof(*result),serial,sizeof(*serial)) ||
  !disjoint(result,sizeof(*result),modem,sizeof(*modem)) ||
  !disjoint(result,sizeof(*result),plan,sizeof(*plan)) ||
  !disjoint(result,sizeof(*result),prm_path,prm_length) ||
  !disjoint(result,sizeof(*result),directory_path,directory_length)))return DIRECTORY_LIVE_ARGUMENT;
 if(context && (!extent(context,sizeof(*context)) ||
  !disjoint(context,sizeof(*context),prm_path,prm_length) ||
  !disjoint(context,sizeof(*context),directory_path,directory_length) ||
  !disjoint(context,sizeof(*context),serial,sizeof(*serial)) ||
  !disjoint(context,sizeof(*context),modem,sizeof(*modem)) ||
  !disjoint(context,sizeof(*context),plan,sizeof(*plan)) ||
  (result && !disjoint(context,sizeof(*context),result,sizeof(*result)))))return DIRECTORY_LIVE_ARGUMENT;
 if(context){
  memset(&context_stage,0,sizeof(context_stage));context_stage.codes=codes;
  memcpy(context_stage.prm_path,prm_path,prm_length);
  memcpy(context_stage.directory_path,directory_path,directory_length);
 }
 if(result)memset(result,0,sizeof(*result));
 status=prm_dos_load(prm_path,&image,&prm_io);
 if(status!=PRM_DOS_OK){
  if(result){result->source_status=status;result->dos_error=prm_io.dos_error;
   result->close_error=prm_io.close_error;result->bytes_processed=prm_io.bytes_processed;}
  status=DIRECTORY_LIVE_PRM_IO;goto done;
 }
 if(terminal_import_decode(&image,&serial_probe)!=TERMINAL_IMPORT_OK){status=DIRECTORY_LIVE_SERIAL;goto done;}
 status=directory_dos_read(directory_path,entry,&selection,&directory_io);
 if(status!=DIRECTORY_DOS_OK){
  if(result){result->source_status=status;result->dos_error=directory_io.dos_error;
   result->close_error=directory_io.close_error;result->bytes_processed=directory_io.bytes_processed;}
  status=DIRECTORY_LIVE_DIRECTORY_IO;goto done;
 }
 if(selection.entry_number!=entry){status=DIRECTORY_LIVE_RECORD;goto done;}
 if(context)memcpy(&context_stage.selection,&selection,sizeof(selection));
 status=directory_live_decode(&image,&selection,codes,serial,modem,plan,result);
 if(status==DIRECTORY_LIVE_OK && context)memcpy(context,&context_stage,sizeof(*context));
 return status;
done:
 if(result)result->status=status;
 return status;
}

/* Eight-argument compatibility owner; context capture is opt-in. */
directory_live_status __cdecl directory_live_read(const char *prm_path,
 const char *directory_path,unsigned entry,unsigned codes,
 terminal_import_settings *serial,modem_import_settings *modem,
 directory_live_plan *plan,directory_live_result *result)
{
 return directory_live_read_context(prm_path,directory_path,entry,codes,
  serial,modem,plan,result,0);
}
static unsigned same_path(const char *a,const char *b)
{
 unsigned i,x,y;
 for(i=0;i<64;++i){
  x=(unsigned char)a[i];y=(unsigned char)b[i];
  if(x>='a' && x<='z')x-=32;if(y>='a' && y<='z')y-=32;
  if(x!=y)return 0;if(!x)return 1;
 }
 return 0;
}
unsigned __cdecl directory_live_context_matches(const directory_live_context *context,
 const char *prm_path,const char *directory_path,unsigned entry,unsigned codes)
{
 if(!extent(context,sizeof(*context)) || !path_size(prm_path) ||
  !path_size(directory_path) || !entry || entry>200 || codes>1 ||
  context->selection.entry_number!=entry || context->codes!=codes ||
  !bounded((const unsigned char *)context->prm_path,64) ||
  !bounded((const unsigned char *)context->directory_path,64))return 0;
 return same_path(context->prm_path,prm_path) && same_path(context->directory_path,directory_path);
}
