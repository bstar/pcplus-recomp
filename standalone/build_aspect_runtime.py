#!/usr/bin/env python3
"""Source-only incremental native ASPECT execution/ownership diagnostic."""
import hashlib,json,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-runtime'
ASM=[('dispatch','src/aspect/dispatch.asm',None),('abort','src/aspect/abort.asm',None),
 ('keyboard_normalizers','reconstruction/keyboard/core.asm','KEYBOARD_BIOS_ONLY'),
 ('keyboard_detection','reconstruction/keyboard_detection/detect.asm','KEYBOARD_DETECTION_OMF'),
 ('keyboard_owner','src/aspect/keyboard.asm',None),
 ('keyboard_api','src/keyboard/api.asm',None),
 ('globals','src/aspect/global_strings.asm',None),('stack','src/aspect/value_stack.asm',None),
 ('conversions','src/aspect/conversions.asm',None),('conversion_services','src/aspect/conversion_services.asm',None),
 ('console','src/aspect/console_commands.asm',None),
 ('serial_commands','src/aspect/serial_commands.asm',None),
 ('receive_commands','src/aspect/receive_commands.asm',None),
 ('receive_policy','src/aspect/receive_policy.asm',None),
 ('when','src/aspect/when.asm',None),
 ('set_commands','src/aspect/set_commands.asm',None),
 ('break_commands','src/aspect/break_commands.asm','ASPECT_BREAK_RUNTIME'),
 ('end_wait','src/aspect/end_wait.asm',None),
 ('chain_command','src/aspect/chain_command.asm','ASPECT_CHAIN_RUNTIME'),
 ('fetch_command','src/aspect/fetch_command.asm',None),
 ('find_commands','src/aspect/find_commands.asm',None),('case_commands','src/aspect/case_commands.asm',None),
 ('directory','src/aspect/directory_builtins.asm',None),
 ('script_file_setting','src/aspect/script_file_setting.asm',None),
 ('script_file_commands','src/aspect/script_file_commands.asm',None),('script_file_services','src/aspect/script_file_services.asm',None),('script_file_bridge','src/aspect/script_file_bridge.asm',None),
 ('path_commands','src/aspect/path_commands.asm',None),('path_services','src/aspect/path_services.asm',None),('path_state','src/aspect/path_state.asm',None),
 ('path_error_access','reconstruction/program_exec/error_access.asm','PROGRAM_EXEC_OMF'),
 ('path_error_exec','reconstruction/program_exec/error_exec.asm','PROGRAM_EXEC_OMF'),
 ('path_map_error','reconstruction/program_exec/map_error.asm','PROGRAM_EXEC_OMF'),
 ('flow','src/aspect/control_flow.asm',None),('parameters','src/aspect/parameters.asm',None),('strings','src/aspect/string_operands.asm',None),('string_commands','src/aspect/string_commands.asm',None),('string_services','src/aspect/string_services.asm',None),
 ('string_strlen','reconstruction/program_exec/strlen.asm','PROGRAM_EXEC_OMF'),('string_strncmp','reconstruction/program_exec/strncmp.asm','PROGRAM_EXEC_OMF'),
 ('string_strcpy','reconstruction/program_exec/strcpy.asm','PROGRAM_EXEC_OMF'),('string_strcmpi','reconstruction/program_exec/strcmpi.asm','PROGRAM_EXEC_OMF'),
 ('string_concat','reconstruction/directory_dial/append.asm','DIRECTORY_DIAL_OMF'),('string_upper','reconstruction/directory_dial/uppercase.asm','DIRECTORY_DIAL_OMF'),('operands','src/aspect/numeric_operands.asm',None),
 ('operations','src/aspect/numeric_operations.asm',None),
 ('arithmetic','src/aspect/arithmetic.asm',None),('long','src/aspect/long_arithmetic.asm',None),('support','src/aspect/expression_support.asm',None),
 ('copy','reconstruction/erase/move_bytes.asm','ERASE_OMF'),
 ('setjmp','reconstruction/transfer_session/setjmp.asm','TRANSFER_SESSION_OMF'),
 ('longjmp','reconstruction/transfer_session/longjmp.asm','TRANSFER_SESSION_OMF'),
 ('bridge','src/aspect/runtime_bridge.asm',None)]
SUPPORT=[(1,0xd2a0,0xd2d6,109184-0xd0d0),(2,0xd3f2,0xd408,109184-0xd0d0),
 (3,0xdb7d,0xdc48,109184-0xd0d0),(4,0xde4d,0xdf04,109184-0xd0d0),(5,0x9ac0,0x9ae7,0x1200)]
ERRORS={'unsupported':3,'float':4,'budget':6,'heap':8,'stack':9,'divide_zero':11,'native_int0':12,'operand':7,'cancelled':13,'serial':14}
C=r'''
#include <stdio.h>
#include <dos.h>
#include <string.h>
#include "runtime.h"
#include "file_io.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
#include "directory_runtime.h"
#include "when_runtime.h"
#include "set_runtime.h"
#include "find_runtime.h"
#include "script_file_runtime.h"
extern unsigned runtime_receive_pattern_count,runtime_wait_gate,runtime_set_duplex_changed;
extern aspect_file runtime_file;
extern unsigned runtime_string_count,runtime_depth,runtime_stack_pointer,runtime_frame;
extern unsigned char runtime_arena[0x3aca];
extern unsigned runtime_string_pending_near,runtime_string_scratch_pointer,runtime_string_scratch_index;
extern unsigned long runtime_string_pending_far;
static unsigned failures,cases;
static unsigned long checks;
static const char *current;
static unsigned cpu_flags(void);
#pragma aux cpu_flags = "pushf" "pop ax" value [ax] modify exact [ax];
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL %s check=%lu opcode=%u steps=%u\n",current,checks,runtime_last_opcode,runtime_steps);}}
static void run(const char *path,unsigned limit,unsigned error,unsigned has_integer,unsigned integer_value,unsigned has_long,unsigned long long_value,unsigned peak){
 void (__interrupt __far *previous_divide)(void);
 unsigned result,flags_before=cpu_flags();FILE *marker;previous_divide=_dos_getvect(0);current=path;++cases;
 marker=fopen("ACTIVE.TXT","w");if(marker){fprintf(marker,"%s\n",path);fclose(marker);}
 printf("BEGIN %s\n",path);fflush(stdout);result=aspect_runtime_run(path,limit);
 ck(_dos_getvect(0)==previous_divide);
 ck((cpu_flags()&0x600)==(flags_before&0x600));
 ck(runtime_string_pending_far==0 && runtime_string_pending_near==0);
 ck(runtime_string_scratch_pointer==0 && runtime_string_scratch_index==0);
 ck(result==error);ck(runtime_live==0);ck(runtime_find_live==0);ck(runtime_script_file_live==0);ck(runtime_string_count==0);ck(runtime_file.handle==0);
 ck(runtime_depth==0);ck(runtime_stack_pointer==(unsigned)runtime_arena+0x1b1a);
 ck(runtime_frame==runtime_stack_pointer);ck(runtime_abi_bad==0);ck(runtime_peak_live==peak);
 ck(runtime_receive_pattern_count==0);ck(runtime_when_disconnect_armed==0);ck(runtime_wait_gate==0);
 {unsigned slot;for(slot=0;slot<3;++slot)ck(runtime_when_records[84+slot*86]==0 && runtime_when_records[85+slot*86]==0);}
 if(has_integer)ck(runtime_integer_b[0]==integer_value);
 if(has_long)ck(runtime_longs[0]==long_value);
 printf("CASE %s error=%u steps=%u peak=%u cleanup=%u close=%u int0=%u long0=%lu\n",path,result,runtime_steps,runtime_peak_live,runtime_cleanup_count,runtime_close_count,runtime_integer_b[0],runtime_longs[0]);
}
static void output(const char *expected,unsigned count){unsigned i;
 ck(runtime_console_output_size==count);ck(memcmp(runtime_console_output,expected,count)==0);
 printf("OUTPUT %s ",current);for(i=0;i<runtime_console_output_size;++i)printf("%02X",runtime_console_output[i]);printf("\n");
}
static void string_value(unsigned index,const char *expected){unsigned i;
 ck(strcmp((char *)runtime_string_snapshot[index],expected)==0);printf("STRING %s string%u=",current,index);
 for(i=0;i<81 && runtime_string_snapshot[index][i];++i)printf("%02X",runtime_string_snapshot[index][i]);printf("\n");
}
static void numeric_value(unsigned is_long,unsigned index,unsigned long expected){unsigned long value;
 value=is_long?runtime_longs[index]:runtime_integer_b[index];ck(value==expected);
 printf("VALUE %s %s%u=%lu\n",current,is_long?"long":"integer",index,value);
}
static void serial_output(const char *expected,unsigned count){unsigned i;
 ck(runtime_serial_tx_size==count);ck(memcmp(runtime_serial_tx,expected,count)==0);
 printf("TX %s ",current);for(i=0;i<runtime_serial_tx_size;++i)printf("%02X",runtime_serial_tx[i]);printf("\n");
}

/* Fixture metadata stays in a generated DOS data file instead of expanding
 * hundreds of calls into the16-bit near code segment. These are test inputs,
 * not production bytecode/interpreter lookup tables. */
static unsigned fixture_bad;
static unsigned char fixture_input[4096],fixture_trigger[1024],fixture_expected[1024],fixture_directory[114];
static unsigned read_word(FILE *f){unsigned n=0;if(fread(&n,2,1,f)!=1)fixture_bad=1;return n;}
static unsigned long read_long(FILE *f){unsigned long n=0;if(fread(&n,4,1,f)!=1)fixture_bad=1;return n;}
static unsigned read_block(FILE *f,void *p,unsigned n,unsigned capacity){
 if(n>capacity || fread(p,1,n,f)!=n){fixture_bad=1;return 1;}return 0;
}
static unsigned fixture_suite(void){
 FILE *f;unsigned count,i,j,n,limit,error,has_integer,integer,has_long,peak,native_error;
 unsigned mode,in_count,trigger_count,seconds,seconds_step,kind,index,values;
 unsigned long value,initial_ticks,tick_step;char name[32],magic[4];
 f=fopen("CASES.DAT","rb");if(!f)return 1;
 if(read_block(f,magic,4,4)||memcmp(magic,"ACV2",4)){fclose(f);return 1;}
 count=read_word(f);
 for(i=0;i<count&&!fixture_bad;++i){
  n=read_word(f);if(n>=sizeof(name)||read_block(f,name,n,sizeof(name)-1))break;name[n]=0;
  limit=read_word(f);error=read_word(f);has_integer=read_word(f);integer=read_word(f);
  has_long=read_word(f);value=read_long(f);peak=read_word(f);native_error=read_word(f);
  if(read_word(f)){
   in_count=read_word(f);trigger_count=read_word(f);mode=read_word(f);
   initial_ticks=read_long(f);tick_step=read_long(f);seconds=read_word(f);seconds_step=read_word(f);
   if(read_block(f,fixture_input,in_count,sizeof(fixture_input))||read_block(f,fixture_trigger,trigger_count,sizeof(fixture_trigger)))break;
   runtime_receive_fixture(seconds,seconds_step);
   runtime_serial_fixture(fixture_input,in_count,fixture_trigger,trigger_count,mode,initial_ticks,tick_step);
  }else{runtime_serial_fixture_disable();runtime_receive_fixture(0,1);}
  if(read_word(f)){
   n=read_word(f);if(!n||n>200||read_block(f,fixture_directory,114,114)){fixture_bad=1;break;}
   runtime_directory_fixture(n,fixture_directory);
  }else runtime_directory_fixture(0,0);
  if(fixture_bad)break;
  run(name,limit,error,has_integer,integer,has_long,value,peak);
  if(native_error!=65535U){ck(runtime_native_error_code==native_error);printf("NATIVE %s code=%u\n",name,runtime_native_error_code);}
  n=read_word(f);if(read_block(f,fixture_expected,n,sizeof(fixture_expected)))break;output((const char *)fixture_expected,n);
  n=read_word(f);if(read_block(f,fixture_expected,n,sizeof(fixture_expected)))break;serial_output((const char *)fixture_expected,n);
  values=read_word(f);if(values>256){fixture_bad=1;break;}
  for(j=0;j<values&&!fixture_bad;++j){
   kind=read_word(f);index=read_word(f);if(index>=128){fixture_bad=1;break;}
   if(!kind){n=read_word(f);if(n>80||read_block(f,fixture_expected,n,80)){fixture_bad=1;break;}fixture_expected[n]=0;string_value(index,(const char *)fixture_expected);}
   else if(kind==1||kind==2){value=read_long(f);if(!fixture_bad)numeric_value(kind==2,index,value);}
   else fixture_bad=1;
  }
 }
 if(fixture_bad||i!=count||fgetc(f)!=EOF||ferror(f)){fclose(f);return 1;}
 return fclose(f)!=0;
}
int main(void){FILE *done;
 if(fixture_suite())return 2;
'''
END=r'''
 current="invalid API";ck(aspect_runtime_run(0,10)==ASPECT_RUN_STATE);
 ck(aspect_runtime_run("",10)==ASPECT_RUN_STATE);
 ck(aspect_runtime_run("EMPTY.ASX",0)==ASPECT_RUN_STATE);
 done=fopen("DONE.TXT","w");if(!done)return 2;
 fprintf(done,"ASPECT_RUNTIME %u cases %lu checks %u failures\n",cases,checks,failures);fclose(done);
 printf("ASPECT_RUNTIME %u cases %lu checks %u failures\n",cases,checks,failures);return failures?1:0;
}
'''
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 sys.path.insert(0,str(ROOT/'src/aspect'))
 from compiler import compile_source
 OUT.mkdir(parents=True,exist_ok=True);inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 corpus_path=ROOT/'standalone/fixtures/aspect_execution_vectors.json';corpus=json.loads(corpus_path.read_text())
 arithmetic_corpus_path=ROOT/'standalone/fixtures/aspect_arithmetic_vectors.json'
 arithmetic_corpus=json.loads(arithmetic_corpus_path.read_text())
 parameter_corpus_path=ROOT/'standalone/fixtures/aspect_parameter_vectors.json'
 parameter_corpus=json.loads(parameter_corpus_path.read_text())
 parameter_cases=[dict(c,name='PARFLOAT') if c['name']=='FLOAT' else c for c in parameter_corpus['vectors']]
 command_corpus_path=ROOT/'standalone/fixtures/aspect_string_command_vectors.json'
 command_corpus=json.loads(command_corpus_path.read_text())
 conversion_corpus_path=ROOT/'standalone/fixtures/aspect_conversion_vectors.json'
 conversion_corpus=json.loads(conversion_corpus_path.read_text())
 compiler_corpus_path=ROOT/'standalone/fixtures/aspect_compiler_validation_vectors.json'
 compiler_corpus=json.loads(compiler_corpus_path.read_text())
 console_corpus_path=ROOT/'standalone/fixtures/aspect_console_vectors.json'
 console_corpus=json.loads(console_corpus_path.read_text())
 serial_corpus_path=ROOT/'standalone/fixtures/aspect_serial_vectors.json'
 serial_corpus=json.loads(serial_corpus_path.read_text())
 receive_corpus_path=ROOT/'standalone/fixtures/aspect_receive_vectors.json'
 receive_corpus=json.loads(receive_corpus_path.read_text())
 receive_overrides_path=ROOT/'standalone/fixtures/aspect_receive_runtime_overrides.json'
 receive_overrides=json.loads(receive_overrides_path.read_text())
 assert receive_overrides['component_fixture']==str(receive_corpus_path.relative_to(ROOT))
 assert receive_overrides['component_fixture_sha256']==sha(receive_corpus_path)
 receive_cases=[]
 for case in receive_corpus['vectors']:
  override=receive_overrides['overrides'].get(case['name'])
  if override:
   assert case['expected']==override['component_expected'],case['name']
   case=dict(case,expected=override['expected'],serial={**case['serial'],**override['serial']})
  receive_cases.append(case)
 assert set(receive_overrides['overrides'])<={case['name'] for case in receive_cases}
 directory_corpus_path=ROOT/'standalone/fixtures/aspect_directory_vectors.json'
 directory_corpus=json.loads(directory_corpus_path.read_text())
 when_corpus_path=ROOT/'standalone/fixtures/aspect_when_runtime_vectors.json'
 when_corpus=json.loads(when_corpus_path.read_text())
 set_corpus_path=ROOT/'standalone/fixtures/aspect_set_runtime_vectors.json'
 set_corpus=json.loads(set_corpus_path.read_text())
 find_corpus_path=ROOT/'standalone/fixtures/aspect_find_case_runtime_vectors.json'
 find_corpus=json.loads(find_corpus_path.read_text())
 break_corpus_path=ROOT/'standalone/fixtures/aspect_break_runtime_vectors.json'
 break_corpus=json.loads(break_corpus_path.read_text())
 cases=corpus['vectors']+arithmetic_corpus['vectors']+parameter_cases+command_corpus['vectors']+conversion_corpus['vectors']+compiler_corpus['vectors']+console_corpus['vectors']+serial_corpus['vectors']+receive_cases+directory_corpus['vectors']+when_corpus['vectors']+find_corpus['vectors']+break_corpus['vectors']
 # Historical PAUSE oracle expected an unsupported stop before opcode88 recovery.
 # Its authored seven-second script now executes the recovered native delay.
 cases=[dict(c,expected={}) if c['name']=='PAUSE' else c for c in cases]
 assert len({c['name'] for c in cases})==len(cases)
 sources=[Path(__file__).resolve(),corpus_path,arithmetic_corpus_path,parameter_corpus_path,command_corpus_path,ROOT/'reconstruction/uart/encodings.inc',ROOT/'src/aspect/runtime.c',ROOT/'src/aspect/runtime.h',ROOT/'src/aspect/script_file_runtime.c',ROOT/'src/aspect/script_file_runtime.h',ROOT/'src/aspect/file_io.c',ROOT/'src/aspect/file_io.h',ROOT/'src/aspect/script_path.c',ROOT/'src/aspect/script_path.h']
 objects=[];units=[]
 sources.append(conversion_corpus_path)
 sources.append(compiler_corpus_path)
 sources.append(ROOT/'src/aspect/compiler.py')
 sources.append(console_corpus_path)
 sources += [ROOT/'reconstruction/translation/receive.asm',receive_corpus_path,serial_corpus_path,ROOT/'src/aspect/serial_runtime.c',ROOT/'src/aspect/serial_runtime.h',ROOT/'src/aspect/receive_runtime.c',ROOT/'src/aspect/receive_runtime.h']
 sources += [directory_corpus_path,ROOT/'src/aspect/directory_runtime.c',ROOT/'src/aspect/directory_runtime.h']
 sources += [ROOT/'src/aspect/set_runtime.c',ROOT/'src/aspect/set_runtime.h',ROOT/'src/aspect/find_runtime.c',ROOT/'src/aspect/find_runtime.h']
 sources.append(set_corpus_path)
 sources.append(find_corpus_path)
 sources.append(break_corpus_path)
 sources += [when_corpus_path,receive_overrides_path,ROOT/'src/aspect/when_runtime.c',ROOT/'src/aspect/when_runtime.h',ROOT/'src/keyboard/api.h']
 for name,rel,define in ASM:
  p=ROOT/rel;obj=OUT/(name+'.obj');sources.append(p)
  subprocess.run(['nasm','-f','obj',inc]+(['-D'+define] if define else [])+[str(p),'-o',str(obj)],check=True);objects.append(str(obj))
 for unit,start,end,base in SUPPORT:
  p=OUT/f'support{unit}.bin'
  subprocess.run(['nasm','-f','bin',inc,'-DASPECT_EXPR_FLAT',f'-DASPECT_EXPR_UNIT={unit}',str(ROOT/'src/aspect/expression_support.asm'),'-o',str(p)],check=True)
  assert p.stat().st_size==end-start
  units.append(dict(unit=unit,start=start,end_exclusive=end,file_start=base+start,bytes=end-start,sha256=sha(p)))
 near_admission=' runtime_find_fail_after=65535U;\n'
 near_observe=''
 for case in find_corpus['vectors']:
  path=case['name']+'.ASX';ex=case['expected']
  if 'near_fail_after' in case:
   near_admission+=f' if(!strcmp(path,"{path}"))runtime_find_fail_after={case["near_fail_after"]};\n'
  near_observe+=f' if(!strcmp(path,"{path}")){{ck(runtime_find_peak=={ex["near_peak"]});ck(runtime_find_alloc_calls=={ex["near_calls"]});}}\n'
 program=C.replace('result=aspect_runtime_run(path,limit);',near_admission+'result=aspect_runtime_run(path,limit);')
 program=program.replace(' ck(result==error);',near_observe+' ck(result==error);')
 supported={int(op,16):name for op,name in re.findall(r'%(?:el)?if op=(0x[0-9a-f]+)\n dw (\w+)',(ROOT/'src/aspect/runtime_bridge.asm').read_text())}
 assert len(supported)==89
 # ACV2 adds explicit owned-directory metadata to ACV1's diagnostic inputs.
 table=bytearray(b'ACV2'+struct.pack('<H',len(cases)))
 def block(data):
  assert len(data)<=65535
  return struct.pack('<H',len(data))+data
 for case in cases:
  source=case['source'];assert hashlib.sha256(source.encode('cp437')).hexdigest()==case['source_sha256']
  data=compile_source(source)
  assert data==bytes.fromhex(case['hex']) and hashlib.sha256(data).hexdigest()==case['asx_sha256'],case['name']
  name=case['name']+'.ASX';assert len(name)<32
  (OUT/name).write_bytes(data);ex=case['expected'];error=ERRORS[ex['error']] if 'error' in ex else 0
  assert not case.get('dos_excluded',False),case['name']
  table+=block(name.encode('ascii'))
  table+=struct.pack('<HHHHHIHH',ex.get('limit',1000),error,int('integer0' in ex),ex.get('integer0',0)&65535,int('long0' in ex),ex.get('long0',0)&0xffffffff,ex.get('allocated',data[0]),ex.get('native_error',65535))
  serial=case.get('serial');table+=struct.pack('<H',bool(serial))
  if serial:
   incoming=bytes.fromhex(serial.get('input_hex',''));trigger=bytes.fromhex(serial.get('send_after_tx_hex',''))
   assert len(incoming)<=4096 and len(trigger)<=1024
   flags=(int(serial.get('enabled',True)) | (2 if serial.get('case_sensitive') else 0)
          | (4 if serial.get('carrier_present') else 0) | (8 if serial.get('carrier_drop_after_input') else 0))
   table+=struct.pack('<HHHIIHH',len(incoming),len(trigger),flags,serial.get('initial_ticks',0),serial.get('tick_step',1),serial.get('initial_seconds',0),serial.get('seconds_step',1))+incoming+trigger
  directory=case.get('directory');table+=struct.pack('<H',bool(directory))
  if directory:
   record=bytes.fromhex(directory['record_hex']);assert len(record)==114 and 1<=directory['entry']<=200
   table+=struct.pack('<H',directory['entry'])+record
  output=bytes.fromhex(ex.get('stdout_hex',''));tx=bytes.fromhex(ex.get('tx_hex',''));assert len(output)<=1024 and len(tx)<=1024
  table+=block(output)+block(tx)
  values=[]
  for key,value in ex.items():
   if re.fullmatch(r'string[0-9]+',key):
    index=int(key[6:]);assert 0<=index<128
    text=value.encode('cp437');assert len(text)<=80 and b'\0' not in text
    values.append(struct.pack('<HH',0,index)+block(text))
   match=re.fullmatch(r'(integer|long)([0-9]+)',key)
   if match:
    kind,index=match[1],int(match[2]);assert 0<=index<128
    values.append(struct.pack('<HHI',1 if kind=='integer' else 2,index,value&0xffffffff))
  table+=struct.pack('<H',len(values))+b''.join(values)
 (OUT/'CASES.DAT').write_bytes(table)
 program+=' runtime_serial_fixture_disable();runtime_directory_fixture(0,0);\n'
 program+=' run("DIRNUM.ASX",1000,0,1,0,0,0UL,0);numeric_value(0,0,0UL);\n'
 program+=' run("DIR6.ASX",1000,0,0,0,0,0UL,1);string_value(0,"");\n'
 baud=directory_corpus['compiler_only'][0];baud_data=compile_source(baud['source'])
 assert baud_data==bytes.fromhex(baud['hex']) and hashlib.sha256(baud_data).hexdigest()==baud['asx_sha256']
 (OUT/'DIRBAUD.ASX').write_bytes(baud_data)
 program+=' run("DIRBAUD.ASX",1000,3,0,0,0,0UL,0);\n'
 # Malformed fixtures stop at header/read/unsupported boundaries, not arbitrary unsafe operands.
 for name,data,error in [('NOHEADER',b'',2),('BADHEAD',bytes.fromhex('81 cf 94'),2),('BADOP',bytes.fromhex('00 ff'),3),('TRUNC',bytes.fromhex('00 cf 5b 00 8d 00 ab 07'),5)]:
  (OUT/(name+'.ASX')).write_bytes(data);program+=f' run("{name}.ASX",1000,{error},0,0,0,0UL,0);\n'
 (OUT/'MISSING.ASX').unlink(missing_ok=True);program+=' run("MISSING.ASX",1000,1,0,0,0,0UL,0);\n'
 # Native SET dispatch uses a complete owned table; unimplemented selectors
 # remain typed failures. GET is a separate interactive-input instruction.
 set_supported={0x22:'FGETS_CRLF',0x09:'BREAK',0x12:'DISPLAY',0x18:'DUPLEX',0x23:'FINDCASE',0x29:'KEYS',0x2e:'MSG_CRLF',0x30:'PAUSECHAR',0x3b:'RXDATA',0x44:'SWITCHCASE',0x4c:'TXPACE',0x55:'WAITCASE',0x56:'WHENCASE'}
 for sub in range(256):
  if sub not in set_supported:(OUT/f'S{sub:02X}.ASX').write_bytes(bytes([0,0x9e,sub]))
 condition=' && '.join(f'sub!={sub}' for sub in set_supported)
 program+=' {unsigned sub;char path[12];for(sub=0;sub<256;++sub)if('+condition+'){sprintf(path,"S%02X.ASX",sub);run(path,1000,3,0,0,0,0UL,0);}}\n'
 # Native FETCH shares the same complete table but has no status tail.
 for sub in range(256):
  if sub not in set_supported:(OUT/f'Q{sub:02X}.ASX').write_bytes(bytes([0,0x37,sub]))
 program+=' {unsigned sub;char path[12];for(sub=0;sub<256;++sub)if('+condition+'){sprintf(path,"Q%02X.ASX",sub);run(path,1000,3,0,0,0,0UL,0);ck(runtime_set_refresh_count==0);}}\n'
 for case in break_corpus['raw_getters']:
  assert hashlib.sha256(case['source'].encode('cp437')).hexdigest()==case['source_sha256']
  assert compile_source(case['source'])==bytes.fromhex(case['hex'])
  (OUT/(case['name']+'.ASX')).write_bytes(bytes.fromhex(case['hex']))
  program+=f' run("{case["name"]}.ASX",1000,0,1,{case["expected"]},0,0UL,0);ck(runtime_set_refresh_count==0);ck(runtime_set_duplex_changed==0);\n'
 for name,wire in [('QTRUNC',bytes([0,0x37])),('QDEST',bytes([0,0x37,9]))]:
  (OUT/(name+'.ASX')).write_bytes(wire)
  program+=f' run("{name}.ASX",1000,5,0,0,0,0UL,0);ck(runtime_set_refresh_count==0);\n'
 for name,wire,error in [('SETTRUNC',bytes([0,0x9e]),5),('SETVALTR',bytes([0,0x9e,0x56]),5),
                         ('SETBOOL2',bytes([0,0xcf,0x9e,0x56,2,0xd0,0x94]),0),('SETBOOLF',bytes([0,0xcf,0x9e,0x56,255,0xd0,0x94]),0)]:
  (OUT/(name+'.ASX')).write_bytes(wire)
  program+=f' run("{name}.ASX",1000,{error},0,0,0,0UL,0);\n'
  if name in ('SETBOOL2','SETBOOLF'):
   program+=f' ck(runtime_set_refresh_count==1);ck(runtime_set_observed[10]=={wire[4]});\n'
 for case in set_corpus['vectors']:
  source=case['source'];wire=compile_source(source)
  assert hashlib.sha256(source.encode('cp437')).hexdigest()==case['source_sha256']
  assert wire==bytes.fromhex(case['hex']) and hashlib.sha256(wire).hexdigest()==case['asx_sha256']
  name=case['name']+'.ASX';assert len(case['name'])<=8
  (OUT/name).write_bytes(wire);expected=case['expected']
  if case.get('serial'):
   serial=case['serial'];incoming=bytes.fromhex(serial.get('input_hex',''));trigger=bytes.fromhex(serial.get('send_after_tx_hex',''))
   literal=lambda data: '"'+''.join('\\x'+f'{byte:02x}' for byte in data)+'"'
   program+=f' runtime_serial_fixture((const unsigned char *){literal(incoming)},{len(incoming)},(const unsigned char *){literal(trigger)},{len(trigger)},1,0,1);\n'
  else:
   program+=' runtime_serial_fixture_disable();\n'
  program+=f' run("{name}",1000,{expected["error"]},0,0,0,0UL,0);\n'
  program+=f' ck(runtime_set_refresh_count=={expected["refreshes"]});\n'
  if 'setting_index' in expected:
   program+=f' ck(runtime_set_observed[{expected["setting_index"]}]=={expected["setting_value"]});\n'
  if 'native_error' in expected:
   program+=f' ck(runtime_native_error_code=={expected["native_error"]});\n'
  output=bytes.fromhex(expected['stdout_hex'])
  literal=''.join('\\x'+f'{byte:02x}' for byte in output)
  program+=f' output("{literal}",{len(output)});\n'
  if 'tx_hex' in expected:
   tx=bytes.fromhex(expected['tx_hex']);literal=''.join('\\x'+f'{byte:02x}' for byte in tx)
   program+=f' serial_output("{literal}",{len(tx)});\n'
  if 'paced_units' in expected:
   program+=f' ck(runtime_serial_paced_units=={expected["paced_units"]}UL);ck(runtime_serial_paced_calls=={expected["paced_calls"]});\n'
 program+=' runtime_serial_fixture_disable();\n'
 program+=' runtime_fail_after=0;run("STRINGS.ASX",1000,8,0,0,0,0UL,0);\n'
 program+=' runtime_fail_after=1;run("STRINGS.ASX",1000,8,0,0,0,0UL,1);\n'
 program+=' runtime_fail_after=0xffff;run("STRINGS.ASX",1000,0,0,0,0,0UL,2);\n'
 # Maintained ownership-fault fixtures: only the declared string-count header
 # changes; arithmetic bytes remain the corresponding compiler-authored fixture.
 for name,template,error in [('HEAPFLT','IDIVEDGE',12),('HEAPZERO','IDZ',11)]:
  wire=bytearray(bytes.fromhex(next(c['hex'] for c in cases if c['name']==template)))
  assert wire[0]==0;wire[0]=2;(OUT/(name+'.ASX')).write_bytes(wire)
  program+=f' run("{name}.ASX",1000,{error},0,0,0,0UL,2);\n'
 # Truncate the final assignment option/return after the first global was set.
 wire=bytes.fromhex(next(c['hex'] for c in cases if c['name']=='STRGASS'))
 assert wire[0]==2 and wire[-2:]==bytes([0,0x94])
 (OUT/'STRSHORT.ASX').write_bytes(wire[:-2])
 program+=' run("STRSHORT.ASX",1000,5,0,0,0,0UL,2);\n'
 program+=' ck(strcmp((char *)runtime_string_snapshot[0],"HELLO")==0);ck(runtime_string_snapshot[1][0]==0);\n'
 program+=' run("ASSIGN.ASX",1000,0,1,7,0,0UL,0);\n'+END
 # Every unimplemented in-range slot must abort, never silently consume bytes.
 unsupported=[op for op in range(215) if op not in supported]
 extra=''
 for op in unsupported:
  name=f'U{op:03X}.ASX';(OUT/name).write_bytes(bytes([0,op]))
  extra+=f' run("{name}",1000,3,0,0,0,0UL,0);ck(runtime_last_opcode=={op});\n'
 program=program.replace(END,extra+END)
 (OUT/'diagnostic.c').write_text(program)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC',
 '-i='+str(ROOT/'src/aspect'),'-fm=EXECUTE.map','-fe=EXECUTE.EXE',str(OUT/'diagnostic.c'),str(ROOT/'src/aspect/runtime.c'),str(ROOT/'src/aspect/script_file_runtime.c'),str(ROOT/'src/aspect/file_io.c'),str(ROOT/'src/aspect/script_path.c'),str(ROOT/'src/aspect/serial_runtime.c'),str(ROOT/'src/aspect/receive_runtime.c'),str(ROOT/'src/aspect/directory_runtime.c'),str(ROOT/'src/aspect/when_runtime.c'),str(ROOT/'src/aspect/set_runtime.c'),str(ROOT/'src/aspect/find_runtime.c'),*objects],cwd=OUT,check=True)
 report=dict(binary_sha256=sha(OUT/'EXECUTE.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},support_units=units,original_inputs=[],
  compile_flags=['8086','small model','cdecl','ASPECT_RUNTIME_DIAGNOSTIC'],fixture_count=len(cases),
  supported_slots={f'{op:02x}':supported[op] for op in sorted(supported)},unsupported_slot_cases=len(unsupported),diagnostic_case_count=len(cases)+15+len(unsupported)+(256-len(set_supported))+4+len(set_corpus['vectors'])+(256-len(set_supported))+len(break_corpus['raw_getters'])+2,
  SET_family=dict(supported_subcommands={f'{key:02x}':value for key,value in set_supported.items()},unsupported_subcommands_tested=256-len(set_supported),truncated_cases=2,raw_boolean_cases=2,integration_vectors=len(set_corpus['vectors'])),
  BREAK_family=dict(integration_vectors=len(break_corpus['vectors']),raw_fetch_getters=len(break_corpus['raw_getters']),unsupported_fetch_selectors_tested=256-len(set_supported),fetch_truncations=2,diagnostic_timing='Transport readiness only; actual UART pulses covered by separate product DOS tests.'),
  FIND_CASE_family=dict(integration_vectors=len(find_corpus['vectors']),near_failure_cases=sum('near_fail_after' in c for c in find_corpus['vectors']),native_bytes=401,scope='Actual native FIND/SWITCH/CASE with owned near allocations and typed failure before native NULL dereference. FOUND and SWITCH snapshots are shared state; per-invocation SET sensitivity resets separately.'),
  fixture_data={'file':'CASES.DAT','schema':'ACV2','sha256':sha(OUT/'CASES.DAT'),'bytes':len(table),'cases':len(cases)},
  parameter_fixture_aliases={'PARFLOAT':'FLOAT'},
  composed_receive_overrides=receive_overrides,
  maintained_string_fault_fixture={'STRSHORT':'STRGASS compiler bytes with final00 option and94 return removed; first global HELLO retained, second stays empty'},
  maintained_heap_fault_fixtures={'HEAPFLT':'IDIVEDGE compiler bytes with global-string count changed from0to2','HEAPZERO':'IDZ compiler bytes with global-string count changed from0to2'},
  fixture_expectations={c['name']:{'source_sha256':c['source_sha256'],'asx_sha256':c['asx_sha256'],'expected':c['expected']} for c in cases},
  scope='Incremental actual native dispatch/operand/operation/file/heap/WHEN/SET/FIND/CASE composition executing source-owned compiled fixtures. Incomplete89-slot opcode table; thirteen native SET setters and FETCH queries and shared FIND/CASE consumers. Serial queue/clock/carrier inputs and status-tail snapshots are explicit diagnostic models. Not full ASPECT or arbitrary-input safety.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
