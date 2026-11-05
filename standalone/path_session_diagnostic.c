#include "../src/filesystem/path_session.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
#ifdef PATH_SESSION_BOUNDARY
extern unsigned get_calls,native_calls,fault;
unsigned __cdecl path_native_real(const char *);
unsigned __cdecl path_drive_real(void);
unsigned __cdecl path_select_real(unsigned);
unsigned __cdecl path_cwd_real(unsigned,char *);
unsigned __cdecl path_native_change(const char *p)
{++native_calls;if((fault==2 && native_calls==2) || fault==3)return 1;return path_native_real(p);}
unsigned __cdecl path_current_drive(void){return path_drive_real();}
unsigned __cdecl path_select_drive(unsigned d){return path_select_real(d);}
unsigned __cdecl path_getcwd(unsigned d,char *out)
{
 unsigned result;++get_calls;
 if(((fault==1 || fault==2) && get_calls==2) || (fault==4 && get_calls==1))return 5;
 result=path_cwd_real(d,out);if(fault==5 && !result)out[64]=0;return result;
}
unsigned __far __cdecl session_test_native(const char *p){return path_native_real(p);}
unsigned __far __cdecl session_test_state(path_session_state *out)
{
 unsigned i;unsigned char *p=(unsigned char *)out;
 for(i=0;i<sizeof(*out);++i)p[i]=((unsigned char __based(__segname("_CODE")) *)&path_session_storage)[i];
 return FP_SEG((void __far *)&path_session_storage);
}
#else
unsigned get_calls,native_calls,fault;
static unsigned checks,failures;
unsigned __far __cdecl session_test_native(const char *);
unsigned __far __cdecl session_test_state(path_session_state *);
static void check(unsigned ok,const char *name)
{++checks;if(!ok){++failures;printf("FAIL %s\n",name);}}
static void current(const char *wanted)
{
 char actual[68],relative[68];union REGS a,b;unsigned d;
 check(path_session_current(actual)==PATH_OK && !strcmp(actual,wanted),"session current");
 a.h.ah=0x19;intdos(&a,&b);d=b.h.al;
 relative[0]=(char)('A'+d);relative[1]=':';relative[2]='\\';
 a.h.ah=0x47;a.h.dl=(unsigned char)(d+1);a.x.si=(unsigned)(relative+3);intdos(&a,&b);
 check(!b.x.cflag && !strcmp(relative,wanted),"independent DOS drive/path");
}
static void reset(unsigned f){get_calls=native_calls=0;fault=f;}
int main(int argc,char **argv)
{
 path_result r,before;path_session_state state;char output[68],saved[68];unsigned mode,segment,calls;
 if(argc!=2)return 20;mode=(unsigned)(argv[1][0]-'0');
 segment=session_test_state(&state);
 check(sizeof(state)==76 && state.state==PATH_SESSION_COLD,"initialized cold76-byte state");
 check(segment!=FP_SEG((void __far *)&get_calls),"mutable state segment differs from DGROUP");
 reset(0);check(path_session_restore()==PATH_OK && !get_calls && !native_calls,"uninitialized restore no-op");
 memset(&r,0xa5,sizeof(r));before=r;
 check(path_session_change("C:\\ONE",&r)==PATH_SESSION_UNBOUND && !memcmp(&r,&before,sizeof(r)),"unbound change preserves result");
 check(session_test_native("C:\\ONE")==0,"initial actual directory");
 if(mode==5){
  reset(5);memset(output,0xa5,sizeof(output));memcpy(saved,output,sizeof(output));
  check(path_session_current(output)==PATH_DRIVE && !memcmp(output,saved,sizeof(output)),"overflow query preserves output");
  check(path_session_begin()==PATH_DRIVE,"overflow startup query refused");
  session_test_state(&state);check(state.state==PATH_SESSION_COLD && state.last_dos_error==13,"failed begin retains cold state");
  reset(0);
 }
 if(mode==6)check(session_test_native("C:\\AAAAAAAA\\BBBBBBBB\\CCCCCCCC\\DDDDDDDD\\EEEEEEEE\\FFFFFFFF\\GGGGGGGG")==0,"long startup directory");
 check(path_session_begin()==PATH_OK,"begin binds");
 segment=session_test_state(&state);strcpy(saved,state.startup_path);
 check(state.state==PATH_SESSION_ACTIVE && !state.quarantined && state.startup_drive==2,"active frozen startup");
 check(path_session_current(0)==PATH_ARGUMENT,"null current output refused");
 if(mode==0 || mode==5 || mode==6){
  check(path_session_change("D:\\TWO",&r)==PATH_OK,"crossdrive change");current("D:\\TWO");
  check(path_session_begin()==PATH_OK,"begin reentry");session_test_state(&state);
  check(!strcmp(state.startup_path,saved) && state.startup_drive==2,"begin never overwrites startup");
  check(path_session_change("",&r)==PATH_ARGUMENT,"owner argument validation");
  check(path_session_change("SUB",0)==PATH_ARGUMENT,"null change result refused");
  strcpy(r.current_path,"SUB");before=r;
  check(path_session_change(r.current_path,&r)==PATH_ARGUMENT && !memcmp(&r,&before,sizeof(r)),"owner overlap validation");
  check(path_session_restore()==PATH_OK,"restore startup exact path and drive");current(saved);
 }else if(mode==1){
  reset(1);check(path_session_change("SUB",&r)==PATH_VERIFY && !r.rollback_failed,"verification fault rolled back");
  check(!path_session_quarantined(),"verified rollback does not quarantine");reset(0);current("C:\\ONE");
  check(path_session_restore()==PATH_OK,"restore after verified rollback");
 }else if(mode==2){
  reset(2);check(path_session_change("SUB",&r)==PATH_ROLLBACK && r.rollback_failed,"failed rollback surfaced");
  check(path_session_quarantined(),"failed rollback latches quarantine");
  before=r;calls=native_calls+get_calls;
  check(path_session_change("D:\\TWO",&r)==PATH_SESSION_QUARANTINED && !memcmp(&r,&before,sizeof(r)) && calls==native_calls+get_calls,"quarantine refuses further mutation");
  check(path_session_begin()==PATH_SESSION_QUARANTINED,"reentry cannot clear quarantine");
  reset(0);current("C:\\ONE\\SUB");reset(3);
  check(path_session_restore()==PATH_CHANGE && path_session_quarantined(),"failed native restore retains quarantine");
  session_test_state(&state);check(!strcmp(state.startup_path,saved) && state.state==PATH_SESSION_ACTIVE,"failed restore retains saved identity");
  reset(0);check(path_session_restore()==PATH_OK && !path_session_quarantined(),"restore retry clears verified quarantine");current(saved);
 }else if(mode==3){
  check(path_session_change("D:\\TWO",&r)==PATH_OK,"move before restore verification fault");reset(4);
  check(path_session_restore()==PATH_VERIFY && path_session_quarantined(),"failed restore verification quarantines");
  session_test_state(&state);check(state.last_dos_error==5 && !strcmp(state.startup_path,saved),"restore failure retains DOS error and startup");
  reset(0);check(path_session_restore()==PATH_OK && !path_session_quarantined(),"failed restore verification retry");current(saved);
 }else return 21;
 reset(0);check(path_session_restore()==PATH_OK && !get_calls && !native_calls,"restored restore idempotent no-op");
 check(path_session_begin()==PATH_OK,"restored begin no-op");session_test_state(&state);
 check(state.state==PATH_SESSION_RESTORED && !strcmp(state.startup_path,saved),"restored saved identity retained");
 memset(&r,0xa5,sizeof(r));before=r;
 check(path_session_change("D:\\TWO",&r)==PATH_SESSION_UNBOUND && !memcmp(&r,&before,sizeof(r)),"restored change refuses");
 check(!path_session_quarantined(),"verified restore clears quarantine");
 check(session_test_native("C:\\")==0,"diagnostic cleanup root");
 printf("PATHSESSION mode=%u checks=%u failures=%u state_segment=%04X data_segment=%04X\n",mode,checks,failures,segment,FP_SEG((void __far *)&get_calls));
 return failures?1:0;
}
#endif
