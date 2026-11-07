; Diagnostic bank frames match the future code-resident constant contract.
BITS 16
CPU 8086
SEGMENT META_TEXT_CODE public align=16 class=FARCODE use16
GROUP META_TEXT_GROUP META_TEXT_CODE
SEGMENT META_DIALOG_CODE public align=16 class=FARCODE use16
GROUP META_DIALOG_GROUP META_DIALOG_CODE
SEGMENT META_TEST_STATE public align=16 class=FARSTATE use16
GROUP META_TEST_STATE_GROUP META_TEST_STATE
global _external_state
_external_state: times 684 db 0
