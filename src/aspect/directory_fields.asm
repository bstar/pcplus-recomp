; PCPlus2.01 overlay16 selected-directory integer getters.
; Exact native bodies; signed byte fields deliberately use CBW.
; See reconstruction/aspect_directory_fields/provenance.json.
BITS 16
CPU 8086
%ifdef ASPECT_DIRECTORY_FIELDS_FLAT
%define aspect_directory_record 0xe650
%else
SEGMENT _TEXT public class=CODE use16
extern aspect_directory_record
%endif

%macro FIELD 4
%ifdef ASPECT_DIRECTORY_FIELDS_FLAT
%if ASPECT_DIRECTORY_FIELDS_UNIT=%1
ORG %2
%else
%define OMIT_FIELD
%endif
%else
global aspect_directory_builtin_%3
%endif
%ifndef OMIT_FIELD
aspect_directory_builtin_%3:
%if %1=8
 mov ax,[aspect_directory_record+%4]
%else
 mov al,[aspect_directory_record+%4]
 cbw
%endif
 ret
%endif
%undef OMIT_FIELD
%endmacro

FIELD 1,0xd9ab,databit,49
FIELD 2,0xd9b0,duplex,51
FIELD 3,0xd9b9,mode,74
FIELD 4,0xd9be,parity,48
FIELD 5,0xd9c3,port,104
FIELD 6,0xd9d5,stopbit,50
FIELD 7,0xd9da,term,73
FIELD 8,0xd9df,total,70
