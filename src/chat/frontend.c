/* Experimental foreground core. The loaded module owns all panes/session
 * storage; only its18-byte handle and sibling filename stay near. */
#include <dos.h>
#include "loader.h"
#include "parent_sink.h"
#include "../config/resource_path.h"
extern unsigned char CHAT_FAR redisplay_snapshot[],redisplay_view[];
#pragma aux redisplay_snapshot "redisplay_snapshot";
#pragma aux redisplay_view "redisplay_view";
extern unsigned process_psp,ui_window_rows,attributes_normal_value,modes_value_1d1a;
extern unsigned terminal_cr_adds_lf,terminal_tx_count,terminal_deferred_count,connection_state;
extern unsigned terminal_translation_enabled;
extern unsigned char terminal_translation_table[];
#pragma aux process_psp "process_psp";
#pragma aux ui_window_rows "ui_window_rows";
#pragma aux attributes_normal_value "attributes_normal_value";
#pragma aux modes_value_1d1a "modes_value_1d1a";
#pragma aux terminal_cr_adds_lf "terminal_cr_adds_lf";
#pragma aux terminal_tx_count "terminal_tx_count";
#pragma aux terminal_deferred_count "terminal_deferred_count";
#pragma aux connection_state "connection_state";
#pragma aux terminal_translation_enabled "terminal_translation_enabled";
#pragma aux terminal_translation_table "terminal_translation_table";
extern unsigned CHAT_FAR __cdecl chat_front_claim(void);
extern void CHAT_FAR __cdecl chat_front_release(void);
static chat_module_handle handle;
static unsigned initialized=0xc701;
static const char leaf[]="PCCHAT.OVL";
#define STATE ((chat_session CHAT_FAR *)(redisplay_snapshot+12288))
#define REQUEST ((chat_module_request CHAT_FAR *)(redisplay_snapshot+13200))
static unsigned operation(unsigned op)
{REQUEST->operation=op;return chat_module_call(&handle,REQUEST);}
static unsigned stop(void)
{
    if(!handle.loaded)return 0;
    if(handle.busy)return 1;
    operation(CHAT_MODULE_ABORT);
    if(handle.active || chat_module_unload(&handle))return 1;
    chat_front_release();return 0;
}
static unsigned enter(void)
{
    char path[64];unsigned i;
    unsigned char CHAT_FAR *bytes=(unsigned char CHAT_FAR *)REQUEST;
    if(handle.loaded || terminal_deferred_count ||
       resource_program_path(process_psp,leaf,path) || !chat_front_claim())return 0;
    if(chat_module_load(&handle,STATE,path,redisplay_snapshot,8192)){
        chat_front_release();return 0;
    }
    for(i=0;i<sizeof(*REQUEST);++i)bytes[i]=0;
    REQUEST->api=CHAT_MODULE_API;REQUEST->state=STATE;
    REQUEST->frame=(chat_word CHAT_FAR *)redisplay_view;REQUEST->capacity=4000;
    REQUEST->rows=ui_window_rows;REQUEST->attribute=attributes_normal_value&255;
    REQUEST->bar=REQUEST->attribute|0x19;REQUEST->clear=REQUEST->attribute;
    REQUEST->buffered=1;REQUEST->duplex=modes_value_1d1a;REQUEST->newline=terminal_cr_adds_lf;
    REQUEST->user=redisplay_snapshot+13000;REQUEST->value=16;
    if(operation(CHAT_MODULE_PRESENT_OPEN)!=1){stop();return 0;}
    REQUEST->sink=terminal_chat_sink;REQUEST->user=0;REQUEST->budget=32;
    REQUEST->table=redisplay_snapshot+14000;
    for(i=0;i<256;++i)redisplay_snapshot[14000+i]=terminal_translation_enabled?terminal_translation_table[i]:(unsigned char)i;
    return 1;
}
/* Events:0 key,1 pre-read key hold,2 pre-dequeue RX hold,3 actual raw RX,
 * 4 idle service,5 forced stop. DS=SS, one foreground caller; no recursion. */
unsigned CHAT_FAR __cdecl chat_front_event(unsigned event,unsigned value)
{
    unsigned result,i;
    if(initialized==0xc701){
        unsigned char *p=(unsigned char *)&handle;
        for(i=0;i<sizeof(handle);++i)p[i]=0;
        initialized=0xc702;
    }
    if(initialized!=0xc702)return 0;
    if(!handle.loaded){if(event==0 && value==0x1800){enter();return 1;}return 0;}
#ifdef CHAT_ECHO
    /* A native echo parser can poll IO while the module call retains its
     * stack. Preserve ordinary typeahead; only cancellation keys may escape
     * to the existing parent dispatcher. Never call/unload the busy module. */
    if(handle.busy){
        if(event==0)return 0;
        if(event==1)return value!=0x2d00 && value!=0x2300 && (value&255)!=27;
        return 1;
    }
#endif
    if(event==5)return stop();
    if(event==1)return (value!=0x2d00 && value!=0x2300) &&
        (STATE->send.phase || STATE->rx_phase ||
         ((value&255)==27 && terminal_tx_count));
    if(event==2)return STATE->rx_phase!=0 || operation(CHAT_MODULE_PRESENT_CURSOR)!=1;
    if(event==0){
        if(value==0x2d00 || value==0x2300){return stop()?1:0;}
        /* Help/direct TEXT require their own continuation. Experimental core
         * refuses these keys rather than running a different KEY action. */
        if(value==0x6d00 || (value>=0x7800 && value<=0x8100 && !(value&255))){
            handle.dos_error=0x7f01;return 1;
        }
        REQUEST->key=value;REQUEST->transport_idle=terminal_tx_count==0;
        result=operation(CHAT_MODULE_KEY);
        if(result==CHAT_MODULE_BAD || (result&CHAT_FAILED) || !STATE->send.active)stop();
        return 1;
    }
    if(event==3){REQUEST->value=value;return operation(CHAT_MODULE_RECEIVE);}
    if(event==4){
        if(connection_state!=0 && connection_state!=6){stop();return 0;}
        result=operation(CHAT_MODULE_STEP);
        if(result==CHAT_MODULE_BAD || STATE->fault)stop();
    }
    return 0;
}
