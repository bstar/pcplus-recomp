"""Package a compact PCCONN MZ into the shared loader's companion format.

The shared Line/Meta/compiler loader (src/line_port/overlay_shared.asm) reads
`bytes` payload bytes followed by `relocs` two-byte payload offsets, checks
CRC32 and EOF, then adds the parent load delta to each fixup word, refusing
carry, a result >= A000h, an offset past the payload, or an offset not at
least two bytes past its predecessor. Module-relative MZ segment words are
therefore pre-rebased here by the arena's parent-relative target segment, so
the unchanged loader produces exactly what a DOS MZ load at that arena would.

This proves file layout only. It does not grant arena ownership, initialize
BSS/stack, or admit the module to any parent.
"""
import hashlib,struct,zlib

sha=lambda data:hashlib.sha256(data).hexdigest()


def parse_mz(raw):
    raw=bytes(raw);h=struct.unpack_from('<14H',raw)
    assert raw[:2]==b'MZ' and (h[2]-1)*512+(h[1] or 512)==len(raw),'MZ size'
    start=h[4]*16;payload=raw[start:]
    relocs=[]
    for i in range(h[3]):
        off,seg=struct.unpack_from('<HH',raw,h[12]+4*i);at=seg*16+off
        assert at+2<=len(payload),('relocation outside file image',at)
        relocs.append(at)
    footprint=((len(payload)+15)//16+h[5])*16
    return dict(header=h,payload=payload,relocs=relocs,footprint=footprint)


def package(raw,target_segment,extent_bytes):
    mz=parse_mz(raw);payload=bytearray(mz['payload']);relocs=sorted(mz['relocs'])
    assert len(set(relocs))==len(relocs) and all(b>=a+2 for a,b in zip(relocs,relocs[1:])),'overlapping relocations'
    paragraphs=mz['footprint']//16
    for at in relocs:
        value=struct.unpack_from('<H',payload,at)[0]
        # Every fixup must name the module itself; cross-image pointers would
        # survive release and violate the exclusive extent.
        assert value<paragraphs,('nonlocal segment word',at,value)
        struct.pack_into('<H',payload,at,value+target_segment)
    assert len(payload)<65535 and (not relocs or relocs[-1]<len(payload)-1)
    body=bytes(payload)+struct.pack('<%dH'%len(relocs),*relocs)
    # The loader probes EOF by reading one byte at the first byte past the
    # file inside the arena; the module's BSS/stack must also fit.
    eof_end=len(body)+1
    assert eof_end<=extent_bytes and mz['footprint']<=extent_bytes,('extent',eof_end,mz['footprint'],extent_bytes)
    crc=zlib.crc32(body)
    return body,dict(format='source-linked-connection-module-v1',payload_bytes=len(payload),relocations=len(relocs),
        module_bytes=len(body),eof_probe_end=eof_end,allocated_image_bytes=mz['footprint'],
        target_segment=target_segment,extent_bytes=extent_bytes,crc32=f'{crc:08x}',sha256=sha(body),
        polls=dict(data=-(-len(body)//512),eof=1,fixups=-(-len(relocs)//32)),
        limitations=['Layout only: the caller must own the extent; CRC32 is corruption detection, not authenticity.',
                     'BSS and stack beyond the file image are not initialized by the loader.'])


def loader_apply(body,payload_bytes,relocs,delta):
    """Model overlay_shared.asm .fixups exactly; None where the loader refuses."""
    image=bytearray(body[:payload_bytes]);table=struct.unpack_from('<%dH'%relocs,body,payload_bytes)
    previous=None
    for si in table:
        if si>=payload_bytes-1:return None
        if previous is not None and si<=previous+1:return None
        value=struct.unpack_from('<H',image,si)[0]+delta
        if value>0xffff or value>=0xa000:return None
        struct.pack_into('<H',image,si,value);previous=si
    return bytes(image)


def mz_load(raw,load_segment):
    mz=parse_mz(raw);image=bytearray(mz['payload'])
    for at in mz['relocs']:
        struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+load_segment)&0xffff)
    return bytes(image)
