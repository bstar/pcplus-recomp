/* Actual DOS far-bank frame oracle fixture; no product globals or BIOS calls. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/screen.h"
static unsigned current_cs(void);
#pragma aux current_cs = "mov ax,cs" value [ax] modify exact [ax];
static unsigned errors,steps,words[64];
static FILE *input;
static int compare(chat_screen __far *s)
{
    unsigned at=0,n,i,cursors[4];
    while(at<s->cells){
        n=s->cells-at;if(n>64)n=64;
        if(fread(words,2,n,input)!=n)return 0;
        for(i=0;i<n;++i)if(words[i]!=s->frame[at+i])return 0;
        at+=n;
    }
    if(fread(cursors,2,4,input)!=4)return 0;
    return cursors[0]==s->pane[0].row && cursors[1]==s->pane[0].column &&
           cursors[2]==s->pane[1].row && cursors[3]==s->pane[1].column;
}
int main(void)
{
    unsigned segment,state_segment,table_segment,cases,c,rows,attribute,bar,clear,count,i,j,op[5];
    chat_word __far *allocation;
    unsigned char __far *table;
    chat_screen __far *s;
    chat_screen copy;
    if(sizeof(chat_screen)!=30 || FP_SEG(chat_screen_open)==current_cs())return 2;
    if(_dos_allocmem(501,&segment) || _dos_allocmem(2,&state_segment) || _dos_allocmem(16,&table_segment))return 3;
    allocation=(chat_word __far *)MK_FP(segment,0);s=(chat_screen __far *)MK_FP(state_segment,0);
    table=(unsigned char __far *)MK_FP(table_segment,0);
    input=fopen("ORACLE.BIN","rb");if(!input || fread(&cases,2,1,input)!=1)return 4;
    for(c=0;c<cases;++c){
        if(fread(words,2,5,input)!=5)return 5;
        rows=words[0];attribute=words[1];bar=words[2];clear=words[3];count=words[4];
        allocation[0]=0xa55a;allocation[rows*80+1]=0x5aa5;
        if(!chat_screen_open(s,allocation+1,rows*80,rows,attribute,bar,clear))return 6;
        copy=*s;
        if(chat_screen_open(s,allocation+1,rows*80-1,rows,attribute,bar,clear) ||
           chat_screen_open(s,allocation+1,4000,26,attribute,bar,clear) ||
           chat_screen_open(s,allocation+1,4000,rows,256,bar,clear) ||
           chat_screen_open(s,allocation+1,4000,rows,attribute,256,clear) ||
           chat_screen_open(s,allocation+1,4000,rows,attribute,bar,256) ||
           chat_screen_open(s,(chat_word __far *)MK_FP(segment,0xfff0),4000,rows,attribute,bar,clear) ||
           chat_screen_open(s,0,4000,rows,attribute,bar,clear) ||
           _fmemcmp(&copy,s,sizeof(copy)))return 7;
        if(chat_screen_put(s,2,'X') || chat_screen_receive(s,table,256) ||
           chat_screen_receive(s,(unsigned char __far *)MK_FP(table_segment,0xffff),'X'))return 8;
        s->pane[0].column=80;if(chat_screen_put(s,0,'X'))return 9;s->pane[0].column=copy.pane[0].column;
        if(!compare(s))return 10;
        for(i=0;i<count;++i){
            if(fread(op,2,5,input)!=5)return 11;
            j=op[0]==1;
            if(op[2]){s->pane[j].row=op[3];s->pane[j].column=op[4];}
            if(op[0]<2){if(!chat_screen_put(s,op[0],op[1]))return 12;}
            else{
                for(j=0;j<256;++j)table[j]=op[0]==4?0:op[0]==3?(unsigned char)(j*37+1):(unsigned char)j;
                if(!chat_screen_receive(s,table,op[1]))return 13;
            }
            if(!compare(s)){printf("FRAME FAILURE CASE %u STEP %u\n",c,i);return 14;}
            if(allocation[0]!=0xa55a || allocation[rows*80+1]!=0x5aa5)return 15;
            ++steps;
        }
    }
    fclose(input);
    if(_dos_freemem(table_segment) || _dos_freemem(state_segment) || _dos_freemem(segment))++errors;
    printf("CHAT SCREEN %u CASES %u FRAMES %u ERRORS\n",cases,steps+cases,errors);
    return errors?1:0;
}
