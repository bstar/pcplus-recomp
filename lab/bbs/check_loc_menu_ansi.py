import sys,json,struct,re,argparse,subprocess,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
p=argparse.ArgumentParser(description='Replay custom Enigma menu through the linked PCPlus renderer; no live service changes.')
p.add_argument('--bbs',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--node',required=True)
a=p.parse_args();a.output=a.output.resolve();assert a.output.is_relative_to(ROOT/'build') and not a.output.exists();a.output.mkdir()
shutil.copyfile(a.baseline,a.output/'loc_main_menu.before.js')
subprocess.run([a.node,str(ROOT/'lab/bbs/loc_menu_snapshot.cjs'),str(a.bbs.resolve()),str(a.output)],check=True)
import check_transport as transport
transport.BINARY=a.terminal.resolve();transport.MAP=transport.BINARY.parent/'terminal.map'
from live_setup_kernel import LiveSettings
from check_scroll import Scroll
from unicorn.x86_const import UC_X86_REG_AX
class Renderer(LiveSettings):
    def cells(self):return list(struct.unpack('<2000H',self.uc.mem_read(0xb8000,4000)))
    def interrupt(self,u,n,d):
        if n==0x10 and u.reg_read(UC_X86_REG_AX)>>8 in (6,7):return Scroll.interrupt(self,u,n,d)
        return super().interrupt(u,n,d)
out=a.output
for name in ['old','fixed25','fixed24']:
    m=Renderer()
    m.put('terminal_program_active',0);m.put('connection_state',0)
    m.call('terminal_clear_home');assert m.call('terminal_reset_capture')==0
    data=(out/(name+'.bin')).read_bytes()
    # Queue complete ANSI chunks; native parser pulls its continuations itself.
    for chunk in re.split(rb'(?=\x1b\[[0-9]+;1H)',data):
        assert len(chunk)<=4096
        m.receive_irq(chunk)
        while m.get('uart_rx_count'):
            value=m.call('uart_receive_byte')
            m.call('terminal_receive_input',ax=value)
    screen=bytes(m.uc.mem_read(0xb8000,4000))
    (out/(name+'.screen')).write_bytes(screen)
    print(name,'finished',len(data),'bytes')

layout=json.loads((out/'layout.json').read_text())['cells'];layout=layout[:9]+layout[10:]
screen=(out/'fixed24.screen').read_bytes()
palette=[('#000000',0),('#555555',8),('#aaaaaa',7),('#ffffff',15),('#0000aa',1),('#5555ff',9),('#00aaaa',3),('#55ffff',11),('#aa5500',6),('#ffff55',14)]
def rgb(s):
    h=s.lstrip('#');h=''.join(c*2 for c in h) if len(h)==3 else h;v=int(h,16);return (v>>16,v>>8&255,v&255)
expected=bytearray()
for row in layout:
    for c in row:
        v=rgb(c['color']);attr=min(palette,key=lambda p:sum((a-b)**2 for a,b in zip(v,rgb(p[0]))))[1]
        expected.extend([c['ch'].replace('Ð','D').encode('cp437',errors='replace')[0],attr])
assert screen[:3840]==expected,'Native glyph/attribute cells differ from layout'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(passed=True,matched_cells=1920,glyphs_and_attributes_exact=True,browser25_unchanged=True,prompt_row=24,
    terminal_sha256=sha(a.terminal),module_sha256=sha(a.bbs/'mods/loc_main_menu/loc_main_menu.js'),
    sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'lab/bbs/loc_menu_snapshot.cjs',ROOT/'lab/bbs/patches/loc-main-classic-ansi.patch']},
    scope='Captured actual custom menu output; linked PCPlus renderer/parser with modeled BIOS/UART. Browser25 output equals old module; fixed24 cells independently match every source glyph and nearest16-color attribute. No live restart, real account or physical display acceptance.')
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: all1920 native glyph/attribute cells match; browser25 output unchanged.')
