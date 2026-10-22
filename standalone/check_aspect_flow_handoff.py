#!/usr/bin/env python3
"""Execute production v5 admission, preload, real UART ISR and publication."""
import argparse,json,shutil,struct
from pathlib import Path
from check_aspect_render_client import Client,q,sha
ROOT=q.ROOT


class Flow(Client):
    def __init__(self,flags=0):
        self.pre_irq_flags=[];super().__init__();self.words[1:3]=[5,50];self.words.append(flags);self.publish()

    def publish(self):
        w=self.words
        if len(w)==23:return super().publish()
        w[9]=w[3]^w[4]^w[5]^0xa510
        for i in [7,8,*range(11,24)]:w[9]^=w[i]
        self.uc.mem_write(self.desc,struct.pack('<I23H',*w))

    def _code(self,u,address,size,data):
        if address==self.symbols['uart_install_interrupt']:
            self.pre_irq_flags.append(self.get('uart_tx_paused'))
        return super()._code(u,address,size,data)

    def mode(self,mode):self.uc.mem_write(self.data_base+0xb000,b'/S1:0003:03:'+mode+b':6200:0100\0')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    for mode in (b'S',b'B'):
        for initial in (0,1):
            m=Flow(initial);m.mode(mode);assert m.open()==0 and m.get('uart_tx_paused')==initial and m.pre_irq_flags==[initial]
            assert m.call('_aspect_serial_poll')==0
            before=bytes(m.tx);assert m.call('_aspect_serial_try_write',[65])==initial
            assert bytes(m.tx)==before+(b'' if initial else b'A')
            m.receive_irq(b'\x11');assert m.get('uart_tx_paused')==0
            assert m.call('_aspect_serial_try_write',[66])==0 and bytes(m.tx).endswith(b'B')
            m.receive_irq(b'\x13');assert m.get('uart_tx_paused')==1
            before=bytes(m.tx);assert m.call('_aspect_serial_try_write',[67])==1 and bytes(m.tx)==before
            assert m.call('_aspect_serial_close')==0
            words=struct.unpack('<I23H',m.uc.mem_read(m.desc,50));assert words[10]==words[23]==1 and words[8]==0
            assert m.call('_aspect_render_finish')==0
            rows.append(dict(case='v5-'+mode.decode()+'-initial'+str(initial),passed=True))
    for flags in (0,1):
        m=Flow(flags);m.mode(b'S');assert m.open()==0;m.receive_irq(b'\x11')
        assert m.call('_aspect_serial_close')==0
        words=struct.unpack('<I23H',m.uc.mem_read(m.desc,50));assert words[10]==1 and words[23]==0
        rows.append(dict(case='v5-publishes-cleared-pause-initial'+str(flags),passed=True))
    for mode,flags in [(b'S',2),(b'B',65535),(b'N',1),(b'H',1)]:
        m=Flow(flags);m.mode(mode);assert m.open()==1 and not m.writes and not m.get('_aspect_serial_active')
        rows.append(dict(case='reject-flags-'+mode.decode()+str(flags),passed=True))
    for kind in ('size','guard','entry-overlaps-tail','descriptor-crosses-segment'):
        m=Flow();m.mode(b'S')
        if kind=='size':m.words[2]=48;m.publish()
        elif kind=='guard':m.uc.mem_write(m.desc+48,b'\x01\0')
        elif kind=='entry-overlaps-tail':m.words[19:21]=[0x130,0x6200];m.publish()
        else:
            m.uc.mem_write(0x62000+0xffd0,struct.pack('<I23H',*m.words))
            m.uc.mem_write(m.data_base+0xb000,b'/S1:0003:03:S:6200:FFD0\0')
        assert m.open()==1 and not m.writes and not m.get('_aspect_serial_active')
        rows.append(dict(case=kind,passed=True))
    for mode in (b'S',b'B'):
        m=Client();m.uc.mem_write(m.data_base+0xb000,b'/S1:0003:03:'+mode+b':6200:0100\0')
        m.uc.mem_write(m.desc+48,b'QQ');assert m.open()==0 and m.get('uart_tx_paused')==0
        m.receive_irq(b'\x13');assert m.call('_aspect_serial_close')==0
        assert m.uc.mem_read(m.desc+48,2)==b'QQ' and struct.unpack('<H',m.uc.mem_read(m.desc+22,2))[0]==1
        rows.append(dict(case='legacy-v4-no-tail-write-'+mode.decode(),passed=True))
    manifest=json.loads((q.BINARY.parent/'manifest.json').read_text())
    assert manifest['binary_sha256']==sha(q.BINARY)
    inputs={**manifest['sources'],str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
            'standalone/check_aspect_render_client.py':sha(ROOT/'standalone/check_aspect_render_client.py'),
            'standalone/check_uart.py':sha(ROOT/'standalone/check_uart.py')}
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    result=dict(passed=True,cases=rows,runner_sha256=sha(q.BINARY),inputs=inputs,
        scope=__doc__+' DOS/kernel/UART inputs and resident endpoint are modeled. Input pause is present before IRQ installation; real ISR clears/sets on XON/XOFF. Legacy v4 descriptor tail is unchanged. No actual DOS or hardware claim.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
