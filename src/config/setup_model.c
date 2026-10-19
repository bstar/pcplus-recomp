#include "setup_model.h"
#include "terminal_import.h"
#include "modem_import.h"
#include "transfer_import.h"
#include <string.h>

enum { DECIMAL, HEXWORD, PORT, BAUD, PARITY, BITS, PROFILE, COMMAND, RESPONSE,
 BASE, IRQ, PATH };
typedef struct descriptor {
 setup_field_info info;
 unsigned offset,kind,minimum,maximum;
} descriptor;
#define F(label,help,page,at,kind,lo,hi) {{label,help,page},at,kind,lo,hi}
static const descriptor fields[SETUP_FIELD_COUNT]={
 F("Port","COM 1..4; selecting a port installs its standard base and IRQ.",0,0,PORT,1,4),
 F("Baud","300 1200 2400 4800 9600 19200 38400 57600 115200",0,2,BAUD,0,8),
 F("Data bits","7 or 8",0,8,BITS,7,8),
 F("Parity","N O E M S",0,4,PARITY,0,4),
 F("Stop bits","1 or 2",0,6,DECIMAL,1,2),
 F("Software flow","0 disabled, 1 enabled",0,0x198,DECIMAL,0,1),
 F("Hardware flow","0 disabled, 1 enabled",0,0x19a,DECIMAL,0,1),
 F("I/O base","Hex; standard base for selected COM port only.",0,0,BASE,0,0),
 F("IRQ","Standard IRQ for selected COM port only.",0,0,IRQ,0,0),
 F("Terminal profile","Supported profile ID: 4 (VT220), 6 (ANSI)",1,0x194,PROFILE,4,6),
 F("Autowrap","0 disabled, 1 enabled",1,0x19c,DECIMAL,0,1),
 F("Scrolling","0 disabled, 1 enabled",1,0x19e,DECIMAL,0,1),
 F("Normal color","Hex text attribute 00..FF",1,0x1ae,HEXWORD,0,255),
 F("Bold color","Hex text attribute 00..FF",1,0x1b0,HEXWORD,0,255),
 F("Preset color","Hex text attribute 00..FF",1,0x1b2,HEXWORD,0,255),
 F("Reverse color","Hex text attribute 00..FF",1,0x1b4,HEXWORD,0,255),
 F("Underline color","Hex text attribute 00..FF",1,0x1b6,HEXWORD,0,255),
 F("Dial timeout","Seconds 1..32767",2,0xa,DECIMAL,1,32767),
 F("Redial pause","Seconds 0..32767",2,0xc,DECIMAL,0,32767),
 F("Autobaud","0 disabled, 1 enabled",2,0xe,DECIMAL,0,1),
 F("Abort drops DTR","0 disabled, 1 enabled",2,0x10,DECIMAL,0,1),
 F("Abort character","Byte value 0..255",2,0x12,DECIMAL,0,255),
 F("Initialize connected","0 disabled, 1 enabled",2,0x14,DECIMAL,0,1),
 F("Dial cycle limit","0 unlimited, otherwise 1..32767",2,0x16,DECIMAL,0,32767),
 F("Command delay","Nominal 1/55 BIOS-tick units, 0..32767",2,0x1e4,DECIMAL,0,32767),
 F("Pause character","Byte value 0..255",2,0x1e2,DECIMAL,0,255),
 F("BREAK delay","Nominal 1/55 BIOS-tick units, 0..65535",2,0x1a4,DECIMAL,0,65535),
 F("Initialization","Caret notation; at most 46 bytes",3,0x18,COMMAND,0,47),
 F("Dial prefix","Caret notation; at most 24 bytes",3,0x47,COMMAND,0,25),
 F("Dial suffix","Caret notation; at most 24 bytes",3,0x60,COMMAND,0,25),
 F("Hangup","Caret notation; at most 24 bytes",3,0x79,COMMAND,0,25),
 F("Autoanswer on","Caret notation; at most 24 bytes",3,0x92,COMMAND,0,25),
 F("Autoanswer off","Caret notation; at most 24 bytes",3,0xab,COMMAND,0,25),
 F("Response 1","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0xc4,RESPONSE,0,16),
 F("Response 2","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0xd4,RESPONSE,0,16),
 F("Response 3","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0xe4,RESPONSE,0,16),
 F("Response 4","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0xf4,RESPONSE,0,16),
 F("Response 5","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0x104,RESPONSE,0,16),
 F("Response 6","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0x114,RESPONSE,0,16),
 F("Response 7","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0x124,RESPONSE,0,16),
 F("Response 8","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0x134,RESPONSE,0,16),
 F("Response 9","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0x144,RESPONSE,0,16),
 F("Response 10","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0x154,RESPONSE,0,16),
 F("Response 11","Expanded bytes as hex pairs; max 15 bytes; no 00.",4,0x164,RESPONSE,0,16),
 F("Input translation","0 identity; 1 PCPLUS.XLT; 2 strip high bit. Changes need restart.",1,0x1e0,DECIMAL,0,2),
 F("Clipboard separator","Byte after each all/tagged name: 13 CR, 32 space, 0..255.",1,0x4ea,DECIMAL,0,255),
 F("Auto Download","0 disabled; any nonzero word enables ZMODEM automatic reception.",1,0x42c,DECIMAL,0,65535),
 F("Download directory","DOS 8.3 directory; empty uses current directory. Checked at transfer start.",1,0x31c,PATH,0,64)
};
static const unsigned bases[]={0x3f8,0x2f8,0x3e8,0x2e8};
static const unsigned irqs[]={4,3,4,3};
static const unsigned long rates[]={300UL,1200UL,2400UL,4800UL,9600UL,19200UL,38400UL,57600UL,115200UL};
static const char hex[]="0123456789ABCDEF";
static unsigned extent(const void *p,unsigned size)
{ return p && (unsigned long)(unsigned)p+size<=65536UL; }
static unsigned separate(const void *a,unsigned as,const void *b,unsigned bs)
{ return (unsigned long)(unsigned)a+as<=(unsigned)b || (unsigned long)(unsigned)b+bs<=(unsigned)a; }
static unsigned word(const prm_dos_image *im,unsigned at)
{ return im->bytes[at]|((unsigned)im->bytes[at+1]<<8); }
static void putword(prm_dos_image *im,unsigned at,unsigned v)
{ im->bytes[at]=(unsigned char)v;im->bytes[at+1]=(unsigned char)(v>>8); }
static unsigned bytefield(unsigned at) { return at==0x12 || at==0x1e2; }
static unsigned length(const char *s,unsigned cap)
{ unsigned i;for(i=0;i<cap && s[i];++i);return i; }
static unsigned caret_ok(const char *s,unsigned len)
{
 unsigned i;
 for(i=0;i<len;++i)if(s[i]=='^'){
  if(++i==len)return 0;
  if(s[i]=='^' && i+1<len && s[i+1]=='^')++i;
 }
 return 1;
}
static int digit(char c)
{
 if(c>='0' && c<='9')return c-'0';
 if(c>='a' && c<='f')return c-'a'+10;
 if(c>='A' && c<='F')return c-'A'+10;
 return -1;
}
static unsigned parse(const char *s,unsigned len,unsigned radix,unsigned long *out)
{
 unsigned i;unsigned long n=0;int d;
 if(!len)return 0;
 for(i=0;i<len;++i){
  d=digit(s[i]);if(d<0 || (unsigned)d>=radix)return 0;
  if(n>(115200UL-(unsigned)d)/radix)return 0;
  n=n*radix+(unsigned)d;
 }
 *out=n;return 1;
}
static void decimal(char *s,unsigned long value)
{
 char reverse[6];unsigned n=0,i;
 do {reverse[n++]=(char)('0'+value%10);value/=10;}while(value);
 for(i=0;i<n;++i)s[i]=reverse[n-i-1];s[n]=0;
}
const setup_field_info * __cdecl setup_field(unsigned index)
{ return index<SETUP_FIELD_COUNT?&fields[index].info:0; }
setup_status __cdecl setup_get(const prm_dos_image *image,unsigned index,char *text,unsigned capacity)
{
 const descriptor *f;char tmp[SETUP_TEXT_SIZE];unsigned v,at,n,i,k=0;
 if(index>=SETUP_FIELD_COUNT || !extent(image,sizeof(*image)) ||
  !extent(text,capacity) || !capacity || !separate(image,sizeof(*image),text,capacity))return SETUP_ARGUMENT;
 f=&fields[index];at=f->offset;
 if(f->kind==BASE || f->kind==IRQ){
  v=word(image,0);if(v>3)return SETUP_STORED_VALUE;
  at=(f->kind==BASE?0x174:0x184)+v*2;
 }
 if(f->kind==COMMAND || f->kind==RESPONSE || f->kind==PATH){
  n=length((const char *)image->bytes+at,f->maximum);
  if(n==f->maximum || (f->kind==COMMAND && !caret_ok((const char *)image->bytes+at,n)))return SETUP_STORED_VALUE;
  if(f->kind==PATH && !transfer_import_path((const char *)image->bytes+at,f->maximum))return SETUP_STORED_VALUE;
  if(f->kind==COMMAND || f->kind==PATH){memcpy(tmp,image->bytes+at,n+1);}
  else {
   for(i=0;i<n;++i){
    if(i)tmp[k++]=' ';
    v=image->bytes[at+i];tmp[k++]=hex[v>>4];tmp[k++]=hex[v&15];
   }
   tmp[k]=0;
  }
 }else{
  v=bytefield(at)?image->bytes[at]:word(image,at);
  switch(f->kind){
   case PORT:if(v>3)return SETUP_STORED_VALUE;decimal(tmp,v+1);break;
   case BAUD:if(v>8)return SETUP_STORED_VALUE;decimal(tmp,rates[v]);break;
   case PARITY:if(v>4)return SETUP_STORED_VALUE;tmp[0]="NOEMS"[v];tmp[1]=0;break;
   case PROFILE:if(v!=4 && v!=6)return SETUP_STORED_VALUE;decimal(tmp,v);break;
   case BASE:
    if(v!=bases[word(image,0)])return SETUP_STORED_VALUE;
    /* fall through */
   case HEXWORD:
    if(f->kind==HEXWORD && v>255)return SETUP_STORED_VALUE;
    n=f->kind==BASE?4:2;
    for(i=0;i<n;++i)tmp[i]=hex[(v>>((n-i-1)*4))&15];tmp[n]=0;break;
   case IRQ:if(v!=irqs[word(image,0)])return SETUP_STORED_VALUE;decimal(tmp,v);break;
   default:if(v<f->minimum || v>f->maximum)return SETUP_STORED_VALUE;decimal(tmp,v);
  }
 }
 n=length(tmp,sizeof(tmp))+1;if(n>capacity)return SETUP_ARGUMENT;
 memcpy(text,tmp,n);return SETUP_OK;
}
setup_status __cdecl setup_set(const prm_dos_image *baseline,prm_dos_image *staged,
 unsigned index,const char *text)
{
 const descriptor *f;unsigned len,at,v=0,i,n=0,p;unsigned long value;
 unsigned char bytes[64];
 if(index>=SETUP_FIELD_COUNT || !extent(baseline,sizeof(*baseline)) ||
  !extent(staged,sizeof(*staged)) || !extent(text,SETUP_TEXT_SIZE) ||
  !separate(baseline,sizeof(*baseline),staged,sizeof(*staged)) ||
  !separate(baseline,sizeof(*baseline),text,SETUP_TEXT_SIZE) ||
  !separate(staged,sizeof(*staged),text,SETUP_TEXT_SIZE))return SETUP_ARGUMENT;
 len=length(text,SETUP_TEXT_SIZE);if(len==SETUP_TEXT_SIZE)return SETUP_VALUE;
 f=&fields[index];at=f->offset;
 if(f->kind==COMMAND || f->kind==PATH){
  if(len>=f->maximum || (f->kind==COMMAND && !caret_ok(text,len)) ||
   (f->kind==PATH && !transfer_import_path(text,len+1)))return SETUP_VALUE;
  n=len;memcpy(bytes,text,len);
 }else if(f->kind==RESPONSE){
  i=0;
  while(i<len){
   if(i+1>=len || n==15 || digit(text[i])<0 || digit(text[i+1])<0)return SETUP_VALUE;
   v=(unsigned)(digit(text[i])*16+digit(text[i+1]));if(!v)return SETUP_VALUE;
   bytes[n++]=(unsigned char)v;i+=2;
   if(i<len && text[i++]!=' ')return SETUP_VALUE;
   if(i==len && text[i-1]==' ')return SETUP_VALUE;
  }
 }else if(f->kind==PARITY){
  char c;
  if(len!=1)return SETUP_VALUE;
  c=text[0];if(c>='a' && c<='z')c=(char)(c-'a'+'A');
  for(v=0;v<5 && "NOEMS"[v]!=c;++v);if(v==5)return SETUP_VALUE;
 }else{
  if(!parse(text,len,(f->kind==HEXWORD || f->kind==BASE)?16:10,&value))return SETUP_VALUE;
  if(f->kind==BAUD){
   for(v=0;v<9 && rates[v]!=value;++v);if(v==9)return SETUP_VALUE;
  }else{
   if(value>65535UL)return SETUP_VALUE;v=(unsigned)value;
   if(f->kind==BASE || f->kind==IRQ){
    p=word(staged,0);if(p>3)return SETUP_VALUE;
    if(v!=(f->kind==BASE?bases[p]:irqs[p]))return SETUP_VALUE;
    at=(f->kind==BASE?0x174:0x184)+p*2;
   }else if(v<f->minimum || v>f->maximum || (f->kind==PROFILE && v!=4 && v!=6))return SETUP_VALUE;
  }
 }
 /* Nothing above mutates staged. Commit only after full parse. */
 if(f->kind==COMMAND || f->kind==RESPONSE || f->kind==PATH){
  memcpy(staged->bytes+at,baseline->bytes+at,f->maximum);
  memcpy(staged->bytes+at,bytes,n);staged->bytes[at+n]=0;
 }else if(f->kind==PORT){
  --v;putword(staged,0,v);putword(staged,0x174+v*2,bases[v]);putword(staged,0x184+v*2,irqs[v]);
 }else if(bytefield(at))staged->bytes[at]=(unsigned char)v;
 else putword(staged,at,v);
 return SETUP_OK;
}
setup_status __cdecl setup_validate(const prm_dos_image *image,unsigned *bad_field)
{
 terminal_import_settings terminal;modem_import_settings modem;
 char text[SETUP_TEXT_SIZE];unsigned i;
 if(!extent(image,sizeof(*image)) || !extent(bad_field,sizeof(*bad_field)) ||
  !separate(image,sizeof(*image),bad_field,sizeof(*bad_field)))return SETUP_ARGUMENT;
 for(i=0;i<SETUP_FIELD_COUNT;++i)if(setup_get(image,i,text,sizeof(text))!=SETUP_OK){
  *bad_field=i;return SETUP_STORED_VALUE;
 }
 *bad_field=SETUP_NO_FIELD;
 if(terminal_import_decode(image,&terminal)!=TERMINAL_IMPORT_OK ||
  modem_import_decode(image,&modem)!=MODEM_IMPORT_OK)return SETUP_STORED_VALUE;
 return SETUP_OK;
}
