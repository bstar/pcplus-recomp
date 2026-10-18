#!/usr/bin/env python3
"""Source-only actual16-bit accounting helper with synthetic records and dates."""
import datetime,hashlib,json,random,struct
from pathlib import Path
from dos_image import DosImage
from unicorn.x86_const import UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/directory-accounting/DIRSTATS.EXE'
def main():
 cases=[];rng=random.Random(201)
 def run(record,year,month,day,delta,difference=256):
  d=DosImage(BINARY,BINARY.parent/'directory_accounting.map');source=0x4000;dest=source+difference
  d.uc.mem_write(d.data_base+0x3f00,b'\xa5'*1024);d.uc.mem_write(d.data_base+source,record)
  old=bytes(d.uc.mem_read(d.data_base+dest,114));before=bytes(d.uc.mem_read(d.data_base+source,114))
  result=d.call('_directory_accounting_patch',[source,dest,year,month,day,delta]);output=bytes(d.uc.mem_read(d.data_base+dest,114))
  valid=True
  try:
   datetime.date(year,month,day);valid=1980<=year<=2099
  except ValueError:valid=False
  assert result==(0 if valid else 2),(year,month,day,result)
  if valid:
   want=bytearray(before);want[61:70]=f'{month:02}/{day:02}/{year%100:02}'.encode()+b'\0';struct.pack_into('<H',want,70,(struct.unpack_from('<H',before,70)[0]+delta)&65535)
   assert output==want
  else:assert output==old
  for reg,val in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert d.uc.reg_read(reg)==val
  return d
 for _ in range(512):
  year=rng.randrange(1980,2100);day=datetime.date(year,1,1)+datetime.timedelta(days=rng.randrange(365));record=bytes(rng.randrange(256) for _ in range(114));run(record,day.year,day.month,day.day,rng.randrange(65536))
 cases.append({'case':'random-valid-date-count-modulo-and-opaque-preservation','inputs':512,'passed':True})
 for difference in [-113,-64,-1,0,1,64,113]:run(bytes(range(114)),2000,2,29,65535,difference)
 cases.append({'case':'overlapping-and-identical-source-destination-staged','inputs':7,'passed':True})
 for year,month,day in [(1979,12,31),(2100,1,1),(2001,2,29),(2000,2,30),(2026,0,1),(2026,13,1),(2026,1,0),(2026,4,31),(65535,65535,65535)]:run(bytes(range(114)),year,month,day,1)
 cases.append({'case':'invalid-gregorian-date-atomic-no-destination-change','inputs':9,'passed':True})
 for source,dest in [(65423,0x4000),(0x4000,65423),(0xdf80,0x4000),(0x4000,0xdf80)]:
  d=DosImage(BINARY,BINARY.parent/'directory_accounting.map');d.uc.mem_write(d.data_base+0x4000,b'X'*114);old=bytes(d.uc.mem_read(d.data_base+0x4000,114));assert d.call('_directory_accounting_patch',[source,dest,2026,10,17,1])==1;assert bytes(d.uc.mem_read(d.data_base+0x4000,114))==old
 cases.append({'case':'wrapping-and-active-stack-extents-rejected','inputs':4,'passed':True})
 for source,dest in [(65422,0x4000),(0x4000,65422)]:
  d=DosImage(BINARY,BINARY.parent/'directory_accounting.map');record=bytes(range(114));d.uc.mem_write(d.data_base+source,record)
  for reg in [UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX]:d.uc.reg_write(reg,0x9876)
  assert d.call('_directory_accounting_patch',[source,dest,2099,12,31,65535])==0
  result=bytes(d.uc.mem_read(d.data_base+dest,114));assert result[:61]==record[:61] and result[61:70]==b'12/31/99\0' and result[72:]==record[72:]
  for reg in [UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX]:assert d.uc.reg_read(reg)==0x9876
 cases.append({'case':'last-nonwrapping-record-and-callee-register-preservation','inputs':2,'passed':True})
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked maintained pure DOS helper; synthetic records only, no disk or UART.'};(BINARY.parent/'cpu-results.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',sum(x['inputs'] for x in cases),'accounting CPU cases')
if __name__=='__main__':main()
