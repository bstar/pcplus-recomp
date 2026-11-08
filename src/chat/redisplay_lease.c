/* Module-owned suspension. Frozen history goes into a temporary DOS arena;
 * loaded Chat code stays in place. No CRT, static data, own stack or private
 * heap. The fixed parent descriptor supplies DOS and viewer service bridges. */
#include <dos.h>
#include "redisplay_lease.h"
#include "presentation.h"
extern unsigned CHAT_FAR __cdecl chat_view_allocate(unsigned);
extern unsigned CHAT_FAR __cdecl chat_view_free(unsigned);
typedef struct lease {
    unsigned segment,snapshot_segment,cells;
    unsigned held;
    chat_presentation CHAT_FAR *presentation;
} lease;
typedef char chat_view_lease_must_be_12[(sizeof(lease)==12)?1:-1];
/*63000 history bytes rounded to a paragraph, then a normalized underlay. */
#define HISTORY_PARAGRAPHS 3938
static chat_word CHAT_FAR *saved(lease CHAT_FAR *l)
{return (chat_word CHAT_FAR *)MK_FP(l->segment+HISTORY_PARAGRAPHS,0);}
static void copy(chat_word CHAT_FAR *to,const chat_word CHAT_FAR *from,unsigned cells)
{unsigned i;for(i=0;i<cells;++i)to[i]=from[i];}
/* The viewer temporarily detaches Chat's presentation. Its geometry contract
 * still applies to every key/RX/idle/close continuation. Once restored, put
 * the saved live Chat frame back before the viewer resumes drawing. */
static unsigned ready(chat_session CHAT_FAR *s,const chat_view_binding CHAT_FAR *b,lease CHAT_FAR *l)
{
    if(!chat_present_suspended(s,l->presentation)){l->held=1;return 0;}
    if(l->held){b->before();l->held=0;}
    return 1;
}
static unsigned resume(chat_session CHAT_FAR *s,const chat_view_binding CHAT_FAR *b,lease CHAT_FAR *l)
{
    if(!*b->active)return 1;
    if(*b->active==1){
        if(*b->owner!=0 && *b->owner!=2)return 0;
        copy(b->underlay,saved(l),l->cells);
        *b->snapshot_segment=l->snapshot_segment;
        s->presentation=l->presentation;l->presentation->drawn=65535U;
        *b->owner=2;*b->active=2;
    }
    /* Failed free retains a retry phase; never forget the owned allocation. */
    if(chat_view_free(l->segment))return 0;
    l->segment=0;*b->active=0;return 1;
}
static unsigned begin(chat_session CHAT_FAR *s,const chat_view_binding CHAT_FAR *b,lease CHAT_FAR *l)
{
    unsigned segment,paragraphs;
    chat_presentation CHAT_FAR *p=(chat_presentation CHAT_FAR *)s->presentation;
    if(*b->active || *b->owner!=2 || !p || p->backup!=b->underlay ||
       s->send.phase || s->rx_phase || s->text.active ||
       p->cells!=s->screen.cells || p->cells<2000 || p->cells>4000)return 0;
    paragraphs=HISTORY_PARAGRAPHS+(p->cells+7)/8;
    segment=chat_view_allocate(paragraphs);if(!segment)return 0;
    l->segment=segment;l->snapshot_segment=*b->snapshot_segment;
    l->cells=p->cells;l->presentation=p;l->held=0;
    if(segment<0x50 || (unsigned long)segment+paragraphs>0xa000UL){
        *b->active=2;resume(s,b,l);return 0;
    }
    copy(saved(l),b->underlay,l->cells);
    *b->snapshot_segment=segment;s->presentation=0;*b->active=1;
    *b->owner=0;b->enter();
    if(*b->owner==1)return 1;
    *b->owner=2;
    resume(s,b,l);return 0;
}
unsigned CHAT_CALL chat_view_dispatch(chat_module_request CHAT_FAR *r)
{
    const chat_view_binding CHAT_FAR *b=(const chat_view_binding CHAT_FAR *)r->state->live.view;
    lease CHAT_FAR *l;
    if(!b || !b->active || !b->owner || !b->snapshot_segment || !b->scratch ||
       !b->underlay || !b->enter || !b->leave || !b->before)return 0;
    l=(lease CHAT_FAR *)b->scratch;
    if(r->value==CHAT_VIEW_BEGIN)return begin(r->state,b,l);
    if(r->value==CHAT_VIEW_READY)return *b->active!=1 || ready(r->state,b,l);
    if(r->value==CHAT_VIEW_CLOSE && *b->active==1 && *b->owner==1){
        if(!ready(r->state,b,l))return 0;
        b->leave();
    }
    if(r->value==CHAT_VIEW_RESUME || r->value==CHAT_VIEW_CLOSE)return resume(r->state,b,l);
    return 0;
}

/* Existing frontend admission/scheduling, banked without changing its policy.
 * Peek/hold must never invoke presentation validation or block cancellation. */
unsigned CHAT_CALL chat_view_service(chat_module_request CHAT_FAR *r)
{
    chat_session CHAT_FAR *s=r->state;
    const chat_view_binding CHAT_FAR *b=(const chat_view_binding CHAT_FAR *)s->live.view;
    unsigned value=r->key,result;
    if(!b || !b->tx_count || !b->connection)return CHAT_MODULE_BAD;
    if(r->operation==CHAT_MODULE_KEY_HOLD)return value!=0x2d00 && value!=0x2300 &&
        (s->send.phase || s->rx_phase ||
         ((s->text.active || *b->tx_count) && !(s->text.active && (value&255)==27)));
    if(*b->active==1 && !ready(s,b,(lease CHAT_FAR *)b->scratch))return CHAT_MODULE_BAD;
    if(r->operation==CHAT_MODULE_RX_HOLD)return !s->send.active || !s->screen.active || s->rx_phase!=0;
    if(*b->connection!=0 && *b->connection!=6)return CHAT_MODULE_BAD;
    result=chat_live_step(r);return s->fault?CHAT_MODULE_BAD:result;
}

/* Construction also belongs to the loaded bank: retain the original parent
 * memory budget while keeping every buffer/stack/stream capacity unchanged. */
unsigned CHAT_CALL chat_view_front_open(chat_module_request CHAT_FAR *r)
{
    const chat_live_binding CHAT_FAR *live=(const chat_live_binding CHAT_FAR *)r->table;
    const chat_view_binding CHAT_FAR *b;
    unsigned i,attribute;
    if(!live || !live->view)return 0;
    b=(const chat_view_binding CHAT_FAR *)live->view;
    if(!b->rows || !b->attribute || !b->duplex || !b->newline || !b->translate ||
       !b->input_table || !b->presentation || !b->rx_table || !b->sink)return 0;
#ifdef CHAT_SEND_MODE
    if(r->buffered>255)return 0;
#endif
    attribute=*b->attribute&255;
    if(!chat_present_open(r->state,(chat_presentation CHAT_FAR *)b->presentation,
        b->underlay,4000,*b->rows,attribute,attribute|0x19,attribute,
#ifdef CHAT_SEND_MODE
        r->buffered,
#else
        1,
#endif
        *b->duplex,*b->newline))return 0;
    if(!chat_live_bind(r->state,live)){chat_session_abort(r->state);return 0;}
    r->sink=b->sink;r->user=0;r->budget=32;r->table=b->rx_table;
    for(i=0;i<256;++i)b->rx_table[i]=*b->translate?b->input_table[i]:(unsigned char)i;
    return 1;
}
