/* Fixture adapter: run the unchanged composed-session harness through the
 * loader and one far module entry. No Chat implementation is statically linked. */
#define chat_session_open chat_proxy_open
#define chat_session_key chat_proxy_key
#define chat_session_receive chat_proxy_receive
#define chat_session_step chat_proxy_step
#define chat_session_abort chat_proxy_abort
#include <dos.h>
#include "../src/chat/loader.h"
extern unsigned char __far chat_scratch[];
static chat_module_handle module;
static chat_module_request request;
static unsigned call(unsigned operation,chat_session __far *state)
{
    request.api=CHAT_MODULE_API;request.operation=operation;request.state=state;
    return chat_module_call(&module,&request);
}
unsigned CHAT_CALL chat_session_open(chat_session __far *s,chat_word __far *frame,
    unsigned capacity,unsigned rows,unsigned attribute,unsigned bar,unsigned clear,
    unsigned buffered,unsigned duplex,unsigned newline)
{
    if(!module.loaded && chat_module_load(&module,s,"PCCHAT.OVL",MK_FP(FP_SEG(chat_scratch)+1,0),63000))return 0;
    request.frame=frame;request.capacity=capacity;request.rows=rows;
    request.attribute=attribute;request.bar=bar;request.clear=clear;
    request.buffered=buffered;request.duplex=duplex;request.newline=newline;
    return call(CHAT_MODULE_OPEN,s);
}
unsigned CHAT_CALL chat_session_key(chat_session __far *s,unsigned key,unsigned transport_idle)
{
    unsigned result;
    if(!module.loaded)return s->fault?CHAT_FAILED:0;
    request.key=key;request.transport_idle=transport_idle;result=call(CHAT_MODULE_KEY,s);
    if(result&(CHAT_CLOSED|CHAT_FAILED))chat_module_unload(&module);
    return result;
}
unsigned CHAT_CALL chat_session_receive(chat_session __far *s,const unsigned char __far *table,unsigned value)
{
    if(!module.loaded)return 0;
    request.table=table;request.value=value;return call(CHAT_MODULE_RECEIVE,s);
}
unsigned CHAT_CALL chat_session_step(chat_session __far *s,unsigned budget,chat_sink sink,void __far *context)
{
    if(!module.loaded)return 0;
    request.budget=budget;request.sink=sink;request.user=context;return call(CHAT_MODULE_STEP,s);
}
void CHAT_CALL chat_session_abort(chat_session __far *s)
{
    if(module.loaded){call(CHAT_MODULE_ABORT,s);chat_module_unload(&module);}
}
