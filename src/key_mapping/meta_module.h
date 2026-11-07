#ifndef PCPLUS_META_MODULE_H
#define PCPLUS_META_MODULE_H
#include "meta_editor.h"
#include "meta_key_resource.h"
/* Only call while the matched loader is ACTIVE. All explicit far cdecl;
 * near component interfaces in meta_editor.h are not parent entry points. */
unsigned __far __cdecl meta_editor_open_far(meta_editor __far *,unsigned,const unsigned char __far *,const char __far *,const char __far *,unsigned);
unsigned __far __cdecl meta_editor_key_far(meta_editor __far *,unsigned);
unsigned __far __cdecl meta_editor_step_far(meta_editor __far *,unsigned);
unsigned __far __cdecl meta_editor_draw_far(const meta_editor __far *,unsigned __far *,unsigned);
unsigned __far __cdecl meta_editor_cursor_far(const meta_editor __far *);
unsigned __far __cdecl meta_editor_shape_far(const meta_editor __far *);
unsigned __far __cdecl meta_editor_stop_far(meta_editor __far *);
unsigned __far __cdecl meta_editor_matches_far(const meta_editor __far *,const unsigned char __far *,const char __far *);
unsigned __far __cdecl meta_editor_proposal_far(const meta_editor __far *,unsigned char __far *,char __far *,char __far *);
unsigned __far __cdecl meta_module_resolve(unsigned,const char *,meta_key_resource_result *);
#endif
