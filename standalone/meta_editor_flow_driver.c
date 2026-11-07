#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include <direct.h>
#include "meta_editor.h"
#include "key_editor_faults.h"
extern meta_editor __far editor;
extern unsigned char __far live[540];
extern unsigned char __far proposal[540];
static unsigned checks,pspseg,envseg;
static char initial[64]="C:\\LAB\\TEST.KEY",name[64]="TEST.KEY",out_name[64],out_path[64];
static unsigned char original[540],saved[540];
static unsigned frame[2000],prior[2000];
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %u check %u phase %u model %u notice %u backend %u\r\n",__LINE__,checks,editor.phase,editor.dialog.phase,editor.notice,editor.backend_status);exit(1);}}while(0)
static int put(const char *p,const unsigned char __far *v,unsigned n)
{unsigned i;FILE *f=fopen(p,"wb");if(!f)return 0;for(i=0;i<n;++i)if(fputc(v[i],f)==EOF){fclose(f);return 0;}return !fclose(f);}
static int matches(const char *p,const unsigned char __far *v,unsigned n)
{unsigned i;int ok=1;FILE *f=fopen(p,"rb");if(!f)return 0;for(i=0;i<n;++i)if(fgetc(f)!=v[i])ok=0;if(fgetc(f)!=EOF)ok=0;if(fclose(f))ok=0;return ok;}
static void key(unsigned k){CHECK(!meta_editor_key(&editor,k));}
static unsigned pump(void)
{unsigned n=0,status=0;while(editor.phase!=META_EDITOR_DIALOG && editor.phase!=META_EDITOR_NAME && editor.phase!=META_EDITOR_PICK && editor.phase!=META_EDITOR_CLOSED && editor.phase!=META_EDITOR_FATAL){CHECK(++n<1000);status=meta_editor_step(&editor,1);if(status)break;}return status;}
static void type(const char *p){while(*p)key((unsigned char)*p++);}
static void view(void)
{
 unsigned i;
 for(i=0;i<2000;++i)frame[i]=prior[i]=0x2700|(32+i%224);
 CHECK(!meta_editor_draw(&editor,frame,0x1f));
 for(i=0;i<2000;++i)if(i/80<3 || i/80>21)CHECK(frame[i]==prior[i]);
 if(editor.phase==META_EDITOR_NAME){CHECK(frame[9*80+3]==0x1f4c);for(i=0;i<8;++i)CHECK(frame[9*80+17+i]==(0x1f00|editor.prompt.editor.field[i]));CHECK(meta_editor_cursor(&editor)==0x0911+editor.prompt.editor.cursor);}
}
int main(int argc,char **argv)
{
 unsigned r,i,mode=argc>1?atoi(argv[1]):0,calls;
 CHECK(sizeof(editor)<=16384 && FP_SEG(&editor)!=FP_SEG((void __far *)original));
 CHECK(!_dos_allocmem(16,&pspseg) && !_dos_allocmem(32,&envseg));_fmemset(MK_FP(pspseg,0),0,256);*(unsigned __far *)MK_FP(pspseg,0x2c)=envseg;_fmemset(MK_FP(envseg,0),0,512);_fmemcpy(MK_FP(envseg,0),"PCPLUS=C:\\FALL",15);
 for(i=0;i<540;++i)original[i]=(unsigned char)(32+i%200);
 for(r=0;r<10;++r){original[r*54]=3;original[r*54+1]=0;original[r*54+2]='A'+r;original[r*54+3]=0;}
 _fmemcpy(live,original,540);CHECK(put(initial,original,540));CHECK(put("C:\\LAB\\NEXT.KEY",original,540));CHECK(put("C:\\FALL\\FALL.KEY",original,540));
 key_fault_reset(0);CHECK(!meta_editor_open(&editor,pspseg,live,name,initial,0x0607));calls=key_calls;CHECK(meta_editor_step(&editor,0)==META_EDITOR_BUSY && key_calls==calls);CHECK(meta_editor_open(&editor,pspseg,live,name,initial,0x0607)==META_EDITOR_BUSY);CHECK(!pump());view();
 if(mode){
  key('R');key(13);key('!');key(13);key('S');key_fault_reset(KF_CLOSE_STAGE);CHECK(meta_editor_step(&editor,1)==META_EDITOR_RECOVERY && editor.phase==META_EDITOR_FATAL && editor.owner.phase==META_OWNER_HELD);calls=key_calls;CHECK(meta_editor_step(&editor,1)==META_EDITOR_RECOVERY && meta_editor_stop(&editor)==META_EDITOR_RECOVERY && meta_editor_key(&editor,27)==META_EDITOR_RECOVERY && key_calls==calls);CHECK(meta_editor_proposal(&editor,proposal,out_name,out_path)==META_EDITOR_ARGUMENT);CHECK(matches(initial,original,540));view();printf("PASS fatal %u checks;held owner cannot close/propose/restart\r\n",checks);return 0;
 }
 /* Revision and cancellation keep native definitions and do not write disk. */
 key('R');key(13);key('!');key(13);CHECK(editor.dialog.records[2]=='!' && matches(initial,original,540));
 key('L');view();key(27);CHECK(editor.phase==META_EDITOR_DIALOG && !editor.dialog.status && editor.dialog.records[2]=='!');
 key('L');key(13);CHECK(editor.phase==META_EDITOR_PLAN);key(27);CHECK(!editor.dialog.status);
 key('L');key(13);CHECK(!meta_editor_step(&editor,1) && editor.phase==META_EDITOR_SCAN);key(27);CHECK(editor.phase==META_EDITOR_DIALOG && !editor.dialog.status);
 key('S');calls=key_calls;CHECK(meta_editor_step(&editor,0)==META_EDITOR_BUSY && key_calls==calls);key(27);CHECK(matches(initial,original,540) && !editor.dialog.status);
 key('S');CHECK(!pump() && matches(initial,editor.dialog.records,540));
 /* Explicit typed load, then missing-file default creation. */
 key('L');type("next");key(13);CHECK(!pump() && !_fstrcmp(editor.dialog.name,"NEXT.KEY") && !_fstrcmp(editor.current_path,"C:\\LAB\\NEXT.KEY"));
 _fmemcpy(saved,editor.dialog.records,540);key('L');type("new");key(13);CHECK(!pump() && editor.owner.created && matches("C:\\FALL\\NEW.KEY",editor.dialog.records,540));
 for(r=0;r<10;++r)for(i=0;i<54;++i)CHECK(editor.dialog.records[r*54+i]==(i<3?(i==0?3:0):saved[r*54+i]));
 CHECK(put("C:\\LAB\\BAD.KEY",original,539));_fmemcpy(saved,editor.dialog.records,540);key('L');type("bad");key(13);CHECK(pump()==META_EDITOR_IO && editor.phase==META_EDITOR_DIALOG && editor.dialog.status && !_fmemcmp(editor.dialog.records,saved,540) && !_fstrcmp(editor.current_path,"C:\\FALL\\NEW.KEY"));
 /* Current picker list and frozen PCPLUS fallback list. */
 key('L');key(13);CHECK(!pump() && editor.phase==META_EDITOR_PICK);view();key(27);CHECK(!editor.dialog.status);
 CHECK(!chdir("C:\\EMPTY"));key('L');key(13);CHECK(!pump() && editor.phase==META_EDITOR_PICK && editor.fallback);view();key(13);CHECK(!pump() && !_fstrcmp(editor.current_path,"C:\\FALL\\FALL.KEY"));CHECK(!chdir("C:\\LAB"));
 /* Empty both lists is a notice, not a failed/corrupt load. */
 _fmemset(MK_FP(envseg,0),0,512);CHECK(!chdir("C:\\EMPTY"));key('L');key(13);CHECK(!pump() && editor.phase==META_EDITOR_DIALOG && editor.notice==2 && !editor.dialog.status);view();CHECK(!chdir("C:\\LAB"));
 key('R');key(13);key('?');key(13);_fmemcpy(saved,editor.dialog.records,540);key(27);CHECK(editor.phase==META_EDITOR_CLOSING);CHECK(meta_editor_step(&editor,0)==META_EDITOR_BUSY);CHECK(!pump() && editor.phase==META_EDITOR_CLOSED && meta_key_owner_exec_allowed());
 CHECK(!meta_editor_proposal(&editor,proposal,out_name,out_path) && !_fmemcmp(proposal,saved,540) && !strcmp(out_path,"C:\\FALL\\FALL.KEY") && !strcmp(out_name,"FALL.KEY"));CHECK(meta_editor_matches(&editor,live,initial));CHECK(!meta_editor_matches(&editor,live,out_path));CHECK(matches("C:\\FALL\\FALL.KEY",original,540));live[0]=0;CHECK(!meta_editor_matches(&editor,live,initial));live[0]=original[0];
 CHECK(!meta_editor_open(&editor,pspseg,live,name,initial,0x0607));key(27);CHECK(!meta_editor_step(&editor,0) && editor.phase==META_EDITOR_CLOSED);CHECK(!_fmemcmp(live,original,540));
 CHECK(!_dos_freemem(envseg) && !_dos_freemem(pspseg));
 printf("PASS %u checks;state %u;serviced edit/name/picker/scan/load/create/save/cancel/close proposal\r\n",checks,sizeof(editor));return 0;
}
