; Exact overlay16 WORD getters: COL,ROW,SCRNCOLS,SCRNROWS and five attributes.
BITS 16
CPU 8086
%ifdef ASPECT_TERMINAL_FLAT
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_columns 0x7a72
%define screen_rows 0x7a74
%define attributes_bold_value 0x1d34
%define attributes_preset_value 0x1d36
%define attributes_normal_value 0x1d32
%define attributes_reverse_value 0x1d38
%define attributes_underline_value 0x1d3a
%elifdef ASPECT_TERMINAL_PARENT
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern screen_cursor_column,screen_cursor_row,screen_columns,ui_window_rows
%define screen_rows ui_window_rows
extern attributes_bold_value,attributes_preset_value,attributes_normal_value
extern attributes_reverse_value,attributes_underline_value
%else
SEGMENT _TEXT public class=CODE use16
extern _runtime_terminal_values
%define screen_cursor_column (_runtime_terminal_values+0)
%define screen_cursor_row (_runtime_terminal_values+2)
%define screen_columns (_runtime_terminal_values+4)
%define screen_rows (_runtime_terminal_values+6)
%define attributes_bold_value (_runtime_terminal_values+8)
%define attributes_preset_value (_runtime_terminal_values+10)
%define attributes_normal_value (_runtime_terminal_values+12)
%define attributes_reverse_value (_runtime_terminal_values+14)
%define attributes_underline_value (_runtime_terminal_values+16)
%endif
%macro GETTER 4
%ifdef ASPECT_TERMINAL_FLAT
%if ASPECT_TERMINAL_UNIT=%1
ORG %2
%else
%define OMIT_GETTER
%endif
%else
global aspect_terminal_%3
%endif
%ifndef OMIT_GETTER
aspect_terminal_%3:
 mov ax,[%4]
 ret
%endif
%undef OMIT_GETTER
%endmacro
GETTER 0,0xd9a7,col,screen_cursor_column
GETTER 1,0xd9e8,row,screen_cursor_row
GETTER 2,0xd9ec,cols,screen_columns
GETTER 3,0xd9f0,rows,screen_rows
GETTER 4,0xd9f4,bold,attributes_bold_value
GETTER 5,0xd9f8,dim,attributes_preset_value
GETTER 6,0xd9fc,norm,attributes_normal_value
GETTER 7,0xda00,rev,attributes_reverse_value
GETTER 8,0xda04,uline,attributes_underline_value
