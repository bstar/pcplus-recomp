#!/usr/bin/env python3
"""Run compiled authored ASX through incremental recovered DOS dispatch."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from build_aspect_runtime import ROOT,OUT,sha
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
EXPECTED=['f44d1381879db32a3471ab7605c49a6d97b25395422c5a8604b45d9337216833',
 '2f3c68286f7445c3c1d401d1ed410239e9719f11687def70d37378e38cf93bb5',
 'ec40b46f8c508b585b8ef7eeb7f2398e5c081567fe83495721b87cd6e0ae9809',
 'b235ad26e9d5106fe3390f615c52f2868f44fb5ec54cad3352249a4285be8298',
 '13198f32453ef810aad7bdde574976081e28a8037b04581ede30be457a30cc10']

def metadata_records(path):
 """Independently walk ACV2, including variable-size serial/output fields."""
 data=path.read_bytes();position=0
 def take(size):
  nonlocal position
  assert size>=0 and position+size<=len(data),'truncated ACV2 record'
  result=data[position:position+size];position+=size;return result
 def word():return int.from_bytes(take(2),'little')
 def block():return take(word())
 assert take(4)==b'ACV2'
 records=[]
 for _ in range(word()):
  name=block().decode('ascii');assert name.endswith('.ASX') and len(name)<32
  header=struct.unpack('<HHHHHIHH',take(18))
  serial=word();assert serial in (0,1)
  if serial:
   count,trigger,mode,ticks,step,seconds,second_step=struct.unpack('<HHHIIHH',take(18))
   assert count<=4096 and trigger<=1024
   take(count);take(trigger)
  directory=word();assert directory in (0,1)
  entry,record=(word(),take(114)) if directory else (0,None)
  stdout,tx=block(),block();values={}
  for _ in range(word()):
   kind,index=word(),word();assert index<128 and kind in (0,1,2)
   if kind==0:
    value=block();assert len(value)<=80
    values['string'+str(index)]=value
   else:values[('integer' if kind==1 else 'long')+str(index)]=int.from_bytes(take(4),'little')
  records.append(dict(name=name,error=header[1],entry=entry,record=record,stdout=stdout,tx=tx,values=values))
 assert position==len(data),'unexpected ACV2 trailing bytes'
 assert len({record['name'] for record in records})==len(records)
 return records

def check_directory_metadata(records,output):
 """Bind authored metadata, ACV2 payload and actual DOS observations separately."""
 fixture=ROOT/'standalone/fixtures/aspect_directory_vectors.json'
 vectors=json.loads(fixture.read_text())['vectors'];assert len(vectors)==18
 indexed={record['name']:record for record in records};checks=0
 lines=output.splitlines()
 assert sum(record['record'] is not None for record in records)==len(vectors)
 for vector in vectors:
  name=vector['name']+'.ASX';record=indexed[name];expected=vector['expected']
  assert record['entry']==vector['directory']['entry'] and record['record']==bytes.fromhex(vector['directory']['record_hex']);checks+=1
  assert record['error']==0;checks+=1
  assert any(line.startswith('CASE '+name+' error=0 ') for line in lines);checks+=1
  for label,key in [('OUTPUT','stdout_hex'),('TX','tx_hex')]:
   value=bytes.fromhex(expected.get(key,''));assert record['stdout' if label=='OUTPUT' else 'tx']==value
   assert label+' '+name+' '+value.hex().upper() in lines;checks+=2
  for key,value in expected.items():
   if key.startswith('string'):
    encoded=value.encode('cp437');assert record['values'][key]==encoded
    assert 'STRING '+name+' '+key+'='+encoded.hex().upper() in lines;checks+=2
   elif key.startswith(('integer','long')):
    assert record['values'][key]==(value&0xffffffff)
    assert 'VALUE '+name+' '+key+'='+str(value&0xffffffff) in lines;checks+=2
 assert 'VALUE DIRNUM.ASX integer0=0' in lines
 assert 'STRING DIR6.ASX string0=' in lines
 assert any(line.startswith('CASE DIRBAUD.ASX error=3 ') for line in lines)
 baud=next(v for v in json.loads(fixture.read_text())['compiler_only'] if v['name']=='DIRBAUD')
 assert sha(OUT/'DIRBAUD.ASX')==baud['asx_sha256'];checks+=4
 return dict(cases=len(vectors),default_noentry_cases=2,unsupported_baud_cases=1,
             host_binding_checks=checks,fixture_sha256=sha(fixture),
             scope='Independent ACV2 parse, exact authored114B/entry binding, and actualDOS output/tx/value lines. No private original input.')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path);args=p.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_runtime.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());optional=None
 assert manifest['fixture_data']['file']=='CASES.DAT' and sha(OUT/'CASES.DAT')==manifest['fixture_data']['sha256']
 assert manifest['fixture_data']['schema']=='ACV2'
 assert manifest['fixture_data']['cases']==manifest['fixture_count']
 records=metadata_records(OUT/'CASES.DAT');assert len(records)==manifest['fixture_count']
 if args.original:
  assert sha(args.original)==ORIGINAL;original=args.original.read_bytes()
 for unit,digest in zip(manifest['support_units'],EXPECTED):
  path=OUT/f'support{unit["unit"]}.bin';assert sha(path)==unit['sha256']==digest
  if args.original:assert original[unit['file_start']:unit['file_start']+unit['bytes']]==path.read_bytes()
 if args.original:
  # Original string builtin19 routes via thunkC2C7 to overlay16 DAFB,
  # which returns a pointer to NUL. The owner supplies its own empty string.
  import struct
  assert struct.unpack_from('<H',original,0x25950+0x4cf8+19*2)[0]==0xc2c7
  assert original[109184-0xd0d0+0xdafb:109184-0xd0d0+0xdaff]==bytes.fromhex('b8 42 49 c3')
  assert original[0x25950+0x4942]==0
  assert struct.unpack_from('<H',original,0x25950+0x4cb6+21*2)[0]==0xcc6f
  assert struct.unpack_from('<H',original,0x25950+0x4cb6+27*2)[0]==0xbc97
  directory_thunks=[0xbdb7,0xbe0b,0xbe2f,0xbe77,0xbebf,0xbf1f,0xbf67,0xbfbb]
  assert list(struct.unpack_from('<8H',original,0x25950+0x4cf8))==directory_thunks
  assert struct.unpack_from('<H',original,0x25950+0x4cb6+3*2)[0]==0xc6db
  original_directory=b''.join(bytes([0xb8])+pointer.to_bytes(2,'little')+b'\xc3'
                             for pointer in [0xe68d,0xe6af,0xe6a6,0xe650,0xe6b9,0xe669,0xe69b,0xe684])
  assert original[109184-0xd0d0+0xdaa2:109184-0xd0d0+0xdac2]==original_directory
  assert original[109184-0xd0d0+0xd9b5:109184-0xd0d0+0xd9b9]==bytes.fromhex('a1 82 e4 c3')
  # Scanner consumes only decimal-digit bit04, not the other CRT flags.
  assert original[0x25950+0x776c:0x25950+0x776c+13]==b'-.0123456789\0'
  assert [i for i,flags in enumerate(original[0x25950+0x7caf:0x25950+0x7caf+256]) if flags&4]==list(range(48,58))
  optional=dict(conversion_scanner_data={'candidate_DS_offset':'776C','candidates':'-.0123456789','ctype_DS_offset':'7CAF','observed_digit_bit':4,'digit_bytes':list(range(48,58)),'maintained_scope':'Only consumed bit04 reproduced; other original CRT flags are absent.'},comparison_builtins={'21':'FAILURE/DA0C reads compare result','27':'SUCCESS/DA28 returns result==0'},original_sha256=ORIGINAL,exact_support_bytes=sum(u['bytes'] for u in manifest['support_units']),units=manifest['support_units'],empty_string_builtin=dict(index=19,resident_thunk='C2C7',overlay=16,entry='DAFB',returned_DS_offset='4942',observed_first_byte=0,maintained_scope='Builtin19 supplies owned empty81B backing; directory0..7 now route exact native getters to owned record. Other string services remain unsupported.'))
  optional['directory_builtins']=dict(string_selectors=list(range(8)),string_thunks=[f'{value:04X}' for value in directory_thunks],integer_entry_selector=3,integer_entry_thunk='C6DB',exact_getter_bytes=36,scope='Original table slots and getter bytes corroborated; maintained owned record/entry snapshots supply their data.')
 for name in ['DONE.TXT','PASS.TXT','FAIL.TXT']:(OUT/name).unlink(missing_ok=True)
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nEXECUTE >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(conf)
 with (OUT/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 summary=(OUT/'DONE.TXT').read_text().strip()
 assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
 assert summary.startswith(f'ASPECT_RUNTIME {manifest["diagnostic_case_count"]} cases ') and summary.endswith('0 failures'),summary
 directory=check_directory_metadata(records,(OUT/'RESULT.TXT').read_text())
 result=dict(passed=True,DOS_summary=summary,binary_sha256=sha(OUT/'EXECUTE.EXE'),manifest_sha256=sha(OUT/'manifest.json'),
  check_sha256=sha(Path(__file__).resolve()),result_sha256=sha(OUT/'RESULT.TXT'),optional_original=optional,
  original_inputs=[] if optional is None else [str(args.original)],fixture_count=manifest['fixture_count'],
  unsupported_slot_cases=manifest['unsupported_slot_cases'],
  directory_metadata=directory,fixture_data_sha256=sha(OUT/'CASES.DAT'),fixture_schema='ACV2',
  scope='Actual recovered dispatcher executes source-compiled authored ASX through real DOS files/far heap and native console/serial/WHEN commands. Serial queue/clock/carrier boundaries are explicit diagnostic models. Incomplete66-slot command surface; all149 unsupported in-range slots and255 unsupported SET subcommands abort. No full compiler/VM or arbitrary-bytecode safety.')
 (OUT/('checks-native.json' if optional else 'checks.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
