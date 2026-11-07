BITS 16
CPU 8086
SEGMENT KEY_TEST_STATE public align=16 class=FARSTATE use16
GROUP KEY_TEST_STATE_GROUP KEY_TEST_STATE
global _key_records
_key_records: times 1620 db 0
