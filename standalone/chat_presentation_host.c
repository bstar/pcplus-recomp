/* Real DOS/VGA lifecycle around the loaded source-built presentation variant.
 * Fixture allocations and the recovered row helper are not product storage. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
#include "../src/chat/presentation.h"
#include "../src/process/native_display_rows.h"
extern unsigned char __far chat_scratch[];
static chat_module_handle handle;
static chat_module_request request;
static unsigned errors,effects;
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned largest(void)
{unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
#define REQUIRE(c) do {if(!(c)){printf("FAIL line %u\n",__LINE__);++errors;}} while(0)
static unsigned invoke(unsigned op)
{request.operation=op;return chat_module_call(&handle,&request);}
static void cursor_set(unsigned position,unsigned shape)
{
    union REGS in,out;memset(&in,0,sizeof(in));in.h.ah=1;in.x.cx=shape;int86(0x10,&in,&out);
    in.h.ah=2;in.h.bh=0;in.x.dx=position;int86(0x10,&in,&out);
}
static void cursor_get(unsigned *position,unsigned *shape)
{
    union REGS in,out;memset(&in,0,sizeof(in));in.h.ah=3;int86(0x10,&in,&out);*position=out.x.dx;*shape=out.x.cx;
}
static void page(unsigned n)
{union REGS in,out;memset(&in,0,sizeof(in));in.h.ah=5;in.h.al=(unsigned char)n;int86(0x10,&in,&out);}
static unsigned word_at(unsigned i,unsigned seed)
{return ((i*17+seed)&255)|(((i*11+seed)&127)<<8);}
static unsigned screen_matches(unsigned cells,unsigned seed)
{unsigned i;const unsigned __far *v=MK_FP(0xb800,0);for(i=0;i<cells;++i)if(v[i]!=word_at(i,seed))return 0;return 1;}
static unsigned __far __cdecl sink(unsigned kind,unsigned value,void __far *context)
{
    if(*(unsigned __far *)context!=0x6172 || value!=240 ||
       kind!=(effects?CHAT_LOG:CHAT_HISTORY))++errors;
    ++effects;return 1;
}
static unsigned canary(const unsigned char __far *p,unsigned n)
{unsigned i;for(i=0;i<n;++i)if(p[i]!=0xa5)return 0;return 1;}
int main(void)
{
    const unsigned rows[4]={25,28,43,50};native_display_rows_info info;
    unsigned state_seg,backup_seg,context_seg,table_seg,pressure,free_before,saved_psp;
    unsigned i,j,k,segment,cells,position,shape,want_position,want_shape,seed,identity=0x6172;
    unsigned char jft[20],__far *table;
    chat_session __far *state;chat_presentation __far *presentation;
    chat_word __far *video=MK_FP(0xb800,0),__far *backup;
    if(sizeof(chat_session)!=362 || sizeof(chat_presentation)!=16)return 2;
    if(_dos_allocmem(24,&state_seg) || _dos_allocmem(501,&backup_seg) ||
       _dos_allocmem(2,&context_seg) || _dos_allocmem(16,&table_seg))return 3;
    state=MK_FP(state_seg,8);backup=MK_FP(backup_seg,8);presentation=MK_FP(context_seg,8);table=MK_FP(table_seg,0);
    for(i=0;i<256;++i)table[i]=(unsigned char)i;
    saved_psp=psp();for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(saved_psp,0x18+i));
    free_before=largest();if(_dos_allocmem(free_before,&pressure))return 4;
    for(i=0;i<4;++i)for(j=0;j<2;++j){
        REQUIRE(native_display_rows_set(rows[i],&info)==0 && info.rows==rows[i]);
        cells=rows[i]*80;seed=7+i+j;
        for(k=0;k<cells;++k)video[k]=word_at(k,seed);
        want_position=((rows[i]-3)<<8)|17;want_shape=j?0x2607:0x0607;
        cursor_set(want_position,want_shape);cursor_get(&want_position,&want_shape);
        _fmemset(chat_scratch,0xa5,63032);_fmemset(MK_FP(state_seg,0),0xa5,384);
        _fmemset(MK_FP(backup_seg,0),0xa5,8016);_fmemset(MK_FP(context_seg,0),0xa5,32);
        memset(&handle,0,sizeof(handle));memset(&request,0,sizeof(request));
        segment=FP_SEG(chat_scratch)+1+j*256;
        REQUIRE(chat_module_load(&handle,state,"PCCHAT.OVL",MK_FP(segment,0),8192)==0);
        request.api=CHAT_MODULE_API;request.state=state;request.frame=backup;request.capacity=4000;
        request.rows=rows[i];request.attribute=0x17;request.bar=0x71;request.clear=0x17;
        request.buffered=1;request.transport_idle=1;request.user=presentation;request.value=sizeof(*presentation);
        if(i==0 && j==0){
            request.api=0x100;REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==CHAT_MODULE_BAD);request.api=CHAT_MODULE_API;
            request.capacity=cells-1;REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==0);request.capacity=4000;
            request.attribute=256;REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==0);request.attribute=0x17;
            request.rows=0;REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==0);request.rows=rows[i];
            request.user=state;REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==0);request.user=presentation;
            request.frame=(chat_word __far *)state;REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==0);request.frame=backup;
            request.frame=MK_FP(segment,0);REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==0);request.frame=backup;
            request.user=0;REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==0);request.user=presentation;
            request.value=sizeof(*presentation)-1;REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==CHAT_MODULE_BAD);request.value=sizeof(*presentation);
            REQUIRE(screen_matches(cells,seed) && canary(MK_FP(backup_seg,0),8016));
        }
        REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==1 && handle.active && state->presentation==presentation);
        REQUIRE(chat_module_unload(&handle)==CHAT_LOAD_ACTIVE);
        REQUIRE(invoke(CHAT_MODULE_OPEN)==CHAT_MODULE_BAD);
        cursor_get(&position,&shape);REQUIRE(position==((rows[i]>28?34:20)<<8) && shape==want_shape);
        REQUIRE(video[36]==0x7152 && video[(rows[i]>28?33:19)*80+37]==0x714c);
        request.key='A';REQUIRE(invoke(CHAT_MODULE_KEY)==(CHAT_ACCEPTED|CHAT_PAINT));
        cursor_get(&position,&shape);REQUIRE(position==(((rows[i]>28?34:20)<<8)|1) && shape==want_shape);
        REQUIRE(video[(rows[i]>28?34:20)*80]==0x1741);
        request.table=table;request.value=240;REQUIRE(invoke(CHAT_MODULE_RECEIVE)==1);
        effects=0;request.sink=sink;request.user=&identity;request.budget=32;
        REQUIRE(invoke(CHAT_MODULE_STEP)==2 && effects==2);
        REQUIRE(video[(rows[i]>28?32:18)*80]==0x17f0);
        REQUIRE(chat_module_image_valid(segment));
        if(j){
            page(1);request.key='B';REQUIRE(invoke(CHAT_MODULE_KEY)==CHAT_MODULE_BAD);
            request.value='C';REQUIRE(invoke(CHAT_MODULE_RECEIVE)==CHAT_MODULE_BAD);
            REQUIRE(state->screen.pane[1].column==1 && !state->rx_phase);
            request.key=27;REQUIRE(invoke(CHAT_MODULE_KEY)==CHAT_MODULE_BAD);
            REQUIRE(invoke(CHAT_MODULE_ABORT)==CHAT_MODULE_BAD);
            REQUIRE(handle.active && state->presentation && chat_module_unload(&handle)==CHAT_LOAD_ACTIVE);
            REQUIRE(video[(rows[i]>28?34:20)*80]==0x1741);
            page(0);REQUIRE(invoke(CHAT_MODULE_ABORT)==0);
        }else{request.key=27;REQUIRE(invoke(CHAT_MODULE_KEY)==(CHAT_ACCEPTED|CHAT_CLOSED));}
        REQUIRE(!handle.active && !state->presentation && screen_matches(cells,seed));
        cursor_get(&position,&shape);REQUIRE(position==want_position && shape==want_shape);
        REQUIRE(chat_module_unload(&handle)==0 && largest()==0 && psp()==saved_psp);
        REQUIRE(canary(MK_FP(state_seg,0),8) && canary(MK_FP(state_seg,8+sizeof(*state)),384-8-sizeof(*state)));
        REQUIRE(canary(MK_FP(backup_seg,0),8) && canary(MK_FP(backup_seg,8008),8));
        REQUIRE(canary(MK_FP(context_seg,0),8) && canary(MK_FP(context_seg,24),8));
        for(k=0;k<20;++k)REQUIRE(jft[k]==*((unsigned char __far *)MK_FP(saved_psp,0x18+k)));
    }
    REQUIRE(_dos_freemem(pressure)==0 && largest()==free_before);
    REQUIRE(_dos_freemem(table_seg)==0 && _dos_freemem(context_seg)==0 &&
            _dos_freemem(backup_seg)==0 && _dos_freemem(state_seg)==0);
    REQUIRE(native_display_rows_set(25,&info)==0);
    printf("errors=%u presentations=8 rows=25,28,43,50 quarantine=4 negatives=9\n",errors);
    return errors?1:0;
}
