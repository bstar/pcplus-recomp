#include <stdio.h>
#include "../src/line_port/session.h"
#include "../src/line_port/plan.h"
#include <string.h>
static line_port_session session;
static line_port_values initial={0,5,0,1,8},request;
static terminal_import_settings actual;
static prm_dos_image prm;
static line_port_plan proposal;
static unsigned frame[2000],events,save,checks;
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL %u\n",checks);return 1;}}while(0)
int main(void)
{
 unsigned i;FILE *file;
 CHECK(!line_port_session_begin(&session,&initial));
 CHECK(!line_port_view(&session.selected,frame,2000));
 file=fopen("POPUP.BIN","wb");CHECK(file!=0);
 CHECK(fwrite(frame,2,2000,file)==2000);CHECK(!fclose(file));
 CHECK(!line_port_session_key(&session,'5',&events));CHECK(!events && session.selected.baud==4);
 CHECK(!line_port_session_key(&session,'e',&events));CHECK(session.selected.parity==2);
 CHECK(!line_port_session_key(&session,27,&events));CHECK(session.phase==LINE_PORT_REQUEST && !session.save);
 CHECK(!line_port_session_request(&session,&request,&save));CHECK(!save && request.baud==4 && request.parity==2);
 CHECK(line_port_session_applied(&session,1)==LINE_PORT_APPLY_FAILED);
 CHECK(session.phase==LINE_PORT_REQUEST && session.selected.baud==4);
 CHECK(!line_port_session_applied(&session,0));CHECK(session.phase==LINE_PORT_DONE);
 CHECK(initial.baud==5 && initial.parity==0);
 CHECK(!line_port_session_begin(&session,&initial));
 CHECK(!line_port_session_key(&session,'7',&events));CHECK(!line_port_session_key(&session,0x1200,&events));
 CHECK(session.selected.baud==6 && session.selected.bits==7 && session.selected.parity==2 && session.selected.stop==1);
 CHECK(!line_port_session_key(&session,0x1f00,&events));
 CHECK(line_port_session_applied(&session,0)==LINE_PORT_ARGUMENT);
 CHECK(!line_port_session_request(&session,&request,&save));CHECK(save==1);
 CHECK(line_port_session_saved(&session,1,0)==LINE_PORT_SAVE_FAILED);CHECK(session.phase==LINE_PORT_EDIT);
 CHECK(!line_port_session_key(&session,0x1f00,&events));CHECK(!line_port_session_saved(&session,0,0));
 CHECK(session.phase==LINE_PORT_SAVED);
 CHECK(line_port_session_applied(&session,1)==LINE_PORT_APPLY_FAILED);
 CHECK(!line_port_session_request(&session,&request,&save));CHECK(!save && request.baud==6);
 CHECK(!line_port_session_applied(&session,0));
 CHECK(!line_port_session_begin(&session,&initial));
 CHECK(line_port_session_key(&session,0x3f00,&events)==LINE_PORT_UNSUPPORTED);
 CHECK(events==1 && session.selected.port==0 && !session.quiesce_requests);
 CHECK(!line_port_session_key(&session,0x3b00,&events));CHECK(events==2 && session.quiesce_requests==1);
 CHECK(!line_port_session_key(&session,0x3e00,&events));CHECK(events==2 && session.selected.port==3 && session.quiesce_requests==2);
 CHECK(!line_port_session_key(&session,0xffff,&events));CHECK(events==1 && session.selected.port==3);
 CHECK(line_port_session_key(&session,'1',&session.phase)==LINE_PORT_ARGUMENT);
 CHECK(!line_port_session_key(&session,0x1f00,&events));
 CHECK(line_port_session_saved(&session,1,1)==LINE_PORT_LOCKED);
 CHECK(line_port_session_key(&session,27,&events)==LINE_PORT_LOCKED);
 CHECK(line_port_session_request(&session,&request,&save)==LINE_PORT_ARGUMENT);
 CHECK(line_port_session_begin(&session,&initial)==LINE_PORT_LOCKED);
 for(i=0;i<5;++i){
  line_port_values bad=initial;unsigned invalid[]={4,9,5,0,9};
  ((unsigned *)&bad)[i]=invalid[i];
  CHECK(line_port_session_begin(&session,&bad)==LINE_PORT_ARGUMENT);
 }
 actual.port_number=3;actual.baud_low=19200;actual.data_bits=8;actual.stop_bits=1;
 actual.io_base=0x3e8;actual.irq=5;actual.hardware_flow=1;actual.terminal_id=6;
 actual.clipboard_separator='!';
 CHECK(!line_port_from_serial(&actual,&request));CHECK(request.port==2 && request.baud==5);
 CHECK(!line_port_plan_make(&actual,&request,&prm,&proposal));CHECK(!proposal.change_mask);
 CHECK(proposal.serial.io_base==0x3e8 && proposal.serial.irq==5 && proposal.serial.hardware_flow==1);
 request.baud=8;request.parity=2;request.bits=7;
 CHECK(!line_port_plan_make(&actual,&request,&prm,&proposal));CHECK(proposal.change_mask==6);
 CHECK(proposal.serial.baud_high==1 && proposal.serial.baud_low==49664);
 CHECK(proposal.serial.clipboard_separator=='!' && proposal.serial.terminal_id==6);
 CHECK(proposal.prefix[0]==2 && proposal.prefix[2]==8 && proposal.prefix[4]==2 && proposal.prefix[6]==1 && proposal.prefix[8]==7);
 request.port=1;
 CHECK(line_port_plan_make(&actual,&request,&prm,&proposal)==LINE_PORT_UNSUPPORTED);
 prm.bytes[0x176]=0xf8;prm.bytes[0x177]=2;prm.bytes[0x186]=7;
 CHECK(!line_port_plan_make(&actual,&request,&prm,&proposal));CHECK(proposal.change_mask==7);
 CHECK(proposal.serial.io_base==0x2f8 && proposal.serial.irq==7);
 CHECK(actual.port_number==3 && actual.baud_low==19200 && actual.irq==5);
 actual.baud_low=12345;
 CHECK(line_port_from_serial(&actual,&request)==LINE_PORT_UNSUPPORTED);
 printf("PASS %u\n",checks);return 0;
}
