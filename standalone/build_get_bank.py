#!/usr/bin/env python3
"""Build the complete opt-in GET code bank with explicit resident callbacks."""
import re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def build(output,flags):
 own=['runtime_get_command_run','runtime_get_command_recover','runtime_get_command_ready','runtime_get_command_retained','runtime_get_command_execute',
      'runtime_get_native','runtime_get_native_active','runtime_get_native_aborted','runtime_get_native_generation',
      'runtime_get_context_policy','runtime_get_context_parent_policy','runtime_get_context_enter','runtime_get_context_leave',
      'runtime_get_anchor_begin','runtime_get_anchor_active','runtime_get_anchor_info','runtime_get_field_configure','runtime_get_field_begin',
      'runtime_get_field_phase','runtime_get_field_result','runtime_get_field_active','runtime_get_field_poll','runtime_get_field_position',
      'runtime_get_field_end','runtime_get_field_commit','runtime_get_field_recover','runtime_get_field_discard',
      'runtime_get_native_field','runtime_get_cursor','runtime_get_adopt']
 callbacks=dict(runtime_set_error='get_bank_error',runtime_when_get_begin='get_bank_when_begin',runtime_when_get_end='get_bank_when_end',
  runtime_when_get_poll='get_bank_when_poll',runtime_when_get_unwind='get_bank_when_unwind',runtime_when_get_confirm_abort='get_bank_confirm',
  runtime_when_get_confirm_active='get_bank_confirm_active',runtime_when_get_confirm_recover='get_bank_confirm_recover',
  aspect_render_field='get_bank_render_field',aspect_render_active='get_bank_render_active',aspect_render_field_state='get_bank_render_state',
  aspect_render_confirm_state='get_bank_render_confirm',aspect_render_window_active='get_bank_render_window',aspect_render_program_active='get_bank_render_program',
  runtime_keyboard_peek='get_bank_peek',runtime_keyboard_read='get_bank_key',runtime_console_emit_byte='get_bank_emit')
 c_aliases={n:n+'_impl' for n in own};c_aliases.update(callbacks)
 objects=[];sources=[Path(__file__).resolve(),ROOT/'src/aspect/get_bank.inc']
 c_names=['get_runtime','get_context','get_command','get_native_field','get_vm_bindings']
 for name in c_names:
  source=ROOT/'src/aspect'/(name+'.c');obj=output/(name+'-c-bank.obj');sources.append(source)
  subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we',*flags,'-nt=GET_VM_CODE','-nc=FARCODE',
   *['-d'+n+'='+v for n,v in c_aliases.items()],'-i='+str(ROOT/'src/aspect'),'-fo='+str(obj),str(source)],cwd=output,check=True);objects.append(str(obj))
 # Pure editor functions already declare far calls and need no resident thunks.
 source=ROOT/'src/aspect/get_field.c';obj=output/'get-field-bank.obj';sources.append(source)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-dASPECT_GET_BANK','-nt=GET_FIELD_CODE','-nc=FARCODE',
  '-i='+str(ROOT/'src/aspect'),'-fo='+str(obj),str(source)],cwd=output,check=True);objects.append(str(obj))
 asm_aliases={'_'+n:'_'+n+'_impl' for n in own}
 asm_aliases.update(runtime_get_abort_gate='runtime_get_abort_gate_impl',aspect_abort_recovered='get_bank_abort',runtime_alarm_abort_gate='get_bank_alarm',aspect_dispatch_read='_get_bank_read')
 asm_aliases['_runtime_get_native.return']='_runtime_get_native_impl.return'
 for name in ['get_native','get_checkpoint','get_command','get_native_field','get_runtime_storage','get_vm_bindings','get_bank']:
  source=ROOT/'src/aspect'/(name+'.asm');obj=output/(name+'-bank.obj');sources.append(source)
  aliases=[] if name in ('get_runtime_storage','get_vm_bindings','get_bank') else ['-D'+n+'='+v for n,v in asm_aliases.items()]
  bank=[] if name in ('get_runtime_storage','get_vm_bindings','get_bank') else ['-D_TEXT=GET_VM_CODE','-DCODE=FARCODE']
  subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/','-I'+str(ROOT/'src/aspect')+'/',*flags,*bank,*aliases,str(source),'-o',str(obj)],check=True);objects.append(str(obj))
 sources += [ROOT/'src/aspect'/n for n in ('get_runtime.h','get_context.h','get_command.h','get_checkpoint.h','get_field.h','get_native_field.h')]
 return objects,sources


def audit(output):
 """Fail the opt-in build if near calls, state or CRT layout cross banks."""
 text=(output/'ASPECT.map').read_text()
 segments={n:dict(segment=int(s,16),offset=int(o,16),size=int(z,16))
  for n,s,o,z in re.findall(r'^(\w+)\s+\w+\s+\w+\s+([0-9a-f]{4}):([0-9a-f]{4,8})\s+([0-9a-f]{8})\s*$',text,re.M|re.I)}
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',text,re.M|re.I)}
 near=segments['_TEXT'];bank=segments['GET_VM_CODE'];field=segments['GET_FIELD_CODE'];state=segments['GET_RUNTIME_STORAGE']
 assert near['segment']==0 and near['offset']==0 and near['size']<=65536
 assert bank['offset']==0 and bank['size']<65536 and field['segment']!=bank['segment']
 def in_segment(name,segment):
  cs,ip=symbols[name];assert cs==segment['segment'] and segment['offset']<=ip<segment['offset']+segment['size'],name
 inc=(ROOT/'src/aspect/get_bank.inc').read_text()
 for name in re.findall(r'^GET_ENTRY (\w+),',inc,re.M):
  in_segment(name,near);in_segment(name+'_impl',bank);in_segment(name+'_far',bank)
 for name,target in re.findall(r'^GET_CALLBACK (\w+),(\w+),',inc,re.M):
  in_segment(name,bank);in_segment(name+'_resident',near);in_segment(target,near)
 for name in ('_runtime_get_native_impl','runtime_get_abort_gate_impl','get_bank_abort','get_bank_alarm'):
  in_segment(name,bank)
 for name in ('runtime_get_abort_gate','aspect_abort_recovered','get_bank_abort_resident','get_bank_alarm_resident'):
  in_segment(name,near)
 assert state['size']==206 and symbols['_runtime_get_field_storage']==(state['segment'],state['offset'])
 linear=lambda item:item['segment']*16+item['offset']
 assert linear(state)+state['size']<=linear(segments['_NULL'])<linear(segments['CONST'])<linear(segments['_BSS'])<linear(segments['STACK'])
 assert segments['STACK']['size']==8192
 group=re.search(r'DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',text,re.I)
 assert int(group[3],16)<=65536
 exe=(output/'ASPECT.EXE').read_bytes();header=struct.unpack_from('<14H',exe)
 assert header[0]==0x5a4d
 return dict(passed=True,near_code_bytes=near['size'],near_code_spare=65536-near['size'],
  GET_code_bytes=bank['size'],editor_code_bytes=field['size'],field_state_bytes=state['size'],
  DGROUP_bytes=int(group[3],16),stack_bytes=8192,
  minimum_DOS_bytes_including_PSP=((len(exe)-header[4]*16+15)//16+header[5]+16)*16,
  near_entries=6,resident_callback_count=len(re.findall(r'^GET_CALLBACK ',inc,re.M)),
  scope='Link-map segment/callback/CRT order admission; execution and available conventional memory require separate DOS tests.')
