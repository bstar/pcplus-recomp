/* Actual DOS fixture. Sink refusals are synthetic; no real UART is claimed. */
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "../src/terminal/chat_owner.h"
typedef struct {unsigned before;chat_owner state;unsigned after,identity;} guarded_owner;
static guarded_owner __far *guarded;
static FILE *output;
static unsigned attempts,case_number,errors,steps,accepted,deny,quiet;
#ifdef CHAT_BANK
static unsigned current_cs(void);
#pragma aux current_cs = "mov ax,cs" value [ax] modify exact [ax];
#endif
static void record(unsigned kind,unsigned value)
{fwrite(&kind,2,1,output);fwrite(&value,2,1,output);}
static unsigned __far __cdecl sink(unsigned kind,unsigned value,void __far *context)
{
    unsigned __far *identity=(unsigned __far *)context;
    if(*identity!=0x1234)++errors;
    ++attempts;
    /* Both first-call and repeated refusals, independent of output values. */
    if(deny || (case_number%2 && (attempts<=5 || attempts%3==0)))return 0;
    if(!quiet)record(kind,value);++accepted;return 1;
}
int main(void)
{
    FILE *input=fopen("VECTORS.BIN","rb");
    unsigned cases,i,b,d,n,count,key,result,old,budget,calls,segment,j,k;
    chat_owner copy;
    output=fopen("EVENTS.BIN","wb");
    if(!input || !output)return 2;
    if(sizeof(chat_owner)!=320)return 3;
#ifdef CHAT_BANK
    if(FP_SEG(chat_owner_open)==current_cs())return 9;
#endif
    if(_dos_allocmem((sizeof(guarded_owner)+15)/16,&segment))return 8;
    guarded=(guarded_owner __far *)MK_FP(segment,0);
    if(fread(&cases,2,1,input)!=1)return 4;
    for(case_number=0;case_number<cases;++case_number){
        if(fread(&b,2,1,input)!=1 || fread(&d,2,1,input)!=1 || fread(&n,2,1,input)!=1 || fread(&count,2,1,input)!=1)return 5;
        _fmemset(guarded,0xcc,sizeof(*guarded));guarded->before=0x1a2b;guarded->after=0x3c4d;guarded->identity=0x1234;
        chat_owner_open(&guarded->state,b,d,n);attempts=0;steps=0;
        record(0xfffe,case_number);
        for(i=0;i<count;++i){
            if(fread(&key,2,1,input)!=1)return 6;
            result=chat_owner_key(&guarded->state,key);
            if(!(result&CHAT_ACCEPTED))++errors;
            if(result&CHAT_PAINT)record(4,key);
            if(result&CHAT_HELP)record(5,key);
            if(result&CHAT_META)record(6,key);
            while(guarded->state.phase){
                copy=guarded->state;
                if(chat_owner_key(&guarded->state,0x2d00) || _fmemcmp(&copy,&guarded->state,sizeof(copy)))++errors;
                old=attempts;budget=steps%5?1:65535;
                calls=chat_owner_step(&guarded->state,0,sink,&guarded->identity);
                if(calls || attempts!=old || _fmemcmp(&copy,&guarded->state,sizeof(copy)))++errors;
                calls=chat_owner_step(&guarded->state,budget,sink,&guarded->identity);
                if(calls!=attempts-old || calls>(budget>32?32:budget))++errors;
                if(++steps>20000)return 7;
            }
        }
        if(guarded->state.active || guarded->state.count || guarded->before!=0x1a2b || guarded->after!=0x3c4d)++errors;
        record(0xffff,case_number);
    }
    /* Confirmed disconnect drops pending work before any subsequent sink call. */
    chat_owner_open(&guarded->state,0,1,1);chat_owner_key(&guarded->state,'X');
    copy=guarded->state;deny=1;
    for(i=0;i<64;++i){
        old=attempts;
        if(chat_owner_step(&guarded->state,32,sink,&guarded->identity)!=1 || attempts!=old+1 || _fmemcmp(&copy,&guarded->state,sizeof(copy)))++errors;
    }
    chat_owner_abort(&guarded->state);old=attempts;
    if(chat_owner_step(&guarded->state,32,sink,&guarded->identity) || attempts!=old || chat_owner_key(&guarded->state,'Y'))++errors;
    chat_owner_open(&guarded->state,1,1,1);chat_owner_key(&guarded->state,'X');chat_owner_abort(&guarded->state);
    if(guarded->state.count || guarded->state.phase || guarded->state.active)++errors;
    /* Retire at different TX/log/history/LF progress points. Already accepted
     * effects remain accepted; no further effect may escape after abort. */
    deny=0;quiet=1;case_number=0;
    for(j=0;j<3;++j)for(k=0;k<14;++k){
        chat_owner_open(&guarded->state,j==0,1,1);
        chat_owner_key(&guarded->state,j==2?17:'A');
        if(j==0)chat_owner_key(&guarded->state,13);
        for(i=0;i<k;++i)chat_owner_step(&guarded->state,1,sink,&guarded->identity);
        chat_owner_abort(&guarded->state);old=attempts;
        if(chat_owner_step(&guarded->state,32,sink,&guarded->identity) || attempts!=old || guarded->state.count || guarded->state.at || guarded->state.limit || guarded->state.phase || guarded->state.active)++errors;
    }
    if(_dos_freemem(segment))++errors;
    fclose(input);if(fclose(output))++errors;
    printf("CHAT OWNER %u CASES %u EVENTS %u ERRORS\n",cases,accepted,errors);
    return errors?1:0;
}
