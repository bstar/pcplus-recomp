#include "../src/filesystem/path_owner.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static unsigned checks,failures,get_calls,native_calls,fault;
unsigned __cdecl path_native_real(const char *p);
unsigned __cdecl path_drive_real(void);
unsigned __cdecl path_select_real(unsigned drive);
unsigned __cdecl path_cwd_real(unsigned drive,char *out);
unsigned __cdecl path_native_change(const char *p)
{++native_calls;if(fault==2 && native_calls==2)return 1;return path_native_real(p);}
unsigned __cdecl path_current_drive(void){return path_drive_real();}
unsigned __cdecl path_select_drive(unsigned drive){return path_select_real(drive);}
unsigned __cdecl path_getcwd(unsigned drive,char *out)
{++get_calls;if(fault && get_calls==2)return 5;return path_cwd_real(drive,out);}
static void check(int ok,const char *name)
{++checks;if(!ok){++failures;printf("FAIL %s\n",name);}}
static unsigned actual_drive(void)
{union REGS a,b;a.h.ah=0x19;intdos(&a,&b);return b.h.al;}
static void expect(const char *path,const char *cwd,unsigned drive)
{
 path_result r;char current[68];union REGS a,b;
 unsigned result=path_change(path,&r);
 check(result==PATH_OK && r.status==PATH_OK && !r.rollback_failed,"change status");
 check(!strcmp(r.current_path,cwd) && r.drive_after==drive,"returned path/drive");
 check(actual_drive()==drive,"independent default drive");
 a.h.ah=0x47;a.h.dl=(unsigned char)(drive+1);a.x.si=(unsigned)(current+3);
 current[0]=(char)('A'+drive);current[1]=':';current[2]='\\';intdos(&a,&b);
 check(!b.x.cflag && !strcmp(current,cwd),"independent DOS per-drive directory");
}
int main(void)
{
 path_result r,before;char text[70];unsigned native;
 expect("C:\\ONE","C:\\ONE",2);
 expect("SUB","C:\\ONE\\SUB",2);
 expect("..","C:\\ONE",2);
 expect("D:\\TWO","D:\\TWO",3);
 expect("C:","C:\\ONE",2);
 expect("D:","D:\\TWO",3);
 expect("c:SUB","C:\\ONE\\SUB",2);
 expect("\\ONE","C:\\ONE",2);
 check(path_change("MISSING",&r)==PATH_CHANGE && actual_drive()==2,"missing directory unchanged");
 native=path_native_change("Y:");
 check(native==0 && actual_drive()==2,"retained native invalid-drive false success");
 check(path_change("Y:",&r)==PATH_DRIVE && r.dos_error==15 && actual_drive()==2,"guarded missing drive refused");
 memset(&r,0xa5,sizeof(r));before=r;
 check(path_change("",&r)==PATH_ARGUMENT && !memcmp(&r,&before,sizeof(r)),"empty leaves result");
 check(path_change(0,&r)==PATH_ARGUMENT && !memcmp(&r,&before,sizeof(r)),"null leaves result");
 check(path_change("ONE",0)==PATH_ARGUMENT,"null result");
 check(path_change("*",&r)==PATH_ARGUMENT && !memcmp(&r,&before,sizeof(r)),"wildcard refused");
 check(path_change("[:",&r)==PATH_ARGUMENT && !memcmp(&r,&before,sizeof(r)),"invalid drive syntax");
 check(path_change("\\\\REMOTE\\SHARE",&r)==PATH_ARGUMENT && !memcmp(&r,&before,sizeof(r)),"UNC refused");
 memset(text,'A',64);text[64]=0;
 check(path_change(text,&r)==PATH_ARGUMENT && !memcmp(&r,&before,sizeof(r)),"overlong refused");
 strcpy(r.current_path,"ONE");before=r;
 check(path_change(r.current_path,&r)==PATH_ARGUMENT && !memcmp(&r,&before,sizeof(r)),"overlap refused");
 get_calls=native_calls=0;fault=1;
 check(path_change("SUB",&r)==PATH_VERIFY && !r.rollback_failed && actual_drive()==2 && !strcmp(r.current_path,"C:\\ONE"),"verification failure rolls back");
 fault=0;expect("C:","C:\\ONE",2);
 get_calls=native_calls=0;fault=2;
 check(path_change("SUB",&r)==PATH_ROLLBACK && r.rollback_failed && !strcmp(r.current_path,"C:\\ONE\\SUB"),"failed rollback reports changed context");
 fault=0;expect("C:\\ONE","C:\\ONE",2);
 expect("D:","D:\\TWO",3);
 expect("C:\\","C:\\",2);
 printf("PATHOWNER checks=%u failures=%u\n",checks,failures);
 return failures?1:0;
}
