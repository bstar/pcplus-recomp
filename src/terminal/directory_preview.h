#ifndef PCPLUS_DIRECTORY_PREVIEW_H
#define PCPLUS_DIRECTORY_PREVIEW_H
#include "../directory/directory_selection.h"
/* Internal foreground far-cdecl entry, DS=SS, IF1/DF0. No IO or live-state
 * mutation. The page/proposal/path contracts are directory_selection_stage's.
 * Accepted baseline and actual-session capture are caller-stack temporaries.
 * Return0 publishes a proposal. Otherwise proposal is unchanged: selection
 * status in bits0..3, source in4..7, detail in8..11; baseline failures are
 * 1000h|baseline-status and capture failures2000h|capture-status. ES is scratch.
 * Spellings retained here are not canonical identities or resource claims. */
unsigned __far __cdecl directory_preview_stage(const directory_dos_page_data __far *,
 unsigned entry,const char *path,directory_selection_proposal __far *);
#endif
