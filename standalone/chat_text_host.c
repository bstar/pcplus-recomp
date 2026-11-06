/* Real8086 far-state owner; callback effects/delay completion are recorded
 * boundaries. No native sender, UART or terminal renderer linked here. */
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "../src/chat/text.h"
static FILE *output;
static unsigned errors,attempts,accepted,case_number;
static unsigned ds(void);
#pragma aux ds = "mov ax,ds" value [ax] modify exact [ax];
static unsigned ss(void);
#pragma aux ss = "mov ax,ss" value [ax] modify exact [ax];
static unsigned cs(void);
#pragma aux cs = "mov ax,cs" value [ax] modify exact [ax];
#define REQUIRE(c) do{if(!(c)){printf("FAIL line%u case%u\n",__LINE__,case_number);++errors;}}while(0)
static unsigned CHAT_FAR __cdecl sink(unsigned kind,unsigned value,void CHAT_FAR *user)
{
    unsigned pair[2];++attempts;
    if(*(unsigned CHAT_FAR *)user!=0x6142 || ds()!=ss())++errors;
    if(attempts%5==0)return 0;
    pair[0]=kind;pair[1]=value;if(fwrite(pair,sizeof(pair),1,output)!=1)++errors;
    ++accepted;return 1;
}
static unsigned canary(const unsigned char CHAT_FAR *p,unsigned n)
{unsigned i;for(i=0;i<n;++i)if(p[i]!=0xa5)return 0;return 1;}
int main(void)
{
    FILE *input;unsigned state_segment,field_segment,cases,kind,settings[4],identity=0x6142;
    unsigned i,before,calls,turns,marker[2],budget;unsigned char field[54];chat_text copy;
    chat_text CHAT_FAR *state;unsigned char CHAT_FAR *source;
    if(sizeof(chat_text)!=68 || FP_SEG(chat_text_open)==cs())return 2;
    if(_dos_allocmem(6,&state_segment) || _dos_allocmem(4,&field_segment))return 3;
    state=MK_FP(state_segment,8);source=MK_FP(field_segment,0);
    input=fopen("CASES.BIN","rb");output=fopen("EVENTS.BIN","wb");if(!input || !output)return 4;
    if(fread(&cases,2,1,input)!=1)return 5;
    for(case_number=0;case_number<cases;++case_number){
        if(fread(field,54,1,input)!=1 || fread(settings,sizeof(settings),1,input)!=1)return 6;
        kind=field[0]|((unsigned)field[1]<<8);REQUIRE(kind<=3);
        _fmemset(MK_FP(state_segment,0),0xa5,96);_fmemset(state,0,sizeof(*state));_fmemcpy(source,field,54);
        REQUIRE(chat_text_open(state,source+2,52,settings[0],settings[1],settings[2])==1);
        if(state->active){copy=*state;REQUIRE(!chat_text_open(state,source+2,52,settings[0],0,0) && !_fmemcmp(&copy,state,sizeof(copy)));}
        accepted=attempts=turns=0;
        while(state->active && (settings[3]==65535 || accepted<settings[3])){
            copy=*state;before=attempts;REQUIRE(chat_text_step(state,0,sink,&identity)==0 && attempts==before && !_fmemcmp(&copy,state,sizeof(copy)));
            budget=settings[3]==65535?(turns%3?1:65535):1;
            calls=chat_text_step(state,budget,sink,&identity);REQUIRE(calls==attempts-before && calls<=(budget>32?32:budget));
            if(++turns>10000)return 7;
        }
        chat_text_abort(state);copy=*state;before=attempts;
        REQUIRE(chat_text_step(state,32,sink,&identity)==0 && attempts==before && !_fmemcmp(&copy,state,sizeof(copy)));
        REQUIRE(!state->active && !state->phase && !state->at && !state->count);
        REQUIRE(canary(MK_FP(state_segment,0),8) && canary(MK_FP(state_segment,76),20));
        marker[0]=65535;marker[1]=case_number;REQUIRE(fwrite(marker,sizeof(marker),1,output)==1);
    }
    /* Failed validation must not change a reusable context or call the sink. */
    _fmemset(state,0xa5,sizeof(*state));state->active=0;copy=*state;
    for(i=0;i<10;++i){
        _fmemset(source,'X',54);source[2]='A';source[3]=0;
        if(i==0)calls=chat_text_open(state,source+2,0,0,0,0);
        else if(i==1)calls=chat_text_open(state,source+2,53,0,0,0);
        else if(i==2)calls=chat_text_open(state,source+2,52,256,0,0);
        else if(i==3){_fmemset(source+2,'A',52);calls=chat_text_open(state,source+2,52,0,0,0);}
        else if(i==4){source[3]='^';source[4]=0;calls=chat_text_open(state,source+2,52,0,0,0);}
        else if(i==5)calls=chat_text_open(state,(unsigned char CHAT_FAR *)state,52,0,0,0);
        else if(i==6)calls=chat_text_open(state,MK_FP(field_segment,65520),52,0,0,0);
        else if(i==7)calls=chat_text_open(state,0,52,0,0,0);
        else if(i==8){source[2]='^';source[3]='`';source[4]='X';source[5]='^';source[6]=0;calls=chat_text_open(state,source+2,52,0,0,0);}
        else calls=chat_text_open(state,MK_FP(state_segment+1,0),52,0,0,0);
        REQUIRE(!calls && !_fmemcmp(&copy,state,sizeof(copy)));
    }
    REQUIRE(fclose(input)==0 && fclose(output)==0);
    REQUIRE(_dos_freemem(field_segment)==0 && _dos_freemem(state_segment)==0);
    printf("errors=%u vectors=%u validation_controls=10\n",errors,cases);
    return errors?1:0;
}
