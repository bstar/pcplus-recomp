#!/usr/bin/env python3
"""Source-only incremental native ASPECT execution/ownership diagnostic."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-runtime'
ASM=[('dispatch','src/aspect/dispatch.asm',None),('abort','src/aspect/abort.asm',None),
 ('globals','src/aspect/global_strings.asm',None),('stack','src/aspect/value_stack.asm',None),
 ('flow','src/aspect/control_flow.asm',None),('parameters','src/aspect/parameters.asm',None),('strings','src/aspect/string_operands.asm',None),('string_commands','src/aspect/string_commands.asm',None),('string_services','src/aspect/string_services.asm',None),
 ('string_strlen','reconstruction/program_exec/strlen.asm','PROGRAM_EXEC_OMF'),('string_strncmp','reconstruction/program_exec/strncmp.asm','PROGRAM_EXEC_OMF'),
 ('string_concat','reconstruction/directory_dial/append.asm','DIRECTORY_DIAL_OMF'),('string_upper','reconstruction/directory_dial/uppercase.asm','DIRECTORY_DIAL_OMF'),('operands','src/aspect/numeric_operands.asm',None),
 ('operations','src/aspect/numeric_operations.asm',None),
 ('arithmetic','src/aspect/arithmetic.asm',None),('long','src/aspect/long_arithmetic.asm',None),('support','src/aspect/expression_support.asm',None),
 ('copy','reconstruction/erase/move_bytes.asm','ERASE_OMF'),
 ('setjmp','reconstruction/transfer_session/setjmp.asm','TRANSFER_SESSION_OMF'),
 ('longjmp','reconstruction/transfer_session/longjmp.asm','TRANSFER_SESSION_OMF'),
 ('bridge','src/aspect/runtime_bridge.asm',None)]
SUPPORT=[(1,0xd2a0,0xd2d6,109184-0xd0d0),(2,0xd3f2,0xd408,109184-0xd0d0),
 (3,0xdb7d,0xdc48,109184-0xd0d0),(4,0xde4d,0xdf04,109184-0xd0d0),(5,0x9ac0,0x9ae7,0x1200)]
ERRORS={'unsupported':3,'float':4,'budget':6,'stack':9,'divide_zero':11,'native_int0':12,'operand':7}
C=r'''
#include <stdio.h>
#include <dos.h>
#include <string.h>
#include "runtime.h"
#include "file_io.h"
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
 unsigned result,flags_before=cpu_flags();previous_divide=_dos_getvect(0);current=path;++cases;result=aspect_runtime_run(path,limit);
 ck(_dos_getvect(0)==previous_divide);
 ck((cpu_flags()&0x600)==(flags_before&0x600));
 ck(runtime_string_pending_far==0 && runtime_string_pending_near==0);
 ck(runtime_string_scratch_pointer==0 && runtime_string_scratch_index==0);
 ck(result==error);ck(runtime_live==0);ck(runtime_string_count==0);ck(runtime_file.handle==0);
 ck(runtime_depth==0);ck(runtime_stack_pointer==(unsigned)runtime_arena+0x1b1a);
 ck(runtime_frame==runtime_stack_pointer);ck(runtime_abi_bad==0);ck(runtime_peak_live==peak);
 if(has_integer)ck(runtime_integer_b[0]==integer_value);
 if(has_long)ck(runtime_longs[0]==long_value);
 printf("CASE %s error=%u steps=%u peak=%u cleanup=%u close=%u int0=%u long0=%lu\n",path,result,runtime_steps,runtime_peak_live,runtime_cleanup_count,runtime_close_count,runtime_integer_b[0],runtime_longs[0]);
}
int main(void){FILE *done;
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
 OUT.mkdir(parents=True,exist_ok=True);inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 corpus_path=ROOT/'standalone/fixtures/aspect_execution_vectors.json';corpus=json.loads(corpus_path.read_text())
 arithmetic_corpus_path=ROOT/'standalone/fixtures/aspect_arithmetic_vectors.json'
 arithmetic_corpus=json.loads(arithmetic_corpus_path.read_text())
 parameter_corpus_path=ROOT/'standalone/fixtures/aspect_parameter_vectors.json'
 parameter_corpus=json.loads(parameter_corpus_path.read_text())
 parameter_cases=[dict(c,name='PARFLOAT') if c['name']=='FLOAT' else c for c in parameter_corpus['vectors']]
 command_corpus_path=ROOT/'standalone/fixtures/aspect_string_command_vectors.json'
 command_corpus=json.loads(command_corpus_path.read_text())
 cases=corpus['vectors']+arithmetic_corpus['vectors']+parameter_cases+command_corpus['vectors']
 assert len({c['name'] for c in cases})==len(cases)
 sources=[Path(__file__).resolve(),corpus_path,arithmetic_corpus_path,parameter_corpus_path,command_corpus_path,ROOT/'reconstruction/uart/encodings.inc',ROOT/'src/aspect/runtime.c',ROOT/'src/aspect/runtime.h',ROOT/'src/aspect/file_io.c',ROOT/'src/aspect/file_io.h']
 objects=[];units=[]
 for name,rel,define in ASM:
  p=ROOT/rel;obj=OUT/(name+'.obj');sources.append(p)
  subprocess.run(['nasm','-f','obj',inc]+(['-D'+define] if define else [])+[str(p),'-o',str(obj)],check=True);objects.append(str(obj))
 for unit,start,end,base in SUPPORT:
  p=OUT/f'support{unit}.bin'
  subprocess.run(['nasm','-f','bin',inc,'-DASPECT_EXPR_FLAT',f'-DASPECT_EXPR_UNIT={unit}',str(ROOT/'src/aspect/expression_support.asm'),'-o',str(p)],check=True)
  assert p.stat().st_size==end-start
  units.append(dict(unit=unit,start=start,end_exclusive=end,file_start=base+start,bytes=end-start,sha256=sha(p)))
 program=C
 supported={int(op,16):name for op,name in re.findall(r'%(?:el)?if op=(0x[0-9a-f]+)\n dw (\w+)',(ROOT/'src/aspect/runtime_bridge.asm').read_text())}
 assert len(supported)==50
 for case in cases:
  data=bytes.fromhex(case['hex']);assert hashlib.sha256(data).hexdigest()==case['asx_sha256']
  name=case['name']+'.ASX';(OUT/name).write_bytes(data);ex=case['expected'];error=ERRORS[ex['error']] if 'error' in ex else 0
  assert not case.get('dos_excluded',False),case['name']
  program+=f' run("{name}",{ex.get("limit",1000)},{error},{int("integer0" in ex)},{ex.get("integer0",0)&65535}U,{int("long0" in ex)},{ex.get("long0",0)}UL,{ex.get("allocated",data[0])});\n'
  if 'native_error' in ex:program+=f' ck(runtime_native_error_code=={ex["native_error"]});printf("NATIVE {name} code=%u\\n",runtime_native_error_code);\n'
  for key,value in ex.items():
   if re.fullmatch(r'string[0-9]+',key):
    index=int(key[6:]);assert 0<=index<128
    text=value.encode('cp437');assert len(text)<=80 and b'\0' not in text
    literal=''.join(f'\\{b:03o}' for b in text)
    program+=f' ck(strcmp((char *)runtime_string_snapshot[{index}],"{literal}")==0);printf("STRING {name} {key}=");{{unsigned i;for(i=0;i<81 && runtime_string_snapshot[{index}][i];++i)printf("%02X",runtime_string_snapshot[{index}][i]);printf("\\n");}}\n'
   match=re.fullmatch(r'(integer|long)([0-9]+)',key)
   if match:
    kind,index=match[1],int(match[2]);assert 0<=index<128
    bank='runtime_integer_b' if kind=='integer' else 'runtime_longs'
    suffix='U' if kind=='integer' else 'UL'
    program+=f' ck({bank}[{index}]=={value}{suffix});printf("VALUE {name} {key}=%lu\\n",(unsigned long){bank}[{index}]);\n'

 # Malformed fixtures stop at header/read/unsupported boundaries, not arbitrary unsafe operands.
 for name,data,error in [('NOHEADER',b'',2),('BADHEAD',bytes.fromhex('81 cf 94'),2),('BADOP',bytes.fromhex('00 ff'),3),('TRUNC',bytes.fromhex('00 cf 5b 00 8d 00 ab 07'),5)]:
  (OUT/(name+'.ASX')).write_bytes(data);program+=f' run("{name}.ASX",1000,{error},0,0,0,0UL,0);\n'
 (OUT/'MISSING.ASX').unlink(missing_ok=True);program+=' run("MISSING.ASX",1000,1,0,0,0,0UL,0);\n'
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
 '-i='+str(ROOT/'src/aspect'),'-fm=EXECUTE.map','-fe=EXECUTE.EXE',str(OUT/'diagnostic.c'),str(ROOT/'src/aspect/runtime.c'),str(ROOT/'src/aspect/file_io.c'),*objects],cwd=OUT,check=True)
 report=dict(binary_sha256=sha(OUT/'EXECUTE.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},support_units=units,original_inputs=[],
  compile_flags=['8086','small model','cdecl','ASPECT_RUNTIME_DIAGNOSTIC'],fixture_count=len(cases),
  supported_slots={f'{op:02x}':supported[op] for op in sorted(supported)},unsupported_slot_cases=len(unsupported),diagnostic_case_count=len(cases)+12+len(unsupported),
  parameter_fixture_aliases={'PARFLOAT':'FLOAT'},
  maintained_string_fault_fixture={'STRSHORT':'STRGASS compiler bytes with final00 option and94 return removed; first global HELLO retained, second stays empty'},
  maintained_heap_fault_fixtures={'HEAPFLT':'IDIVEDGE compiler bytes with global-string count changed from0to2','HEAPZERO':'IDZ compiler bytes with global-string count changed from0to2'},
  fixture_expectations={c['name']:{'source_sha256':c['source_sha256'],'asx_sha256':c['asx_sha256'],'expected':c['expected']} for c in cases},
  scope='Incremental actual native dispatch/operand/operation/file/heap composition executing source-owned compiled fixtures. Incomplete50-slot opcode table; unavailable services abort. Not full ASPECT or arbitrary-input safety.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
