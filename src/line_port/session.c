#include "session.h"
extern unsigned __far __cdecl line_port_select(line_port_values *,unsigned);
static unsigned valid(const line_port_values *v)
{return v && v->port<4 && v->baud<9 && v->parity<5 &&
 (v->stop==1 || v->stop==2) && (v->bits==7 || v->bits==8);}
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
unsigned __far __cdecl line_port_session_begin(line_port_session *s,const line_port_values *v)
{
 line_port_session next;
 if(!extent(s,sizeof(*s)) || !extent(v,sizeof(*v)) || !valid(v))return LINE_PORT_ARGUMENT;
 if(s->notice==LINE_PORT_LOCKED)return LINE_PORT_LOCKED;
 if(s->phase && s->phase!=LINE_PORT_DONE)return LINE_PORT_ARGUMENT;
 next.selected=next.initial=*v;next.phase=LINE_PORT_EDIT;
 next.save=next.notice=next.quiesce_requests=0;
 *s=next;return 0;
}
unsigned __far __cdecl line_port_session_key(line_port_session *s,unsigned key,unsigned *events)
{
 line_port_values next;unsigned result;
 if(!extent(s,sizeof(*s)) || !extent(events,sizeof(*events)) ||
    !separate(s,sizeof(*s),events,sizeof(*events)) || !valid(&s->selected))return LINE_PORT_ARGUMENT;
 *events=0;
 if(s->notice==LINE_PORT_LOCKED)return LINE_PORT_LOCKED;
 if(s->phase!=LINE_PORT_EDIT)return LINE_PORT_ARGUMENT;
 /* Native wrapper intercepts these keys before its selector. */
 if(key==27 || key==0x1f00){s->save=key==0x1f00;s->phase=LINE_PORT_REQUEST;s->notice=0;return 0;}
 if(key>=0x3f00 && key<=0x4200 && !(key&255)){
  s->notice=LINE_PORT_UNSUPPORTED;*events=1;return LINE_PORT_UNSUPPORTED;
 }
 next=s->selected;result=line_port_select(&next,key);
 if(!valid(&next))return LINE_PORT_ARGUMENT;
 s->selected=next;s->notice=0;
 if((result&2) && s->quiesce_requests!=65535U)++s->quiesce_requests;
 *events=result;return 0;
}
unsigned __far __cdecl line_port_session_saved(line_port_session *s,unsigned error,unsigned uncertain)
{
 if(!extent(s,sizeof(*s)) || s->phase!=LINE_PORT_REQUEST || !s->save)return LINE_PORT_ARGUMENT;
 if(error || uncertain){s->notice=uncertain?LINE_PORT_LOCKED:LINE_PORT_SAVE_FAILED;s->phase=LINE_PORT_EDIT;return s->notice;}
 s->phase=LINE_PORT_SAVED;s->notice=0;return 0;
}
unsigned __far __cdecl line_port_session_applied(line_port_session *s,unsigned error)
{
 if(!extent(s,sizeof(*s)) || (s->phase!=LINE_PORT_REQUEST && s->phase!=LINE_PORT_SAVED) ||
    (s->phase==LINE_PORT_REQUEST && s->save))return LINE_PORT_ARGUMENT;
 if(error){s->notice=LINE_PORT_APPLY_FAILED;return s->notice;}
 s->phase=LINE_PORT_DONE;s->notice=0;return 0;
}
unsigned __far __cdecl line_port_session_request(const line_port_session *s,line_port_values *v,unsigned *save)
{
 if(!extent(s,sizeof(*s)) || !extent(v,sizeof(*v)) || !extent(save,sizeof(*save)) ||
    !separate(s,sizeof(*s),v,sizeof(*v)) || !separate(s,sizeof(*s),save,sizeof(*save)) ||
    !separate(v,sizeof(*v),save,sizeof(*save)) || !valid(&s->selected) ||
    (s->phase!=LINE_PORT_REQUEST && s->phase!=LINE_PORT_SAVED))return LINE_PORT_ARGUMENT;
 *v=s->selected;*save=s->phase==LINE_PORT_REQUEST && s->save;return 0;
}
