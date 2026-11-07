#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "meta_picker.h"
#include "meta_file_prompt.h"
extern meta_picker_state __far picker;
extern meta_file_prompt __far prompt;
extern unsigned char __far entries[META_PICKER_BYTES];
static unsigned frame[2000],prior[2000],checks;
static char stem[9],expected[9],selected[9];
static unsigned word(FILE *f){unsigned n;if(fread(&n,2,1,f)!=1)return 0xffff;return n;}
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %u check %u phase %u count %u top %u row %u\r\n",__LINE__,checks,picker.phase,picker.count,picker.top,picker.row);return 1;}}while(0)
static int get(FILE *f,void *p,unsigned n){return fread(p,1,n,f)==n;}
static unsigned ds(void);
#pragma aux ds = "mov ax,ds" value [ax] modify [];
static unsigned ss(void);
#pragma aux ss = "mov ax,ss" value [ax] modify [];
static unsigned finish(void)
{unsigned n=0;while(picker.phase==META_PICKER_SORT && ++n<20000)if(meta_picker_sort_step(&picker,64))return 0;return picker.phase==META_PICKER_ACTIVE;}
static int view(void)
{
 unsigned r,c,i,j,attr,at;
 for(i=0;i<2000;++i)frame[i]=prior[i]=0x2700|(i%224+32);
 if(meta_picker_draw(&picker,frame,0x1f))return 0;
 for(i=0;i<2000;++i)if((i/80<3 || i/80>21 || i%80<32 || i%80>47) && frame[i]!=prior[i])return 0;
 for(r=0;r<15 && picker.top+r<picker.count;++r){
  attr=r==picker.row?0x71:0x1f;at=(picker.top+r)*9;
  j=0;while(j<8 && entries[at+j])++j;
  for(c=0;c<8;++c)if(frame[(r+5)*80+35+c]!=((attr<<8)|(c<j?entries[at+c]:' ')))return 0;
 }return 1;
}
int main(void)
{
 FILE *f=fopen("CASES.BIN","rb");unsigned cases,index,count,n,i,key,top,row,bells,result,observed,status,states=0;
 CHECK(ds()==ss() && FP_SEG(&picker)!=ds() && FP_SEG(entries)!=ds());CHECK(f && word(f)==0x4b50);cases=word(f);
 for(index=0;index<cases;++index){
  count=word(f);CHECK(!meta_picker_begin(&picker,entries));
  for(i=0;i<count;++i){CHECK(get(f,stem,9));CHECK(!meta_picker_add(&picker,stem));}
  CHECK(!meta_picker_seal(&picker) && finish());
  for(i=0;i<count;++i){CHECK(get(f,expected,9));CHECK(!_fmemcmp(entries+i*9,expected,9));}
  observed=0;n=word(f);
  for(i=0;i<n;++i){
   key=word(f);top=word(f);row=word(f);bells=word(f);
   CHECK(picker.top==top && picker.row==row && observed==bells && view());status=meta_picker_key(&picker,key);if(status==META_PICKER_BELL)++observed;else CHECK(status==META_PICKER_OK);++states;
  }
  result=word(f);CHECK(get(f,expected,9));bells=word(f);CHECK(observed==bells);
  memset(selected,0xa5,9);status=meta_picker_selected(&picker,selected);
  if(result)CHECK(picker.phase==META_PICKER_ACCEPT && !status && !memcmp(selected,expected,9));
  else{CHECK(picker.phase==META_PICKER_CANCEL && status==META_PICKER_BUSY);for(i=0;i<9;++i)CHECK((unsigned char)selected[i]==0xa5);}
 }
 CHECK(fgetc(f)==EOF && !fclose(f));
 /* Upper bound is maintained far-buffer coverage, NOT original replay coverage. */
 CHECK(!meta_picker_begin(&picker,entries));
 for(i=1001;i;--i){sprintf(stem,"K%04u",i);CHECK(!meta_picker_add(&picker,stem));}
 strcpy(stem,"EXTRA");CHECK(meta_picker_add(&picker,stem)==META_PICKER_LIMIT && picker.count==1001);
 CHECK(!meta_picker_seal(&picker));CHECK(meta_picker_sort_step(&picker,65)==META_PICKER_ARGUMENT);CHECK(finish());
 for(i=0;i<1001;++i){sprintf(stem,"K%04u",i+1);CHECK(!_fstrcmp((const char __far *)entries+i*9,stem));}
 CHECK(!meta_picker_key(&picker,0x4f00) && picker.top==986 && !picker.row);CHECK(!meta_picker_key(&picker,13));CHECK(!meta_picker_selected(&picker,selected) && !strcmp(selected,"K0987"));
 /* Actual composition: empty name -> picker -> chosen stem -> .KEY request. */
 CHECK(meta_file_prompt_begin(&prompt,1,0x0607)==META_FILE_OK);CHECK(meta_file_prompt_key(&prompt,13)==META_FILE_PICK);
 CHECK(!meta_picker_begin(&picker,entries));strcpy(stem,"ZETA");CHECK(!meta_picker_add(&picker,stem));strcpy(stem,"ALPHA");CHECK(!meta_picker_add(&picker,stem));CHECK(!meta_picker_seal(&picker) && finish());CHECK(!meta_picker_key(&picker,0x5000));CHECK(!meta_picker_key(&picker,13));CHECK(!meta_picker_selected(&picker,selected));
 CHECK(meta_file_prompt_pick(&prompt,1,selected)==META_FILE_LOAD && !_fstrcmp(prompt.candidate,"ZETA.KEY"));
 CHECK(meta_file_prompt_begin(&prompt,1,0x0607)==META_FILE_OK);CHECK(meta_file_prompt_key(&prompt,13)==META_FILE_PICK);CHECK(!meta_picker_begin(&picker,entries));CHECK(!meta_picker_seal(&picker) && picker.phase==META_PICKER_EMPTY);CHECK(meta_file_prompt_pick(&prompt,0,0)==META_FILE_CANCEL);
 CHECK(meta_picker_begin((meta_picker_state __far *)MK_FP(ds(),0xfff0),entries)==META_PICKER_ARGUMENT);
 CHECK(meta_picker_begin(&picker,(unsigned char __far *)MK_FP(ds(),0xf000))==META_PICKER_ARGUMENT);
 CHECK(meta_picker_begin(&picker,(unsigned char __far *)&picker)==META_PICKER_ARGUMENT);
 CHECK(!meta_picker_begin(&picker,entries));memset(stem,'A',9);CHECK(meta_picker_add(&picker,stem)==META_PICKER_ARGUMENT && !picker.count);
 CHECK(meta_picker_add(&picker,(const char __far *)entries)==META_PICKER_ARGUMENT && !picker.count);
 strcpy(stem,"VALID");CHECK(!meta_picker_add(&picker,stem));CHECK(!meta_picker_seal(&picker));picker.top=0xffff;picker.row=1;CHECK(meta_picker_key(&picker,13)==META_PICKER_ARGUMENT);
 CHECK(!meta_picker_begin(&picker,entries));strcpy(stem,"VALID");CHECK(!meta_picker_add(&picker,stem));CHECK(!meta_picker_seal(&picker));CHECK(!meta_picker_key(&picker,13));CHECK(meta_picker_selected(&picker,(char __far *)entries)==META_PICKER_ARGUMENT);
 printf("PASS %u checks; %u native cases; %u native states/views;1001 maintained entries;prompt composition\r\n",checks,cases,states);return 0;
}
