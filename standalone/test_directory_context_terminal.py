#!/usr/bin/env python3
"""Actual terminal retained context across PROGRAM/COMSPEC and memory pressure."""
import hashlib,json,re,struct,subprocess,sys
from pathlib import Path
from test_connection_dos import ROOT,BINARY,run
from modem_fixtures import fixture
sys.path.insert(0,str(ROOT/'src/directory'))
from codec import DirectoryRecord201

def main():
 listing=(ROOT/'build/terminal/terminal.map').read_text();symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 dg=int(re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I)[1],16)
 def near(name):seg,off=symbols[name];return seg*16+off-dg*16
 context=near('terminal_directory_context');required=16+dg+(context+496+15)//16
 out=ROOT/'build/directory-context';out.mkdir(parents=True,exist_ok=True);child=out/'CTXCHILD.COM'
 defines=dict(DGROUP_SEG=dg,PROCESS_PSP=near('process_psp'),CONTEXT_VALID=near('terminal_directory_context_valid'),CONTEXT=context,REQUIRED_PARAS=required)
 subprocess.run(['nasm','-f','bin',*[f'-D{k}={v}' for k,v in defines.items()],str(ROOT/'standalone/directory_context_child.asm'),'-o',str(child)],check=True)
 header=b'CaseTest:\0'.ljust(25,b'\0')+b'23\0'.ljust(25,b'\0')+bytes(200)
 record=(DirectoryRecord201.default().with_string('name',b'Owned context').with_string('number',b'AB').with_integer('port_override',1).with_integer('baud_index',6).with_integer('parity_index',0).with_integer('data_bits',8).with_integer('stop_bits',1).with_integer('terminal_id',6).to_bytes())
 directory=bytearray(header+bytes(200*114));directory[250+16*114:250+17*114]=record
 keys=bytearray(540)
 for i in range(10):struct.pack_into('<H',keys,i*54,3)
 command=b'D:\\CTXCHILD.COM';struct.pack_into('<H',keys,0,1);keys[2:2+len(command)]=command
 folder=ROOT/'build/connection-dos/directory-context';folder.mkdir(parents=True,exist_ok=True);(folder/'CONTEXT.BIN').unlink(missing_ok=True)
 result=run('directory-context','success','p3000 a-1 p1800 space p1200 a-x',directory=bytes(directory),prm=fixture(timeout=5),arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:17 /C:LEGACY /T:D:\\TEST.KEY COM1 38400 HARD',directory_entry=17,files={'CTXCHILD.COM':child.read_bytes(),'TEST.KEY':bytes(keys)})
 data=(folder/'CONTEXT.BIN').read_bytes() if (folder/'CONTEXT.BIN').exists() else b''
 checks=result['checks'];checks['full_context_child_result']=len(data)==508
 if len(data)==508:
  magic,status,parent,ds,retained,allocated=struct.unpack_from('<6H',data)
  checks['parent_context_survives_disjoint16KiB_allocation_fill']=magic==0x4358 and status==15
  checks['parent_MCB_covers_context']=retained>=required and ds==parent+16+dg
  expected=struct.pack('<H',17)+header+record+struct.pack('<H',1)+b'D:\\TEST.PRM'.ljust(64,b'\0')+b'D:\\TEST.DIR'.ljust(64,b'\0')
  checks['exact496_bytes_raw_codes_record_and_bound_request']=data[12:]==expected
  checks['allocation_disjoint_from_parent']=allocated>=parent+retained or allocated+0x400<=parent
 result.update(passed=all(checks.values()),binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),child_sha256=hashlib.sha256(child.read_bytes()).hexdigest(),sample_hex=data.hex(),linker_defines=defines,scope='Actual DOS directory startup with explicit legacy codes, loopback modem, global Meta PROGRAM/COMSPEC child, retained496-byte parent context and disjoint16KiB allocation/fill. Child compares full context before/after without parent mutation; exact bytes and subsequent directory accounting/hardware restoration checked separately. Not live setup or physical modem proof.')
 (out/'terminal-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
if __name__=='__main__':main()
