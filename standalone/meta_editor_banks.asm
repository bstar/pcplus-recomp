BITS 16
CPU 8086
SEGMENT META_EDITOR_TEST public align=16 class=FARSTATE use16
GROUP META_EDITOR_TEST_GROUP META_EDITOR_TEST
global _editor,_live,_proposal
_editor: times 16384 db 0
_live: times 540 db 0
_proposal: times 540 db 0
