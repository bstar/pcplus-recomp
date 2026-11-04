/* Maintained destructive selector owner around recovered BIOS services.
 * Requested selector and independently verified geometry are distinct. */
#include "native_display_rows.h"
extern void __cdecl display_rows_set_video_mode(unsigned mode);
extern void __cdecl display_rows_baseline(void);
extern void __cdecl display_rows_select(unsigned rows);
extern unsigned display_rows_mono;
typedef char selection_size[sizeof(native_display_selection)==24?1:-1];
static void publish(native_display_selection *out,const native_display_selection *stage)
{
 unsigned i;unsigned *d=(unsigned *)out;const unsigned *s=(const unsigned *)stage;
 for(i=0;i<12;++i)d[i]=s[i];
}
static unsigned baseline(native_display_rows_info *p)
{
 unsigned mode=display_rows_mono?7:3,status;
 display_rows_baseline();status=native_display_rows_probe(p);
 return status || p->mode!=mode || p->rows!=25;
}
static unsigned fallback(native_display_selection *p,unsigned result)
{
 unsigned status=baseline(&p->geometry);
 p->geometry.fallback=1;p->accepted_selector=0xffff;
 if(status)return DISPLAY_ROWS_UNUSABLE;
 p->accepted_selector=1;return result;
}
unsigned __far __cdecl native_display_select(unsigned selector,unsigned rows,
 unsigned mode,native_display_selection *out)
{
 native_display_selection stage;unsigned status,desired,accepted=selector;
 if(selector>4 || !out || (unsigned long)(unsigned)out+sizeof(*out)>65536UL)return DISPLAY_ROWS_INVALID;
 stage.requested_selector=selector;stage.accepted_selector=0xffff;
 status=native_display_rows_probe(&stage.geometry);if(status)return status;
 if(selector==1 || selector==2){
  if(baseline(&stage.geometry))goto failed;
 }else if(selector==3 || selector==4){
  if((signed short)mode<=0 || !stage.geometry.font_capable){
   status=fallback(&stage,DISPLAY_ROWS_OK);publish(out,&stage);return status;
  }
  display_rows_set_video_mode(mode);status=native_display_rows_probe(&stage.geometry);
  if(status || stage.geometry.mode!=(mode&127))goto failed;
 }
 desired=stage.geometry.rows;
 if(selector==2 || selector==4){
  /* Preserve native low-byte/font-capability decisions, while verifying their
   * result independently. A selector itself is never hardware success. */
  if(stage.geometry.font_capable){
   if(stage.geometry.scanline_capable){
    desired=rows&255;if(desired!=28 && desired!=43 && desired!=50)desired=25;
   }else desired=(rows&255)==43?43:25;
  }
  if(rows!=stage.geometry.rows)display_rows_select(rows);
  status=native_display_rows_probe(&stage.geometry);
  if(status || stage.geometry.rows!=desired)goto failed;
 }
 stage.accepted_selector=accepted;publish(out,&stage);return DISPLAY_ROWS_OK;
failed:
 status=fallback(&stage,DISPLAY_ROWS_FAILED);publish(out,&stage);return status;
}
