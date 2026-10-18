#!/usr/bin/env python3
"""Reject damaged configuration call frames, relocations and segment extents."""
import hashlib,json,re,struct,tempfile
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal'
def main():
 binary=OUT/'TERMINAL.EXE';mp=OUT/'terminal.map';raw=binary.read_bytes();listing=mp.read_text()
 memory=inspect_terminal_memory(binary,mp)
 assert memory['configuration_bridge_pairs_verified']==22 and memory['far_code_bridge_pairs_verified']==66
 header=struct.unpack_from('<14H',raw);start=header[4]*16
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 def at(name):s,o=symbols[name];return start+s*16+o
 mutations=[]
 for name,count in [('_directory_live_decode',7),('_directory_live_read',8),('_directory_live_read_context',9),('_directory_live_context_matches',5),('_live_configuration_decode',7),('_live_setup_bind',3),('_live_setup_begin',5),('_live_setup_finish',2),('_live_setup_abort',1),('_live_setup_finish_policy',3),('_live_setup_acknowledge',1)]:
  for suffix,delta,kind in [('',5,'near-argument-offset'),('',3+count*3+1,'far-target'),('',3+count*3+5+4,'near-return'),('_far',5,'far-argument-offset'),('_far',3+count*3+1,'implementation-target'),('_far',3+count*3+3+4,'far-return')]:
   bad=bytearray(raw);bad[at(name+suffix)+delta]^=1;mutations.append((name+':'+kind,bad,listing))
 for name in ['config_memcpy_service_','config_memset_service_','config_memcmp_service_','config_strchr_service_','config_canonical_service_','_config_terminal_decode','_config_modem_decode','_config_prm_read','_config_directory_read','_config_number_expand','_config_live_expand']:
  service=name if name.endswith('_') else name+'_service'
  for label,location in [('service-far-target',at(service)+1),('resident-call-frame',at(name+'_resident')+1)]:
   bad=bytearray(raw);bad[location]^=1;mutations.append((name+':'+label,bad,listing))
 # Remove one required segment relocation from every public entry and callback.
 for name,segment_offset in [('_directory_live_read_context',33),('_live_configuration_decode',27),('config_memcpy_service_',3),('_config_number_expand_service',3),('_live_setup_bind',15),('_live_setup_begin',21),('_live_setup_finish',12),('_live_setup_abort',9),('_live_setup_finish_policy',15),('_live_setup_acknowledge',9),('config_canonical_service_',3),('_config_live_expand_service',3)]:
  bad=bytearray(raw);wanted=at(name)-start+segment_offset
  for i in range(header[3]):
   off,seg=struct.unpack_from('<HH',bad,header[12]+4*i)
   if seg*16+off==wanted:struct.pack_into('<HH',bad,header[12]+4*i,0,0);break
  else:raise AssertionError(('No relocation for',name))
  mutations.append((name+':missing-MZ-relocation',bad,listing))
 missing=listing.replace('CONFIG_CODE','UNRECOGNIZED_CONFIG_CODE')
 oversized=re.sub(r'(?m)^(CONFIG_CODE\s+FARCODE\s+\S+\s+\S+\s+)\w+',r'\g<1>00010001',listing)
 wrong_end=re.sub(r'(?m)^([0-9a-f]{4}):[0-9a-f]{4}([*+ ]+\s+terminal_config_code_end\s*)$',r'\g<1>:0001\g<2>',listing)
 for label,text in [('missing-class',missing),('oversized-code',oversized),('incomplete-C-extent',wrong_end)]:
  assert text!=listing;mutations.append((label,raw,text))
 with tempfile.TemporaryDirectory() as directory:
  exe=Path(directory)/'BAD.EXE';mapfile=Path(directory)/'bad.map'
  for label,data,text in mutations:
   exe.write_bytes(data);mapfile.write_text(text)
   try:inspect_terminal_memory(exe,mapfile)
   except AssertionError:pass
   else:raise AssertionError(('Damaged configuration ABI accepted',label))
 result=dict(passed=True,binary_sha256=hashlib.sha256(raw).hexdigest(),configuration_bridge_pairs_verified=22,entry_argument_counts=[1,2,3,5,7,8,9],rejected_mutations=[m[0] for m in mutations],memory=memory,scope='Serialized DOS MZ and linker-map validation of eleven explicit near-cdecl entries, five compiler register callbacks and six resident cdecl callbacks; exact argument-copy frames, target calls/returns, relocations and full configuration C extent. Independent CPU candidate/directory/owner suites and actual DOS child allocation exercise behavior.')
 (OUT/'config-far-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Configuration ABI:',len(mutations),'damaged frames/layouts rejected')
if __name__=='__main__':main()
