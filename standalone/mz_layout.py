#!/usr/bin/env python3
"""Inspect DOS-only MZ load extent; align header without changing load bytes."""
import hashlib,struct

def sha(data):return hashlib.sha256(data).hexdigest()
def inspect(data):
 assert len(data)>=32
 h=list(struct.unpack_from('<14H',data))
 assert h[0]==0x5a4d and h[2] and h[1]<512 and h[13]==0
 declared=h[2]*512-(512-h[1] if h[1] else 0)
 assert declared==len(data),'DOS-only MZ must have no appended overlay'
 header=h[4]*16
 assert 32<=header<len(data) and h[12]>=28 and h[12]+h[3]*4<=header
 image=data[header:]
 return dict(header_bytes=header,image_bytes=len(image),image_sha256=sha(image),
  relocation_table_sha256=sha(data[h[12]:h[12]+h[3]*4]),
  exact_minimum_including_PSP=((len(image)+15)//16+h[5]+16)*16,
  page_minimum_including_PSP=(h[2]*32-h[4]+h[5]+16)*16)

def align_header(data):
 before=inspect(data);h=list(struct.unpack_from('<14H',data))
 # Keep file size within its present512-byte page and leave at most15 pad
 # bytes in that page. Insert only whole paragraphs before the load image.
 delta=((511-len(data)%512)//16)*16 if len(data)%512 else 0
 if not delta:return data,dict(before=before,after=before,header_padding_added=0)
 result=bytearray(data[:before['header_bytes']]+bytes(delta)+data[before['header_bytes']:])
 h[4]+=delta//16;assert h[4]<65536
 h[1]=len(result)%512;h[2]=(len(result)+511)//512
 assert h[2]<65536
 struct.pack_into('<14H',result,0,*h)
 after=inspect(result)
 assert after['image_sha256']==before['image_sha256']
 assert after['relocation_table_sha256']==before['relocation_table_sha256']
 assert after['exact_minimum_including_PSP']==before['exact_minimum_including_PSP']
 assert after['page_minimum_including_PSP']<=before['page_minimum_including_PSP']
 return bytes(result),dict(before=before,after=after,header_padding_added=delta)
