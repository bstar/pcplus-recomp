"""Extract the source-linked compiler bank into a matched-parent cold module.

The caller selects an inactive, retained overlay arena. This tool proves layout,
not exclusive runtime ownership. Only MZ-declared segment fixups are transformed.
"""
import hashlib,re,struct,zlib
sha=lambda data:hashlib.sha256(data).hexdigest()
def crc16(data):
 crc=65535
 for byte in data:
  crc^=byte
  for _ in range(8):crc=(crc>>1)^(0xa001 if crc&1 else 0)
 return crc

def split(binary,map_path,arena_symbol,arena_offset=0,arena_bytes=4096,keep_symbol='UI_STORAGE',overlays=()):
 raw=bytearray(binary.read_bytes());h=list(struct.unpack_from('<14H',raw))
 assert raw[:2]==b'MZ' and (h[2]-1)*512+(h[1] or 512)==len(raw)
 start=h[4]*16;image=bytearray(raw[start:]);listing=map_path.read_text()
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 classes={n:c for n,c in re.findall(r'^(\w+)\s+(\w+)\s+\w+\s+[0-9a-f]+:[0-9a-f]+\s+[0-9a-f]+\s*$',listing,re.M|re.I)}
 segments={n:(int(s,16),int(o,16),int(z,16)) for n,s,o,z in re.findall(r'^(\w+)\s+\w+\s+\w+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)\s*$',listing,re.M|re.I)}
 bank,offset,size=segments['LEASE_BANK'];assert offset==0 and 2<=size<=4096
 size=(size+15)//16*16
 paras=(size+15)//16;lo,hi=bank*16,(bank+paras)*16
 assert lo<len(image) and hi<=len(image)+15
 if hi>len(image):image+=bytes(hi-len(image))
 assert not any(image[lo+size:hi])
 arena,off=symbols.get(arena_symbol,segments.get(arena_symbol,(None,None))[:2]);assert arena is not None
 arena_byte=arena*16+off+arena_offset
 assert arena_byte%16==0 and arena_bytes>=size
 # Relocation words referring to the removed bank now refer to the selected arena.
 def segment(value):
  if bank<=value<bank+paras:return target+value-bank
  return value-paras if value>=bank+paras else value
 def address(value):
  assert not lo<=value<hi
  return value-(hi-lo) if value>=hi else value
 target=(lo if arena_byte==lo else address(arena_byte))//16
 keep_seg,keep_off=symbols.get(keep_symbol,segments.get(keep_symbol,(None,None))[:2]);assert keep_seg is not None
 keep_byte=keep_seg*16+keep_off
 keep=((lo if keep_byte==lo else address(keep_byte))+15)//16+16
 assert target+16>=keep
 payload=bytearray(image[lo:lo+size]);local=[];resident=[]
 for i in range(h[3]):
  off,seg=struct.unpack_from('<HH',raw,h[12]+i*4);at=seg*16+off;assert at+2<=len(image)
  value=struct.unpack_from('<H',image,at)[0]
  if lo<=at<hi:
   assert at+2<=lo+size;struct.pack_into('<H',payload,at-lo,segment(value));local.append(at-lo)
  else:
   struct.pack_into('<H',image,at,segment(value));resident.append(address(at))
 local.sort();assert len(local)<=256 and all(b>=a+2 for a,b in zip(local,local[1:]))
 body=bytes(payload)+struct.pack('<'+'H'*len(local),*local)
 assert len(body)<=arena_bytes and len(resident)==len(set(resident))
 image=image[:lo]+image[hi:]
 expected=symbols['_compiler_lease_expected'];at=address(expected[0]*16+expected[1])
 assert struct.unpack_from('<2H',image,at)==(0x4342,1)
 struct.pack_into('<7H',image,at,0x4342,1,size,len(local),crc16(body),target,keep)
 # Existing matched-parent modules contain parent-relative segment words too.
 # Rebase both their fixups and their resident expected metadata together.
 for kind,other in overlays:
  leaf,anchor,words=('PCLINE.OVL','_line_overlay_expected',8) if kind=='line' else ('PCMETA.OVL','_meta_loader_expected',10)
  path=binary.with_name(leaf);data=bytearray(path.read_bytes());assert sha(data)==other['sha256']
  count=other['relocations'];n=other['bank_bytes'];assert len(data)==n+2*count
  for fix in struct.unpack_from('<'+'H'*count,data,n):
   value=struct.unpack_from('<H',data,fix)[0]
   assert not bank<=value<bank+paras,'cross-module bank pointer violates exclusive lifetime'
   struct.pack_into('<H',data,fix,segment(value))
  checksum=zlib.crc32(data);s,o=symbols[anchor];where=address(s*16+o)
  fields=list(struct.unpack_from('<'+'H'*words,image,where))
  if kind=='line':
   assert fields[:2]==[n,count] and fields[2]|fields[3]<<16==int(other['crc32'],16)
   fields[2:6]=[checksum&65535,checksum>>16,segment(fields[4]),segment(fields[5])]
   other['relative_target_segment']=fields[4]
  else:
   assert fields[:4]==[0x4d4c,1,n,count] and fields[4]|fields[5]<<16==int(other['crc32'],16)
   fields[4:9]=[checksum&65535,checksum>>16,segment(fields[6]),segment(fields[7]),segment(fields[8])]
   other['relative_target_segment']=fields[6];other['relative_arena_segment']=fields[8]
  struct.pack_into('<'+'H'*words,image,where,*fields)
  path.write_bytes(data);other.update(sha256=sha(data),crc32=f'{checksum:08x}',compiler_lease_rebased=True)
 # Every permanently retained section and stack must be wholly below the cut.
 for name,(s,o,n) in segments.items():
  if name=='LEASE_BANK' or name.startswith('LEASE_PAD') or classes[name]=='OVERLAY':continue
  if name in ('UI_STORAGE','REDISPLAY_STORAGE','SNAPSHOT_STORAGE','FAR_STORAGE','HISTORY_STORAGE','RESET_DATA'):continue
  assert address(s*16+o)+n<=keep*16-256,(name,s,o,n,keep)
 old_count=h[3];h[3]=len(resident);h[7]=segment(h[7]);h[11]=segment(h[11])
 total=start+len(image);h[1]=total%512;h[2]=(total+511)//512
 struct.pack_into('<14H',raw,0,*h);raw[h[12]:h[12]+old_count*4]=bytes(old_count*4)
 for i,p in enumerate(resident):struct.pack_into('<HH',raw,h[12]+4*i,p%16,p//16)
 binary.with_name('compiler-lease-linked.bin').write_bytes(binary.read_bytes())
 map_path.with_name('compiler-lease-linked.map').write_text(listing)
 listing=re.sub(r'^(LEASE_BANK\s+)LEASE_BANK',r'\1OVERLAY',listing,flags=re.M)
 listing=re.sub(r'\b([0-9a-f]{4}):([0-9a-f]{4})\b',lambda m:f'{segment(int(m[1],16)):04x}:{m[2]}',listing,flags=re.I)
 binary.write_bytes(bytes(raw[:start])+image);map_path.write_text(listing)
 binary.with_name('PCCOMP.OVL').write_bytes(body)
 return dict(format='source-linked-compiler-lease-v1',original_inputs=[],bank_bytes=size,relocations=len(local),
  sha256=sha(body),crc16=f'{crc16(body):04x}',relative_target_segment=target,keep_paragraphs=keep,
  module_bytes=len(body),extracted_bytes=hi-lo,arena_symbol=arena_symbol,arena_offset=arena_offset,arena_bytes=arena_bytes,
  linked_sha256=sha(binary.with_name('compiler-lease-linked.bin').read_bytes()),
  limitations=['Matched parent only; CRC16 is corruption detection, not authenticity.','Caller must own inactive overlay arena; layout extraction does not establish runtime ownership.'])
