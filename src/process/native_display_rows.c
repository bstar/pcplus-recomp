#include "native_display_rows.h"
extern unsigned display_rows_legacy,display_rows_extended_mode;
extern unsigned display_rows_font_capable,display_rows_scanline_capable;
extern unsigned display_rows_columns,display_rows_rows,display_rows_segment;
extern unsigned display_rows_mode,display_rows_stride,display_rows_cells;
extern void __cdecl display_rows_geometry(void),display_rows_detect(void);
extern void __cdecl display_rows_select(unsigned rows),display_rows_baseline(void);
extern unsigned __cdecl display_rows_supported(void);
static unsigned context(void)
{
 unsigned dsword=0,ssword=0,flags=0;
 __asm {
 mov ax,ds
 mov dsword,ax
 mov ax,ss
 mov ssword,ax
 pushf
 pop ax
 mov flags,ax
 }
 return dsword==ssword && (flags&0x600)==0x200;
}
static void copy(native_display_rows_info *p)
{
 p->mode=display_rows_mode&255;p->columns=display_rows_columns;p->rows=display_rows_rows;
 p->segment=display_rows_segment;p->stride=display_rows_stride;p->cells=display_rows_cells;
 p->font_capable=display_rows_font_capable;p->scanline_capable=display_rows_scanline_capable;
 p->extended_mode=display_rows_extended_mode;p->fallback=0;
}
unsigned __far __cdecl native_display_rows_probe(native_display_rows_info *p)
{
 if(!p || !context())return DISPLAY_ROWS_INVALID;
 if(display_rows_supported())return DISPLAY_ROWS_UNSUPPORTED;
 /* Native detection increments capability WORDs. Clear them on each fresh
  * probe rather than inheriting counts or guessing from a selected mode. */
 display_rows_legacy=display_rows_extended_mode=0;
 display_rows_font_capable=display_rows_scanline_capable=0;
 display_rows_geometry();display_rows_detect();copy(p);
 if((p->segment!=0xb800 && p->segment!=0xb000) || p->columns!=80 || p->stride!=160 ||
    (p->rows!=25 && p->rows!=28 && p->rows!=43 && p->rows!=50))return DISPLAY_ROWS_UNSUPPORTED;
 return DISPLAY_ROWS_OK;
}
unsigned __far __cdecl native_display_rows_set(unsigned rows,native_display_rows_info *p)
{
 unsigned rc;
 if(rows!=25 && rows!=28 && rows!=43 && rows!=50)return DISPLAY_ROWS_INVALID;
 rc=native_display_rows_probe(p);if(rc)return rc;
 if(rows!=25 && (!p->font_capable || (!p->scanline_capable && rows!=43)))return DISPLAY_ROWS_UNSUPPORTED;
 if(rows==25)display_rows_baseline();else display_rows_select(rows);
 rc=native_display_rows_probe(p);
 if(!rc && p->rows==rows)return DISPLAY_ROWS_OK;
 /* BIOS request completion is not proof of the requested geometry. */
 display_rows_baseline();rc=native_display_rows_probe(p);
 if(!rc && p->rows==25){p->fallback=1;return DISPLAY_ROWS_FAILED;}
 return DISPLAY_ROWS_UNUSABLE;
}
