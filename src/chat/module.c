/* Overlay entry keeps the parent's DS=SS and uses only caller-owned far state. */
#include "module.h"
typedef char request_size_must_be_50[(sizeof(chat_module_request)==50)?1:-1];
typedef char session_size_must_be_358[(sizeof(chat_session)==358)?1:-1];
unsigned CHAT_FAR __cdecl chat_module_dispatch(chat_module_request CHAT_FAR *r)
{
    unsigned result;
    if(!r || r->api!=CHAT_MODULE_API)return CHAT_MODULE_BAD;
    if(r->operation==CHAT_MODULE_QUERY)result=sizeof(chat_session);
    else if(!r->state)return CHAT_MODULE_BAD;
    else switch(r->operation){
    case CHAT_MODULE_OPEN:
        result=chat_session_open(r->state,r->frame,r->capacity,r->rows,r->attribute,r->bar,r->clear,r->buffered,r->duplex,r->newline);break;
    case CHAT_MODULE_KEY:result=chat_session_key(r->state,r->key,r->transport_idle);break;
    case CHAT_MODULE_RECEIVE:result=chat_session_receive(r->state,r->table,r->value);break;
    case CHAT_MODULE_STEP:result=chat_session_step(r->state,r->budget,r->sink,r->user);break;
    case CHAT_MODULE_ABORT:chat_session_abort(r->state);result=0;break;
    default:return CHAT_MODULE_BAD;
    }
    r->result=result;return result;
}
