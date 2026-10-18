#include "capture_session.h"
extern unsigned terminal_sink_398a_enabled,terminal_sink_398c_disabled;
unsigned capture_session_notice=0,capture_session_failed=0;
unsigned capture_session_buffered=0;
static unsigned cookie=0xc510;
static unsigned char buffer[256];
static unsigned long observed=0,pending_since=0;
#define BIOS_DAY 0x1800b0UL
static unsigned failed(unsigned status)
{
 if(!capture_session_failed)capture_session_failed=status;
 terminal_sink_398a_enabled=terminal_sink_398c_disabled=0;
 /* A poisoned exact-write owner cannot retry its remaining bytes. Close once;
  * an ambiguous close remains owned/uncertain until process termination. */
 capture_file_cleanup();capture_session_notice=CS_ERROR;return status;
}
unsigned __cdecl capture_session_initialize(void)
{
 unsigned status;
 if(cookie==0xc511)return CF_OK;
 if(cookie!=0xc510)return CF_STATE;
 status=capture_file_initialize();if(status)return status;
 terminal_sink_398a_enabled=terminal_sink_398c_disabled=0;
 capture_session_notice=capture_session_failed=capture_session_buffered=0;
 observed=pending_since=0;cookie=0xc511;return CF_OK;
}
unsigned __cdecl capture_session_begin(const char *path,unsigned long ticks)
{
 unsigned status;
 if(cookie!=0xc511)return CF_STATE;
 if(terminal_sink_398a_enabled)return CF_BUSY;
 if(!capture_file_validate_path(path,1))return CF_ARGUMENT;
 if(!*path)path="PCPLUS.LOG";
 /* APPEND never creates. Only an actual file-not-found result permits NEW;
  * creatnew then refuses a raced-in file instead of truncating it. */
 status=capture_file_begin(path,CF_APPEND);
 if(status==CF_INSPECT && capture_file_result.dos_error==2)
  status=capture_file_begin(path,CF_NEW);
 if(status){
  capture_session_notice=CS_DENIED;
  if(capture_file_result.handle_uncertain)return failed(status);
  return status;
 }
 capture_session_buffered=0;observed=pending_since=ticks;
 terminal_sink_398c_disabled=0;terminal_sink_398a_enabled=1;
 capture_session_notice=CS_OPEN;return CF_OK;
}
unsigned __cdecl capture_session_flush(void)
{
 unsigned status;
 if(cookie!=0xc511)return CF_STATE;
 if(!terminal_sink_398a_enabled || !capture_session_buffered)return CF_OK;
 status=capture_file_append(buffer,capture_session_buffered);
 if(status)return failed(status);
 capture_session_buffered=0;return CF_OK;
}
unsigned __cdecl capture_session_put(unsigned character,unsigned unused_handle)
{
 unsigned need,status;
 (void)unused_handle;
 if(cookie!=0xc511 || !terminal_sink_398a_enabled || terminal_sink_398c_disabled)return 0xffff;
 character&=255;
 need=character==10?2:1;
 if(capture_session_buffered+need>sizeof(buffer)){
  status=capture_session_flush();if(status)return 0xffff;
 }
 if(!capture_session_buffered)pending_since=observed;
 /* Native capture opens in text mode; its lower a368 writer inserts CR before
  * LF. Keep the checked DOS sink binary and perform that translation here. */
 if(character==10)buffer[capture_session_buffered++]=13;
 buffer[capture_session_buffered++]=(unsigned char)character;
 if(capture_session_buffered==sizeof(buffer) && capture_session_flush())return 0xffff;
 return (unsigned char)character;
}
unsigned __cdecl capture_session_stop(void)
{
 unsigned status,closed,active;
 if(cookie!=0xc511)return CF_STATE;
 active=terminal_sink_398a_enabled;
 status=capture_session_flush();
 terminal_sink_398a_enabled=terminal_sink_398c_disabled=0;
 /* Rejected opens may retain a diagnostic first_status without acquiring a
  * handle. They are UI errors, not failed capture writes or exit failures. */
 closed=CF_OK;
 if(capture_file_result.handle_open || capture_file_result.handle_uncertain)
  closed=capture_file_cleanup();
 if(status || closed)return failed(status?status:closed);
 if(active)capture_session_notice=CS_CLOSED;
 return CF_OK;
}
unsigned __cdecl capture_session_pause(void)
{
 unsigned status;
 if(cookie!=0xc511)return CF_STATE;
 if(!terminal_sink_398a_enabled)return CF_OK;
 status=capture_session_flush();if(status)return status;
 terminal_sink_398c_disabled=!terminal_sink_398c_disabled;
 capture_session_notice=terminal_sink_398c_disabled?CS_HOLD:CS_OPEN;return CF_OK;
}
void __cdecl capture_session_poll(unsigned long ticks)
{
 unsigned long elapsed;
 if(cookie!=0xc511)return;
 observed=ticks;
 if(!terminal_sink_398a_enabled || !capture_session_buffered)return;
 if(ticks>=BIOS_DAY || pending_since>=BIOS_DAY)elapsed=18;
 else elapsed=ticks>=pending_since?ticks-pending_since:BIOS_DAY-pending_since+ticks;
 if(elapsed>=18)capture_session_flush();
}
unsigned __cdecl capture_session_shutdown(void)
{
 unsigned status;
 if(cookie!=0xc511)return CF_STATE;
 status=capture_session_stop();
 return capture_session_failed?capture_session_failed:status;
}
