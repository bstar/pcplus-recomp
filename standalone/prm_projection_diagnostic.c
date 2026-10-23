#include "../src/config/prm_projection.h"
#include <stdio.h>
#include <string.h>
static prm_dos_image baseline,output,saved;
static terminal_import_settings serial,read_serial;
static modem_import_settings modem,read_modem;
static transfer_import_settings transfer,read_transfer;
static unsigned checks,failures;
static void checked(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL line=%u\n",line);}}
#define check(yes) checked((yes),__LINE__)
static unsigned project(void){return prm_project_active(&baseline,&serial,&modem,&transfer,&output);}
static void fixture(void)
{
 unsigned i;
 for(i=0;i<1264;++i)baseline.bytes[i]=(unsigned char)(i*37+129);
 baseline.bytes[0x31c]=0;baseline.bytes[0x42c]=0xef;baseline.bytes[0x42d]=0xbe;
 memset(&serial,0,sizeof(serial));memset(&modem,0,sizeof(modem));memset(&transfer,0,sizeof(transfer));
 serial.port_number=2;serial.baud_low=57600U;serial.data_bits=8;serial.stop_bits=1;
 serial.io_base=0x2f8;serial.irq=3;serial.hardware_flow=1;serial.terminal_id=6;
 serial.normal_attribute=7;serial.bold_attribute=15;serial.preset_attribute=3;
 serial.reverse_attribute=0x70;serial.underline_attribute=1;
 serial.autowrap=serial.scroll_enabled=1;serial.translation_mode=2;serial.clipboard_separator=13;
 serial.mapping_pause_character=modem.command_pause_character='~';
 serial.mapping_character_delay_units=modem.command_character_delay_units=12;
 modem.dial_timeout_seconds=60;modem.redial_pause_seconds=10;modem.dial_abort_character=27;
 modem.autobaud=modem.abort_drop_dtr=1;modem.break_delay_units=65535U;
 strcpy((char *)modem.initialization,"ATZ^M");strcpy((char *)modem.dial_prefix,"ATDT");
 strcpy((char *)modem.dial_suffix,"^M");strcpy((char *)modem.hangup,"+++~ATH0^M");
 strcpy((char *)modem.responses[0],"CONNECT");strcpy((char *)modem.responses[1],"NO CARRIER");
 transfer.auto_download=1;strcpy(transfer.download_directory,".");
 memset(&output,0xcd,sizeof(output));memcpy(&saved,&output,sizeof(saved));
}
static void rejected(unsigned expected)
{memcpy(&saved,&output,sizeof(saved));check(project()==expected);check(!memcmp(&output,&saved,sizeof(output)));}
static void write_file(const char *name,const void *p,unsigned n)
{FILE *f=fopen(name,"wb");check(f!=0);if(f){check(fwrite(p,1,n,f)==n);check(fclose(f)==0);}}
int main(void)
{
 static const unsigned bases[]={0x3f8,0x2f8,0x3e8,0x2e8},irqs[]={4,3,4,3};
 static const unsigned long rates[]={300UL,1200UL,2400UL,4800UL,9600UL,19200UL,38400UL,57600UL,115200UL};
 unsigned p,r,par,bits,stop,i,n,cap;unsigned char *slot;
 fixture();check(project()==PRM_PROJECT_OK);
 check(!terminal_import_decode(&output,&read_serial));check(!memcmp(&serial,&read_serial,sizeof(serial)));
 check(!modem_import_decode(&output,&read_modem));check(!transfer_import_decode(&output,&read_transfer));
 check(read_transfer.auto_download==1 && !strcmp(read_transfer.download_directory,"."));
 check(output.bytes[0x42c]==0xef && output.bytes[0x42d]==0xbe && output.bytes[0x31c]==0);
 write_file("BASE.BIN",&baseline,sizeof(baseline));write_file("ACTIVE.BIN",&output,sizeof(output));
 for(p=1;p<=4;++p)for(r=0;r<9;++r)for(par=0;par<5;++par)for(bits=7;bits<=8;++bits)for(stop=1;stop<=2;++stop){
  serial.port_number=p;serial.io_base=bases[p-1];serial.irq=irqs[p-1];
  serial.baud_low=(unsigned)rates[r];serial.baud_high=(unsigned)(rates[r]>>16);
  serial.parity=par;serial.data_bits=bits;serial.stop_bits=stop;
  check(project()==PRM_PROJECT_OK);check(!terminal_import_decode(&output,&read_serial));
  check(!memcmp(&serial,&read_serial,sizeof(serial)));
 }
 fixture();serial.port_number=0;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.port_number=5;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.baud_low=14400;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.baud_high=1;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.io_base=0x3f8;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.irq=4;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.parity=5;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.data_bits=9;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.stop_bits=0;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.software_flow=2;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.hardware_flow=2;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.terminal_id=5;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.normal_attribute=256;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.bold_attribute=256;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.preset_attribute=256;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.reverse_attribute=256;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.underline_attribute=256;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.autowrap=2;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.scroll_enabled=2;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.translation_mode=3;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.clipboard_separator=256;rejected(PRM_PROJECT_SERIAL);
 fixture();serial.mapping_pause_character=256;rejected(PRM_PROJECT_SERIAL);
 fixture();modem.command_pause_character=256;rejected(PRM_PROJECT_MODEM);
 fixture();modem.dial_abort_character=256;rejected(PRM_PROJECT_MODEM);
 fixture();++serial.mapping_pause_character;rejected(PRM_PROJECT_SHARED);
 fixture();++serial.mapping_character_delay_units;rejected(PRM_PROJECT_SHARED);
 fixture();modem.dial_timeout_seconds=0;rejected(PRM_PROJECT_MODEM);
 fixture();modem.dial_timeout_seconds=32768U;rejected(PRM_PROJECT_MODEM);
 fixture();modem.autobaud=2;rejected(PRM_PROJECT_MODEM);
 fixture();modem.abort_drop_dtr=2;rejected(PRM_PROJECT_MODEM);
 fixture();modem.initialize_while_connected=2;rejected(PRM_PROJECT_MODEM);
 fixture();modem.redial_pause_seconds=32768U;rejected(PRM_PROJECT_MODEM);
 fixture();modem.dial_cycle_limit=32768U;rejected(PRM_PROJECT_MODEM);
 fixture();serial.mapping_character_delay_units=modem.command_character_delay_units=32768U;rejected(PRM_PROJECT_MODEM);
 for(i=0;i<17;++i){
  fixture();cap=i==0?47:i<6?25:16;
  if(i==0)slot=modem.initialization;else if(i==1)slot=modem.dial_prefix;
  else if(i==2)slot=modem.dial_suffix;else if(i==3)slot=modem.hangup;
  else if(i==4)slot=modem.answer_on;else if(i==5)slot=modem.answer_off;
  else slot=modem.responses[i-6];
  for(n=0;n<cap;++n){memset(slot,0xda,cap);slot[n]=0;check(project()==PRM_PROJECT_OK);}
  memset(slot,'X',cap);rejected(PRM_PROJECT_MODEM);
  if(i<6){slot[0]='^';slot[1]=0;rejected(PRM_PROJECT_MODEM);}
 }
 fixture();transfer.auto_download=2;rejected(PRM_PROJECT_TRANSFER);
 fixture();strcpy(transfer.download_directory,"..\\SECRET");rejected(PRM_PROJECT_TRANSFER);
 fixture();memset(transfer.download_directory,'A',64);rejected(PRM_PROJECT_TRANSFER);
 fixture();transfer.auto_download=0;check(project()==PRM_PROJECT_OK);
 check(!output.bytes[0x42c] && !output.bytes[0x42d]);
 fixture();strcpy(transfer.download_directory,"D:\\FILES");check(project()==PRM_PROJECT_OK);
 check(!strcmp((char *)output.bytes+0x31c,"D:\\FILES"));
 fixture();baseline.bytes[0x42c]=baseline.bytes[0x42d]=0;check(project()==PRM_PROJECT_OK);
 check(output.bytes[0x42c]==1 && !output.bytes[0x42d]);
 fixture();check(prm_project_active(0,&serial,&modem,&transfer,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,0,&modem,&transfer,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,&serial,0,&transfer,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,&serial,&modem,0,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,&serial,&modem,&transfer,0)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,&serial,&modem,&transfer,&baseline)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,(terminal_import_settings *)&baseline,&modem,&transfer,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active((prm_dos_image *)0xfff0,&serial,&modem,&transfer,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,(terminal_import_settings *)0xfff0,&modem,&transfer,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,&serial,(modem_import_settings *)0xfff0,&transfer,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,&serial,&modem,(transfer_import_settings *)0xfff0,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_active(&baseline,&serial,&modem,&transfer,(prm_dos_image *)0xfff0)==PRM_PROJECT_ARGUMENT);
 check(!memcmp(&output,&saved,sizeof(output)));
 /* An inactive modem is explicit, not a zero-filled active plan. Even bad
  * private baseline commands/flags survive; shared serial fields and current
  * BREAK still project. Existing all-active entry keeps rejecting NULL. */
 fixture();memset(baseline.bytes+0x0a,0xff,0x174-0x0a);
 check(prm_project_session(&baseline,&serial,0,&transfer,350,&output)==PRM_PROJECT_OK);
 check(!memcmp(output.bytes+0x0a,baseline.bytes+0x0a,0x174-0x0a));
 check(output.bytes[0x1a4]==94 && output.bytes[0x1a5]==1);
 check(!terminal_import_decode(&output,&read_serial));
 check(!memcmp(&serial,&read_serial,sizeof(serial)));
 write_file("INBASE.BIN",&baseline,sizeof(baseline));write_file("INACTIVE.BIN",&output,sizeof(output));
 for(i=0;i<3;++i){
  n=i==0?0:i==1?350:65535U;
  check(prm_project_session(&baseline,&serial,0,&transfer,n,&output)==PRM_PROJECT_OK);
  check((output.bytes[0x1a4]|((unsigned)output.bytes[0x1a5]<<8))==n);
 }
 fixture();check(prm_project_session(&baseline,&serial,&modem,&transfer,123,&output)==PRM_PROJECT_OK);
 check(output.bytes[0x1a4]==123 && !output.bytes[0x1a5]);
 fixture();++modem.command_pause_character;
 check(prm_project_session(&baseline,&serial,&modem,&transfer,350,&output)==PRM_PROJECT_SHARED);
 check(!memcmp(&output,&saved,sizeof(output)));
 fixture();modem.dial_timeout_seconds=0;
 check(prm_project_session(&baseline,&serial,&modem,&transfer,350,&output)==PRM_PROJECT_MODEM);
 check(!memcmp(&output,&saved,sizeof(output)));
 fixture();check(prm_project_session(&baseline,0,0,&transfer,350,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_session(&baseline,&serial,0,0,350,&output)==PRM_PROJECT_ARGUMENT);
 check(prm_project_session(&baseline,&serial,0,&transfer,350,&baseline)==PRM_PROJECT_ARGUMENT);
 check(prm_project_session(&baseline,&serial,(modem_import_settings *)0xfff0,&transfer,350,&output)==PRM_PROJECT_ARGUMENT);
 check(!memcmp(&output,&saved,sizeof(output)));
 printf("PRMPROJECT checks=%u failures=%u\n",checks,failures);return failures?1:0;
}
