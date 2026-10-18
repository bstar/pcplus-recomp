#ifndef PCPLUS_YMODEM_H
#define PCPLUS_YMODEM_H
/* Maintained CRC YMODEM foreground session. Near cdecl, DS=SS. Uses the
 * exclusive native session arena; ordinary XMODEM must not run concurrently.
 * IO read returns a byte or 0xffff; poll distinguishes timeout from a fault.
 * unread restores only the immediately preceding count bytes, or fails. */
enum { YM_OK=0,YM_ARGUMENT,YM_IO,YM_TIMEOUT,YM_CANCEL,YM_PROTOCOL,
 YM_HEADER,YM_FILE,YM_LENGTH,YM_RECOVERY,YM_END_UNCONFIRMED };
typedef struct ymodem_result {
 unsigned status,direction,phase,blocks,last_file_status;
 unsigned long files,bytes;
 char name[13];
} ymodem_result;
extern ymodem_result ymodem_current;
extern unsigned char terminal_batch_buffer[];
unsigned __cdecl ymodem_run(const char *path,unsigned sending);
unsigned __cdecl ymodem_io_read(unsigned seconds);
unsigned __cdecl ymodem_io_put(unsigned value);
unsigned __cdecl ymodem_io_poll(void);
unsigned __cdecl ymodem_io_unread(unsigned count);
void __cdecl ymodem_io_progress(void);
#endif
