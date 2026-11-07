"""Split a source-linked code bank into a matched-parent transient overlay.

Only MZ relocation words and map segment addresses change. Near offsets and
instructions stay fixed. No original executable or inferred relocation exists.
"""
import hashlib,re,struct,zlib


def split(binary,map_path):
 raw=bytearray(binary.read_bytes());h=list(struct.unpack_from('<14H',raw))
 assert raw[:2]==b'MZ' and (h[2]-1)*512+(h[1] or 512)==len(raw)
 start=h[4]*16;image=bytearray(raw[start:]);listing=map_path.read_text()
 symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(
  r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 match=re.search(r'^LINE_PORT_CODE\s+FARCODE\s+\S+\s+([0-9a-f]{4}):0000\s+([0-9a-f]+)',listing,re.M|re.I)
 assert match
 bank=int(match[1],16);size=int(match[2],16);paragraphs=(size+15)//16
 lo=bank*16;hi=lo+paragraphs*16
 assert 256<size<=24000 and hi<=len(image) and not any(image[lo+size:hi])
 assert symbols['redisplay_snapshot'][1]==0
 target=symbols['redisplay_snapshot'][0]+1024
 assert target>=bank+paragraphs
 def segment(value):
  if bank<=value<bank+paragraphs:return target-paragraphs+value-bank
  return value-paragraphs if value>=bank+paragraphs else value
 def address(value):
  assert not lo<=value<hi
  return value-(hi-lo)if value>=hi else value
 payload=bytearray(image[lo:lo+size]);local=[];resident=[];incoming=[]
 count=h[3]
 for i in range(count):
  off,seg=struct.unpack_from('<HH',raw,h[12]+i*4);at=seg*16+off
  assert at+2<=len(image)
  value=struct.unpack_from('<H',image,at)[0];new=segment(value)
  if lo<=at<hi:
   assert at+2<=lo+size
   struct.pack_into('<H',payload,at-lo,new);local.append(at-lo)
  else:
   struct.pack_into('<H',image,at,new);resident.append(address(at))
   if bank<=value<bank+paragraphs:incoming.append(address(at))
 assert len(local)==len(set(local)) and len(resident)==len(set(resident))
 local.sort();assert len(local)<=512
 body=bytes(payload)+struct.pack('<'+'H'*len(local),*local)
 image=image[:lo]+image[hi:]
 expect_seg,expect_off=symbols['_line_overlay_expected']
 expect=address(expect_seg*16+expect_off)
 assert struct.unpack_from('<2H',image,expect)==(0x504c,0x314f)
 checksum=zlib.crc32(body)
 usage_seg,usage_off=symbols['terminal_usage'];usage_end_seg,usage_end=symbols['terminal_usage_end']
 assert usage_seg==usage_end_seg==bank and 0<=usage_off<usage_end<=size
 assert payload[usage_end-1:usage_end]==b'$' and b'$'not in payload[usage_off:usage_end-1]
 struct.pack_into('<8H',image,expect,size,len(local),checksum&65535,checksum>>16,segment(target),segment(symbols['terminal_program_kind'][0]),usage_off,usage_end-usage_off-1)
 h[3]=len(resident);h[7]=segment(h[7]);h[11]=segment(h[11])
 total=start+len(image);h[1]=total%512;h[2]=(total+511)//512
 struct.pack_into('<14H',raw,0,*h)
 raw[h[12]:h[12]+count*4]=bytes(count*4)
 for i,at in enumerate(resident):struct.pack_into('<HH',raw,h[12]+i*4,at%16,at//16)
 final=bytes(raw[:start])+bytes(image)
 # Preserve the linked input for independent auditing, never execute it as a
 # transient product: only the extracted, matched pair has loader constants.
 binary.with_name('terminal-linked.bin').write_bytes(binary.read_bytes())
 map_path.with_name('terminal-linked.map').write_text(listing)
 listing=re.sub(r'^LINE_PORT_CODE\s+FARCODE[^\n]*\n','',listing,flags=re.M)
 listing=re.sub(r'\b([0-9a-f]{4}):([0-9a-f]{4})\b',
  lambda m:f'{segment(int(m[1],16)):04x}:{m[2]}',listing,flags=re.I)
 binary.write_bytes(final);map_path.write_text(listing)
 binary.with_name('PCLINE.OVL').write_bytes(body)
 return dict(format='source-linked-parent-relative-fixups-v1',bank_bytes=size,
  relocations=len(local),incoming_resident_relocations=len(incoming),
  extracted_bytes=hi-lo,relative_target_segment=segment(target),arena_offset=16384,
  usage_offset=usage_off,usage_bytes=usage_end-usage_off-1,
  crc32=f'{checksum:08x}',sha256=hashlib.sha256(body).hexdigest(),
  linked_sha256=hashlib.sha256(binary.with_name('terminal-linked.bin').read_bytes()).hexdigest(),
  original_inputs=[],limitations=['Matched parent only; CRC is an identity check, not authentication.',
   'Static relocation extraction does not prove runtime lease/admission, latency or allocation acceptance.'])
