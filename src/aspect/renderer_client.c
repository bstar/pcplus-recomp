/* Source-owned client allocation validation; no DOS calls, UART or mutation.
 * Caller supplies current PSP from DOS62 and the bridge's saved caller DS=SS.
 * Only the main child allocation may contain the client and callback entry. */
#include <dos.h>
#include "resident_render.h"

unsigned __cdecl aspect_render_client_admit(unsigned psp,unsigned parent_psp,
 unsigned child_ds,unsigned offset,unsigned token,unsigned *callback)
{
 unsigned char __far *mcb;
 const aspect_render_client __far *client;
 unsigned long begin,end,address,entry;
 unsigned paragraphs;
 if(psp<256 || psp==parent_psp || child_ds<psp || !token ||
    !callback || (unsigned long)(unsigned)callback+4UL>65536UL ||
    (unsigned long)offset+ASPECT_RENDER_CLIENT_SIZE>65536UL)return 10;
 mcb=(unsigned char __far *)MK_FP(psp-1,0);
 if((mcb[0]!='M'&&mcb[0]!='Z') || *(unsigned __far *)(mcb+1)!=psp)return 10;
 paragraphs=*(unsigned __far *)(mcb+3);
 if(!paragraphs)return 10;
 begin=(unsigned long)psp*16UL+256UL;
 end=((unsigned long)psp+paragraphs)*16UL;
 address=(unsigned long)child_ds*16UL+offset;
 if(end>1048576UL || address<begin || address+ASPECT_RENDER_CLIENT_SIZE>end)return 10;
 client=(const aspect_render_client __far *)MK_FP(child_ds,offset);
 if(client->magic!=ASPECT_RENDER_CLIENT_MAGIC || client->version!=ASPECT_RENDER_CAP_VERSION ||
    client->token!=token)return 10;
 entry=(unsigned long)client->callback_segment*16UL+client->callback_offset;
 if(entry<begin || entry>=end || entry>=1048576UL ||
    (entry>=address && entry<address+ASPECT_RENDER_CLIENT_SIZE))return 10;
 callback[0]=client->callback_offset;callback[1]=client->callback_segment;
 return 0;
}
