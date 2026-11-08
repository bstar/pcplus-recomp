"""Read only an owned DOSBox fixture observer before timeout cleanup."""
import hashlib,json,os,struct,subprocess
from pathlib import Path


def snapshot(pid,folder):
 folder=Path(folder);binary=(folder/'RENDER.COM').read_bytes()
 prefix=bytes.fromhex('9c505351525657551e06fc89e5')
 offset=binary.index(prefix);handler=offset+0x100;signature=binary[offset:offset+64]
 result=dict(snapshot_verified=False,application_passed=False,observer_sha256=hashlib.sha256(binary).hexdigest(),
  scope='Timed-out owned emulator fixture only. Exact resident code, allocated DOS MCB/PSP and live sample anchor the observer allocation. UMB backing may be separate. No hardware or application acceptance.')
 result['candidates']=dict(code=0,psp=0,mcb=0,live_sample=0)
 required=max(handler+64,binary.index(b'VWX1')+0x100+10 if binary.count(b'VWX1')==1 else 0)
 try:
  with open('/proc/'+str(pid)+'/mem','rb',buffering=0) as memory:
   budget=256*1024*1024
   for row in Path('/proc/'+str(pid)+'/maps').read_text().splitlines():
    fields=row.split();low,high=(int(s,16) for s in fields[0].split('-'))
    if not fields[1].startswith('rw') or high-low<65536:continue
    if len(fields)>5 and fields[5] not in ('[heap]','/dev/zero'):continue
    for start in range(low,high,8*1024*1024):
     size=min(high-start,8*1024*1024,budget)
     if size<=0:break
     budget-=size
     try:data=os.pread(memory.fileno(),size,start)
     except OSError:continue
     pos=data.find(signature)
     while pos>=0:
      result['candidates']['code']+=1
      address=start+pos-handler
      try:owned=os.pread(memory.fileno(),65552,address-16)
      except OSError:owned=b''
      # DOSBox can back UMB pages separately from conventional RAM. Bind the
      # resident COM by its exact code, allocated MCB, PSP and live sample.
      if len(owned)>=required+16 and owned[16:18]==b'\xcd\x20':result['candidates']['psp']+=1
      if len(owned)>=required+16 and owned[0] in (77,90) and owned[16:18]==b'\xcd\x20' and owned[handler+16:handler+80]==signature:
       result['candidates']['mcb']+=1
       cs=struct.unpack_from('<H',owned,1)[0]
       allocation=struct.unpack_from('<H',owned,3)[0]*16
       sample=struct.unpack_from('<4H',owned,16+0x10b)
       if cs and allocation>=required and sample[0:2]==(0x524e,1) and sample[2] in (0,1) and sample[3]<=8:
        result['candidates']['live_sample']+=1
        resident=owned[16:16+min(allocation,65536)]
        (folder/'observer-memory.bin').write_bytes(resident)
        result.update(snapshot_verified=True,observer_bytes=len(resident),observer_sha256_memory=hashlib.sha256(resident).hexdigest(),observer_segment=cs,sample_header=sample)
        if binary.count(b'VWX1')==1:
         from notice_video_probe import read,BYTES
         count,overflow,records=struct.unpack_from('<3H',binary,binary.index(b'VWX1')+4)
         assert overflow==count+2 and records==count+4
         result['video']=read(resident[count:count+BYTES])
        break
      pos=data.find(signature,pos+1)
     if result['snapshot_verified'] or budget<=0:break
    if result['snapshot_verified'] or budget<=0:break
 except (OSError,ValueError,AssertionError) as error:result['error']=type(error).__name__+': '+str(error)
 (folder/'timeout-snapshot.json').write_text(json.dumps(result,indent=2)+'\n')


def run(args,**kwargs):
 if args[0]!='dosbox-x':return subprocess.run(args,**kwargs)
 timeout=kwargs.pop('timeout');folder=Path(kwargs['cwd'])
 with subprocess.Popen(args,**kwargs) as process:
  try:code=process.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   try:snapshot(process.pid,folder)
   finally:process.kill();process.wait()
   raise
 return subprocess.CompletedProcess(args,code)
