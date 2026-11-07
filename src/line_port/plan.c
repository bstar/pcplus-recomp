#include "plan.h"
#include "session.h"
#define TEXT __based(__segname("_CODE"))
static const unsigned long TEXT rates[]={300UL,1200UL,2400UL,4800UL,9600UL,19200UL,38400UL,57600UL,115200UL};
static const unsigned TEXT bases[]={0x3f8,0x2f8,0x3e8,0x2e8};
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned irq(unsigned v)
{return v==3 || v==4 || v==5 || v==7;}
static unsigned valid(const line_port_values *v)
{return v->port<4 && v->baud<9 && v->parity<5 &&
 (v->stop==1 || v->stop==2) && (v->bits==7 || v->bits==8);}
static unsigned word(const prm_dos_image *p,unsigned at)
{return p->bytes[at]|((unsigned)p->bytes[at+1]<<8);}
unsigned __far __cdecl line_port_from_serial(const terminal_import_settings *serial,line_port_values *v)
{
 line_port_values next;unsigned long baud;unsigned i;
 if(!extent(serial,sizeof(*serial)) || !extent(v,sizeof(*v)) ||
    !separate(serial,sizeof(*serial),v,sizeof(*v)))return LINE_PORT_ARGUMENT;
 if(serial->port_number<1 || serial->port_number>4 || serial->parity>4 ||
    (serial->data_bits!=7 && serial->data_bits!=8) || (serial->stop_bits!=1 && serial->stop_bits!=2) ||
    serial->io_base!=bases[serial->port_number-1] || !irq(serial->irq) ||
    serial->software_flow>1 || serial->hardware_flow>1)return LINE_PORT_ARGUMENT;
 baud=serial->baud_low|((unsigned long)serial->baud_high<<16);
 for(i=0;i<9;++i)if(rates[i]==baud)break;
 if(i==9)return LINE_PORT_UNSUPPORTED;
 next.port=serial->port_number-1;next.baud=i;next.parity=serial->parity;
 next.stop=serial->stop_bits;next.bits=serial->data_bits;
 *v=next;return 0;
}
unsigned __far __cdecl line_port_plan_make(const terminal_import_settings *serial,
 const line_port_values *v,const prm_dos_image *prm,line_port_plan *out)
{
 line_port_plan next;line_port_values before;unsigned i,words[5];unsigned long baud;
 if(!extent(serial,sizeof(*serial)) || !extent(v,sizeof(*v)) ||
    !extent(prm,sizeof(*prm)) || !extent(out,sizeof(*out)) ||
    !separate(out,sizeof(*out),serial,sizeof(*serial)) || !separate(out,sizeof(*out),v,sizeof(*v)) ||
    !separate(out,sizeof(*out),prm,sizeof(*prm)) || !valid(v))return LINE_PORT_ARGUMENT;
 if(line_port_from_serial(serial,&before))return LINE_PORT_ARGUMENT;
 next.serial=*serial;next.serial.port_number=v->port+1;
 baud=rates[v->baud];next.serial.baud_low=(unsigned)baud;next.serial.baud_high=(unsigned)(baud>>16);
 next.serial.parity=v->parity;next.serial.stop_bits=v->stop;next.serial.data_bits=v->bits;
 next.change_mask=0;
 if(before.port!=v->port){
  next.serial.io_base=word(prm,0x174+v->port*2);next.serial.irq=word(prm,0x184+v->port*2);
  if(next.serial.io_base!=bases[v->port] || !irq(next.serial.irq))return LINE_PORT_UNSUPPORTED;
  next.change_mask|=1;
 }
 if(before.baud!=v->baud)next.change_mask|=2;
 if(before.parity!=v->parity || before.stop!=v->stop || before.bits!=v->bits)next.change_mask|=4;
 words[0]=v->port;words[1]=v->baud;words[2]=v->parity;words[3]=v->stop;words[4]=v->bits;
 for(i=0;i<5;++i){next.prefix[2*i]=(unsigned char)words[i];next.prefix[2*i+1]=(unsigned char)(words[i]>>8);}
 *out=next;return 0;
}
