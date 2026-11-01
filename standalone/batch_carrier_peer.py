"""Independent async YMODEM/ZMODEM peers for virtual-carrier loss fixtures.

Only remote wire and owned fixture files are accessed; no product state writes.
"""
import asyncio,binascii,hashlib
from check_zmodem_wire import header as z_header,packet as z_packet


def zh(kind,position=0,fmt=66):
    return z_header(bytes([kind])+position.to_bytes(4,'little'),fmt,0)


def yf(data,number):
    assert len(data) in (128,1024)
    return bytes((1 if len(data)==128 else 2,number,255-number))+data+binascii.crc_hqx(data,0).to_bytes(2,'big')


async def run(reader,writer,item,event,folder,mode,upload_body):
    pending=bytearray()
    async def receive():
        data=await reader.read(4096)
        if not data:raise ConnectionError('Carrier lost before planned batch boundary')
        item['received'].extend(data);pending.extend(data)
    async def expect(want):
        while len(pending)<len(want):await receive()
        actual=bytes(pending[:len(want)]);del pending[:len(want)]
        assert actual==want,('Unexpected batch wire',actual.hex(),want.hex())
    async def send(data):
        writer.write(data);await writer.drain()
    async def ypacket():
        while not pending:await receive()
        assert pending[0] in (1,2),('Unexpected YMODEM leader',pending[:16].hex())
        size=128 if pending[0]==1 else 1024
        while len(pending)<size+5:await receive()
        frame=bytes(pending[:size+5]);del pending[:size+5]
        assert frame[1]^frame[2]==255 and binascii.crc_hqx(frame[3:-2],0)==int.from_bytes(frame[-2:],'big')
        return frame[1],frame[3:-2]
    protocol=mode['protocol'];upload=mode['upload'];partial=mode['partial'];retained=mode.get('retained',False)
    fmt=67
    item['batch']={'protocol':protocol,'metadata':False,'data_frames':0,'ACKed_data_frames':0,'retained_file':False}
    detail=item['batch']
    if upload:
        if protocol==1:
            # Receiver C can precede local startup; repeat only until its header.
            while not pending or pending[0] not in (1,2):
                await send(b'C')
                try:await asyncio.wait_for(receive(),.25)
                except asyncio.TimeoutError:continue
                while pending and pending[0] not in (1,2):del pending[0]
            sequence,body=await ypacket();assert sequence==0
            name,metadata=body.split(b'\0',1)
            assert name==b'SEND.BIN' and int(metadata.split(b'\0',1)[0].split()[0])==len(upload_body)
        else:
            await expect(zh(0));await send(zh(1,0x22000000))
            metadata=(b'SEND.BIN\0'+str(len(upload_body)).encode()+b' 0\0').ljust(128,b'\0')
            await expect(zh(4,0x01000000,fmt)+z_packet(metadata,fmt,107,0))
        detail['metadata']=True;event('batch-upload-metadata')
        if partial:
            await send(b'\x06C' if protocol==1 else zh(9))
            offset=0
            for number in (1,2):
                if protocol==1:
                    sequence,body=await ypacket();assert sequence==number
                    assert body==upload_body[offset:offset+len(body)]
                else:
                    body=upload_body[offset:offset+1024]
                    await expect(zh(10,offset,fmt)+z_packet(body,fmt,107,0))
                offset+=len(body);detail['data_frames']+=1;event('batch-upload-frame-'+str(number))
                if number==1:
                    await send(b'\x06' if protocol==1 else zh(3,offset))
                    detail['ACKed_data_frames']+=1;event('batch-upload-ACK-1')
    else:
        first=b'FIRST COMPLETE FILE\r\n'
        if protocol==1:await expect(b'C')
        else:await expect(zh(1,0x23002000))
        async def offer(name,size):
            metadata=name+b'\0'+str(size).encode()+b'\0'
            if protocol==1:
                await send(yf(metadata.ljust(128,b'\0'),0));await expect(b'\x06C')
            else:
                await send(zh(4,0,fmt)+z_packet(metadata,fmt,107,0));await expect(zh(9))
        async def data_block(body,number,offset):
            if protocol==1:
                await send(yf(body,number));await expect(b'\x06')
            else:
                await send(zh(10,offset,fmt)+z_packet(body,fmt,107,0));await expect(zh(3,offset+len(body)))
        if retained:
            await offer(b'FIRST.BIN',len(first))
            await data_block(first.ljust(128,b'\x1a') if protocol==1 else first,1,0)
            if protocol==1:
                await send(b'\x04');await expect(b'\x15');await send(b'\x04');await expect(b'\x06C')
            else:await send(zh(11,len(first),fmt));await expect(zh(1,0x23002000))
            assert (folder/'RECV/FIRST.BIN').read_bytes()==first
            detail['retained_file']=True;detail['retained_sha256']=hashlib.sha256(first).hexdigest();event('first-file-installed')
        await offer(b'ONE.BIN',12288);detail['metadata']=True;event('batch-receive-metadata')
        if partial:
            received=bytes(65+i%26 for i in range(9216))
            for number in range(1,10):
                offset=(number-1)*1024
                await data_block(received[offset:offset+1024],number,offset)
                detail['data_frames']+=1;detail['ACKed_data_frames']+=1;event('batch-download-ACK-'+str(number))
            staged=(folder/'RECV/PCRX.$$$').read_bytes()
            detail['stage_before_drop']={'bytes':len(staged),'exact':staged==received[:len(staged)]}
            assert 8192<=len(staged)<=9216 and detail['stage_before_drop']['exact']
    assert not pending,('Unexpected trailing batch wire',pending.hex())
