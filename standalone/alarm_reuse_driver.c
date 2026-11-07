/* Test-only CLI replacement: retain real serial/render ownership across three
 * complete VM invocations. No interpreter/service/error substitution. */
#define main unused_original_runner_main
#include "../src/aspect/runner.c"
#undef main
#include "../src/aspect/alarm_dos.h"
#include "../src/aspect/script_file_runtime.h"
#include "../src/aspect/external_unwind.h"
#include <dos.h>
extern unsigned runtime_depth;
static unsigned probe_flags(void);
#pragma aux probe_flags = "pushf" "pop ax" value [ax] modify exact [ax];
static unsigned probe_ds(void);
#pragma aux probe_ds = "mov ax,ds" value [ax] modify exact [ax];
static unsigned probe_ss(void);
#pragma aux probe_ss = "mov ax,ss" value [ax] modify exact [ax];
static struct {
 unsigned magic,version,count;
 unsigned rows[3][14];
 unsigned char before[20],after[20];
} record;
int main(int argc,char **argv)
{
 unsigned i,j,result=0,first=0,status,limit=10000;const char *serial=0;
 FILE *file;void (__interrupt __far *vector)(void);
 if(argc<2||argc>4||!path_ok(argv[1]))return 64;
 for(i=2;i<(unsigned)argc;++i){
  if(argv[i][0]=='/'&&(argv[i][1]=='S'||argv[i][1]=='s'))serial=argv[i];
  else if(!budget(argv[i],&limit))return 64;
 }
 if(runtime_serial_wait_configure(runtime_environment_get("PCPLUS_TXWAIT")))return 64;
 if(notice_input_exit_prepare())return ASPECT_RUN_STATE;
 if(!serial||aspect_serial_open(serial))return ASPECT_RUN_SERIAL;
 record.magic=0x414c;record.version=1;record.count=0;
 _fmemcpy(record.before,MK_FP(_psp,0x18),20);
 for(i=0;i<3;++i){
  result=aspect_runtime_run(i?"D:\\RECOVER.ASX":argv[1],limit);
  if(!i)first=result;
  vector=_dos_getvect(0);
  record.rows[i][0]=result;record.rows[i][1]=runtime_last_opcode;
  record.rows[i][2]=alarm_dos_active();record.rows[i][3]=alarm_coop_active();
  record.rows[i][4]=alarm_coop_native_aborted();
  record.rows[i][5]=runtime_external_checkpoint_active();
  record.rows[i][6]=runtime_live;record.rows[i][7]=runtime_script_file_live;
  record.rows[i][8]=runtime_depth;record.rows[i][9]=probe_ds();
  record.rows[i][10]=probe_ss();record.rows[i][11]=probe_flags()&0x600;
  record.rows[i][12]=FP_SEG(vector);record.rows[i][13]=FP_OFF(vector);
  ++record.count;
  if(record.rows[i][2]||record.rows[i][3])break;
 }
 _fmemcpy(record.after,MK_FP(_psp,0x18),20);
 file=fopen("D:\\REUSE.BIN","wb");if(!file)return ASPECT_RUN_IO;
 j=fwrite(&record,1,sizeof(record),file);status=fclose(file);
 if(j!=sizeof(record)||status)return ASPECT_RUN_IO;
 if(aspect_serial_active){status=aspect_serial_close();if(status)return ASPECT_RUN_SERIAL;}
 if(first)report_error(first);
 status=aspect_render_finish();if(status)return status;
 status=notice_input_exit_finish(first);return status;
}
