BITS 16
CPU 8086
SEGMENT NOTICECODE public class=CODE use16
extern _notice_key_pending_native
global _notice_test_key_pending
_notice_test_key_pending:
 call _notice_key_pending_native
 retf
