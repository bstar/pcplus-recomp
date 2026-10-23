#!/usr/bin/env python3
"""Replay the ordinary editor's actual sound field with caller-owned buffers."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_INS_IN,UC_X86_INS_OUT,UC_X86_REG_ES
from dos_image import DosImage
from check_setup_model import image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/setup-notice-sound'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mouse',action='store_true');args=parser.parse_args()
    if args.mouse:OUT=ROOT/'build/setup-mouse-notice-sound'
    field=50 if args.mouse else 48
    rows=[]
    def forbidden(*args):raise AssertionError('Pure editor field attempted a DOS/BIOS/port operation')
    for value in [0,1,65535]:
        m=DosImage(OUT/'PRMEDIT.EXE',OUT/'setup.map');m.uc.reg_write(UC_X86_REG_ES,m.ds)
        m.uc.hook_add(UC_HOOK_INTR,forbidden)
        for ins in [UC_X86_INS_IN,UC_X86_INS_OUT]:m.uc.hook_add(UC_HOOK_INSN,forbidden,None,1,0,ins)
        a,b,t,bad=0x8000,0x8500,0x8a00,0x8b00
        baseline=bytearray(image());struct.pack_into('<H',baseline,0x1bc,value)
        if args.mouse:struct.pack_into('<HH',baseline,0x4e4,8,4)
        m.uc.mem_write(m.data_base+a,bytes(baseline));m.uc.mem_write(m.data_base+b,bytes(baseline))
        info=m.call('_setup_field',[field]);label=int.from_bytes(m.uc.mem_read(m.data_base+info,2),'little')
        assert bytes(m.uc.mem_read(m.data_base+label,14)).split(b'\0')[0]==b'Program sound'
        assert m.call('_setup_get',[b,field,t,64])==0
        assert bytes(m.uc.mem_read(m.data_base+t,64)).split(b'\0')[0]==str(value).encode()
        assert bytes(m.uc.mem_read(m.data_base+b,1264))==bytes(baseline),'Viewing normalized a stored value'
        for text in [b'0',b'1',b'65535',b'-1',b'65536',b'',b'junk']:
            m.uc.mem_write(m.data_base+b,bytes(baseline));m.uc.mem_write(m.data_base+t,text+b'\0')
            status=m.call('_setup_set',[a,b,field,t],limit=500000)
            valid=text in [b'0',b'1',b'65535'];assert status==(0 if valid else 2)
            expected=bytearray(baseline)
            if valid:struct.pack_into('<H',expected,0x1bc,int(text))
            assert bytes(m.uc.mem_read(m.data_base+b,1264))==bytes(expected)
            assert bytes(m.uc.mem_read(m.data_base+a,1264))==bytes(baseline)
            if valid:assert m.call('_setup_validate',[b,bad],limit=2000000)==0
            rows.append(dict(stored=value,edit=text.decode(),accepted=valid))
    manifest=json.loads((OUT/'manifest.json').read_text());assert manifest['field_count']==field+1 and manifest['binary_sha256']==sha(OUT/'PRMEDIT.EXE')
    sources={**manifest['sources'],**{n:sha(ROOT/n) for n in ['standalone/check_program_sound_editor.py','standalone/check_setup_model.py','standalone/check_modem_import.py','standalone/dos_image.py']}}
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=True,cases=rows,field_count=field+1,mouse=args.mouse,binary_sha256=manifest['binary_sha256'],sources=sources,scope=__doc__+' Ordinary editor EXE, no product patch. Exact whole-image comparisons prove only the selected sound word changes. Field API replay models caller buffers; no interactive save or physical DOS/BIOS/port activity.')
    (OUT/'sound-editor-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))
if __name__=='__main__':raise SystemExit(main())
