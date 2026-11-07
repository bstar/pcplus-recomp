BITS 16
CPU 8086
SEGMENT META_PICKER_CODE public align=16 class=FARCODE use16
GROUP META_PICKER_GROUP META_PICKER_CODE
SEGMENT META_RESOURCE_TEST public align=16 class=FARSTATE use16
GROUP META_RESOURCE_TEST_GROUP META_RESOURCE_TEST
global _scan,_picker,_entries,_records
_scan: times 160 db 0
_picker: times 20 db 0
_entries: times 9009 db 0
_records: times 1620 db 0
