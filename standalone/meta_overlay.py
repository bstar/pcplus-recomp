"""Extract source-linked META code; patch only declared MZ relocation words.

Optional existing PCLINE is rebased through the same segment transform. Both
modules target the shared arena and must have exclusive foreground leases.
"""
import hashlib,re,struct,zlib
sha=lambda data:hashlib.sha256(data).hexdigest()
def split(binary,map_path,arena_symbol,arena_bytes=63000,line_overlay=None,max_bytes=24000):
 raw=bytearray(binary.read_bytes());h=list(struct.unpack_from('<14H',raw));assert raw[:2]==b'MZ' and (h[2]-1)*512+(h[1] or 512)==len(raw)
 start=h[4]*16;image=bytearray(raw[start:]);listing=map_path.read_text()
 symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 m=re.search(r'^META_EDITOR_CODE\s+FARCODE\s+\S+\s+([0-9a-f]+):0000\s+([0-9a-f]+)',listing,re.M|re.I);assert m
 bank,size=int(m[1],16),int(m[2],16);paras=(size+15)//16;lo,hi=bank*16,(bank+paras)*16
 assert max_bytes in (24000,43000) and 256<=size<=max_bytes and hi<=len(image) and not any(image[lo+size:hi])
 arena,offset=symbols[arena_symbol];assert offset==0 and arena_bytes==63000 and arena>=bank+paras
 target=arena+1024-paras
 def segment(value):
  if bank<=value<bank+paras:return target+value-bank
  return value-paras if value>=bank+paras else value
 def address(value):
  assert not lo<=value<hi
  return value-(hi-lo)if value>=hi else value
 payload=bytearray(image[lo:lo+size]);local=[];resident=[]
 for i in range(h[3]):
  off,seg=struct.unpack_from('<HH',raw,h[12]+4*i);at=seg*16+off;assert at+2<=len(image)
  value=struct.unpack_from('<H',image,at)[0]
  if lo<=at<hi:
   assert at+2<=lo+size;struct.pack_into('<H',payload,at-lo,segment(value));local.append(at-lo)
  else:struct.pack_into('<H',image,at,segment(value));resident.append(address(at))
 local.sort();assert len(local)<=512 and len(local)==len(set(local)) and all(b>=a+2 for a,b in zip(local,local[1:]))
 assert len(resident)==len(set(resident)) and size+len(local)*2+16385<=61000
 body=bytes(payload)+struct.pack('<'+'H'*len(local),*local);crc=zlib.crc32(body)
 image=image[:lo]+image[hi:]
 expected_seg,expected_off=symbols['_meta_loader_expected'];at=address(expected_seg*16+expected_off)
 assert struct.unpack_from('<2H',image,at)==(0x4d4c,1)
 ds=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert ds
 struct.pack_into('<10H',image,at,0x4d4c,1,size,len(local),crc&65535,crc>>16,target,segment(int(ds[1],16)),segment(arena),arena_bytes)
 if line_overlay is not None:
  path=binary.with_name('PCLINE.OVL');previous=path.read_bytes();assert sha(previous)==line_overlay['sha256']
  other=bytearray(previous);n=line_overlay['bank_bytes'];count=line_overlay['relocations'];assert len(other)==n+2*count
  for off in struct.unpack_from('<'+'H'*count,other,n):
   value=struct.unpack_from('<H',other,off)[0];assert not bank<=value<bank+paras,'cross-module pointer would violate exclusive lifetime'
   struct.pack_into('<H',other,off,segment(value))
  checksum=zlib.crc32(other);s,o=symbols['_line_overlay_expected'];p=address(s*16+o);fields=list(struct.unpack_from('<8H',image,p))
  assert fields[:2]==[n,count] and fields[2]|fields[3]<<16==int(line_overlay['crc32'],16)
  fields[2:6]=[checksum&65535,checksum>>16,segment(fields[4]),segment(fields[5])];struct.pack_into('<8H',image,p,*fields)
  path.write_bytes(other);line_overlay.update(sha256=sha(other),crc32=f'{checksum:08x}',relative_target_segment=fields[4],meta_rebase_previous_sha256=sha(previous))
 old_count=h[3];h[3]=len(resident);h[7]=segment(h[7]);h[11]=segment(h[11]);total=start+len(image);h[1]=total%512;h[2]=(total+511)//512
 struct.pack_into('<14H',raw,0,*h);raw[h[12]:h[12]+old_count*4]=bytes(old_count*4)
 for i,p in enumerate(resident):struct.pack_into('<HH',raw,h[12]+4*i,p%16,p//16)
 binary.with_name('meta-linked.bin').write_bytes(binary.read_bytes());map_path.with_name('meta-linked.map').write_text(listing)
 listing=re.sub(r'^(META_EDITOR_CODE\s+)FARCODE',r'\1OVERLAY',listing,flags=re.M)
 listing=re.sub(r'\b([0-9a-f]{4}):([0-9a-f]{4})\b',lambda m:f'{segment(int(m[1],16)):04x}:{m[2]}',listing,flags=re.I)
 binary.write_bytes(bytes(raw[:start])+image);map_path.write_text(listing);binary.with_name('PCMETA.OVL').write_bytes(body)
 return dict(format='source-linked-meta-parent-relative-fixups-v1',bank_bytes=size,relocations=len(local),extracted_bytes=hi-lo,relative_target_segment=target,relative_arena_segment=segment(arena),arena_offset=16384,arena_bytes=arena_bytes,crc32=f'{crc:08x}',sha256=sha(body),linked_sha256=sha(binary.with_name('meta-linked.bin').read_bytes()),original_inputs=[],limitations=['Matched parent only; CRC32 identifies bytes, not authenticity.','Caller must prove exclusive retained arena and prevent entry before READY; active callbacks prohibit unloading.'])
