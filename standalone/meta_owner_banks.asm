BITS 16
CPU 8086
SEGMENT META_OWNER_TEST public align=16 class=FARSTATE use16
GROUP META_OWNER_TEST_GROUP META_OWNER_TEST
global _owner,_other_owner,_live,_changed
_owner: times 1518 db 0
_other_owner: times 1518 db 0
_live: times 540 db 0
_changed: times 540 db 0
