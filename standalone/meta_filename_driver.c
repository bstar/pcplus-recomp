#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <direct.h>
#include "meta_file_prompt.h"
#include "meta_dialog.h"
#include "key_editor_file.h"
extern meta_filename_state __far filename_state;
extern meta_file_prompt __far prompt_state;
extern meta_dialog_state __far dialog_state;
extern unsigned char __far file_records[1620];
#define baseline file_records
#define replacement (file_records+540)
#define loaded (file_records+1080)
static unsigned char expected[64],before[64],frame[8];
static unsigned char table[540];
static char name[64]="MAIN.KEY",path[64]="C:\\LAB\\MAIN.KEY",selected[64],stem[9]="main",s[64];
static unsigned checks;
static directory_replace_result saved;
static key_actions_dos_result read_result;
static unsigned word(FILE *f){unsigned n;if(fread(&n,2,1,f)!=1)return 0xffff;return n;}
static int get(FILE *f,void *p,unsigned n){return fread(p,1,n,f)==n;}
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %u check %u\r\n",__LINE__,checks);return 1;}}while(0)
static unsigned ds(void);
#pragma aux ds = "mov ax,ds" value [ax] modify [];
static unsigned ss(void);
#pragma aux ss = "mov ax,ss" value [ax] modify [];
static int put(const char *p,const unsigned char __far *data)
{unsigned i;FILE *f=fopen(p,"wb");if(!f)return 0;for(i=0;i<540;++i)if(fputc(data[i],f)==EOF){fclose(f);return 0;}return !fclose(f);}
int main(void)
{
 FILE *f=fopen("C:\\CASES.BIN","rb");unsigned cases,c,n,i,j,key,cursor,shape,bells,result,total=0,status;
 CHECK(ds()==ss() && FP_SEG(&filename_state)!=ds() && FP_SEG(&prompt_state)!=ds());
 CHECK(f && word(f)==0x4e46);cases=word(f);
 for(c=0;c<cases;++c){
  CHECK(meta_filename_begin(&filename_state,0x0607)==META_FILENAME_ACTIVE);n=word(f);
  for(i=0;i<n;++i){
   key=word(f);CHECK(get(f,frame,8));cursor=word(f);shape=word(f);bells=word(f);
   CHECK(!_fmemcmp(filename_state.field,frame,8) && filename_state.cursor==cursor && meta_filename_shape(&filename_state)==shape && total==bells);
   status=meta_filename_key(&filename_state,key);if(status==META_FILENAME_BELL)++total;
   CHECK(status!=META_FILENAME_ARGUMENT);
  }
  CHECK(get(f,expected,64));result=word(f);bells=word(f);shape=word(f);CHECK(total==bells && filename_state.result==result && meta_filename_shape(&filename_state)==shape);
  memcpy(before,"UNCHANGED",10);memset(before+10,0xa5,54);
  if(result!=0xffff)CHECK(meta_filename_commit(&filename_state,before)==META_FILENAME_ACCEPT);
  else CHECK(meta_filename_commit(&filename_state,before)==META_FILENAME_ARGUMENT);
  CHECK(!memcmp(before,expected,64));total=0;
 }
 CHECK(fgetc(f)==EOF && !fclose(f));
 /* Field routing preserves native eight-cell name behavior; Save has no prompt. */
 CHECK(meta_file_prompt_begin(&prompt_state,0,0x0607)==META_FILE_SAVE && prompt_state.phase==META_FILE_READY && !prompt_state.candidate[0]);
 CHECK(meta_file_prompt_key(&prompt_state,'A')==META_FILE_BUSY);
 CHECK(meta_file_prompt_begin(&prompt_state,1,0x0607)==META_FILE_OK);
 CHECK(meta_file_prompt_key(&prompt_state,13)==META_FILE_PICK && prompt_state.phase==META_FILE_PICKER);
 CHECK(meta_file_prompt_key(&prompt_state,27)==META_FILE_BUSY);
 CHECK(meta_file_prompt_pick(&prompt_state,1,stem)==META_FILE_LOAD && !_fstrcmp(prompt_state.candidate,"MAIN.KEY"));
 CHECK(meta_file_prompt_begin(&prompt_state,1,0x0607)==META_FILE_OK);CHECK(meta_file_prompt_key(&prompt_state,13)==META_FILE_PICK);CHECK(meta_file_prompt_pick(&prompt_state,0,0)==META_FILE_CANCEL);
 CHECK(meta_file_prompt_begin(&prompt_state,1,0x0607)==META_FILE_OK);CHECK(meta_file_prompt_key(&prompt_state,27)==META_FILE_CANCEL);
 CHECK(meta_file_prompt_begin(&prompt_state,1,0x0607)==META_FILE_OK);
 for(i=0;i<4;++i)CHECK(meta_file_prompt_key(&prompt_state,"next"[i])==META_FILE_OK);
 CHECK(meta_file_prompt_key(&prompt_state,13)==META_FILE_LOAD && !_fstrcmp(prompt_state.candidate,"NEXT.KEY"));
 /* Compose real checked files with Meta overview, field, load completion/save. */
 for(i=0;i<540;++i)table[i]=0xa5;
 for(i=0;i<10;++i){j=i*54;table[j]=3;table[j+1]=0;table[j+2]='A'+i;table[j+3]=0;}
 _fmemcpy(baseline,table,540);CHECK(put(path,baseline));
 for(i=0;i<10;++i)table[i*54+2]='K'+i;
 _fmemcpy(replacement,table,540);CHECK(put("C:\\LAB\\NEXT.KEY",replacement));
 CHECK(!meta_dialog_open(&dialog_state,baseline,name,0x0607));CHECK(meta_dialog_key(&dialog_state,'L')==META_DIALOG_LOAD);
 /* The owner freezes its absolute directory and resolves the candidate; no CWD
  * mutation/fallback. This fixture owner is not the application's resource owner. */
 strcpy(selected,"C:\\LAB\\");_fstrcpy(s,prompt_state.candidate);strcat(selected,s);
 CHECK(!key_editor_file_load(selected,loaded,&read_result));CHECK(!meta_dialog_complete(&dialog_state,0,loaded,prompt_state.candidate));
 CHECK(!_fmemcmp(dialog_state.records,replacement,540) && !_fstrcmp(dialog_state.name,"NEXT.KEY"));_fmemcpy(baseline,loaded,540);
 CHECK(!meta_dialog_key(&dialog_state,'R'));CHECK(!meta_dialog_key(&dialog_state,13));CHECK(!meta_dialog_key(&dialog_state,'!'));CHECK(!meta_dialog_key(&dialog_state,13));
 CHECK(meta_dialog_key(&dialog_state,'S')==META_DIALOG_SAVE);CHECK(meta_file_prompt_begin(&prompt_state,0,0x0607)==META_FILE_SAVE);
 CHECK(!key_editor_file_save(selected,baseline,dialog_state.records,&saved) && saved.installed);
 CHECK(!meta_dialog_complete(&dialog_state,0,0,0));CHECK(!key_editor_file_load(selected,loaded,&read_result));CHECK(!_fmemcmp(loaded,dialog_state.records,540) && loaded[2]=='!');
 _fmemcpy(baseline,dialog_state.records,540);
 CHECK(meta_dialog_key(&dialog_state,'L')==META_DIALOG_LOAD);CHECK(meta_file_prompt_begin(&prompt_state,1,0x0607)==META_FILE_OK);CHECK(meta_file_prompt_key(&prompt_state,27)==META_FILE_CANCEL);CHECK(!meta_dialog_complete(&dialog_state,1,0,0));CHECK(!_fmemcmp(baseline,dialog_state.records,540));
 CHECK(meta_dialog_key(&dialog_state,'L')==META_DIALOG_LOAD);CHECK(meta_file_prompt_begin(&prompt_state,1,0x0607)==META_FILE_OK);
 for(i=0;i<6;++i)CHECK(meta_file_prompt_key(&prompt_state,"absent"[i])==META_FILE_OK);CHECK(meta_file_prompt_key(&prompt_state,13)==META_FILE_LOAD);
 CHECK(key_editor_file_load("C:\\LAB\\ABSENT.KEY",loaded,&read_result)==KEY_ACTIONS_DOS_OPEN);CHECK(!meta_dialog_complete(&dialog_state,1,0,0));CHECK(!_fmemcmp(baseline,dialog_state.records,540) && !_fstrcmp(dialog_state.name,"NEXT.KEY"));
 /* Far-state and pending-picker guards, no mutation on malformed completion. */
 CHECK(meta_filename_begin(&filename_state,0x0607)==META_FILENAME_ACTIVE);
 CHECK(meta_filename_key(&filename_state,13)==META_FILENAME_ACCEPT);
 CHECK(meta_filename_commit(&filename_state,(unsigned char __far *)&filename_state)==META_FILENAME_ARGUMENT);
 CHECK(meta_filename_commit(&filename_state,(unsigned char __far *)MK_FP(ds(),0xfff0))==META_FILENAME_ARGUMENT);
 CHECK(meta_filename_key(&filename_state,'X')==META_FILENAME_ARGUMENT);
 filename_state.cookie=0;CHECK(meta_filename_key(&filename_state,13)==META_FILENAME_ARGUMENT && meta_filename_shape(&filename_state)==0xffff);
 CHECK(meta_filename_begin(&filename_state,0x0607)==META_FILENAME_ACTIVE);filename_state.cursor=8;CHECK(meta_filename_key(&filename_state,'X')==META_FILENAME_ARGUMENT);
 CHECK(meta_filename_begin((meta_filename_state __far *)MK_FP(ds(),0xfff0),0)==META_FILENAME_ARGUMENT);
 CHECK(meta_file_prompt_begin((meta_file_prompt __far *)MK_FP(0xffff,0),1,0)==META_FILE_ARGUMENT);
 CHECK(meta_file_prompt_begin(&prompt_state,2,0)==META_FILE_ARGUMENT);
 CHECK(meta_file_prompt_begin(&prompt_state,1,0x0607)==META_FILE_OK);CHECK(meta_file_prompt_key(&prompt_state,13)==META_FILE_PICK);
 CHECK(meta_file_prompt_pick(&prompt_state,1,(char __far *)prompt_state.candidate)==META_FILE_ARGUMENT && prompt_state.phase==META_FILE_PICKER);
 strcpy(stem,"ABCDEFGH");stem[8]='X';CHECK(meta_file_prompt_pick(&prompt_state,1,stem)==META_FILE_ARGUMENT && prompt_state.phase==META_FILE_PICKER);
 stem[0]=0;CHECK(meta_file_prompt_pick(&prompt_state,1,stem)==META_FILE_ARGUMENT && prompt_state.phase==META_FILE_PICKER);
 CHECK(meta_file_prompt_pick(&prompt_state,0,0)==META_FILE_CANCEL);
 CHECK(!meta_dialog_key(&dialog_state,27) && dialog_state.phase==META_DIALOG_CLOSED);
 CHECK(getcwd(s,64)!=0 && !strcmp(s,"D:\\LAB"));
 printf("PASS %u checks; %u native filename cases; composed load/edit/save/cancel/missing file\r\n",checks,cases);return 0;
}
