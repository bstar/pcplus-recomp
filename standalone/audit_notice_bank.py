#!/usr/bin/env python3
"""Audit notice code-bank ABI, independent DOS/UART streams and parent coexistence."""
import argparse,hashlib,itertools,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def symbols(path):
    return {name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',path.read_text(),re.M|re.I)}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['dos','uart','parent','near-dos','near-uart','near-source','window-dos','cohort','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();folders=[args.dos.resolve(),args.uart.resolve(),args.parent.resolve(),args.near_dos.resolve(),args.near_uart.resolve(),args.near_source.resolve(),args.window_dos.resolve()];dos,uart,parent,near_dos,near_uart,near_source,window_dos=folders
    cohort=args.cohort.resolve();output=args.output.resolve()
    assert all(p.is_relative_to(ROOT/'build') for p in [*folders,cohort]) and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    cohort.mkdir();selected={Path(__file__)}
    bases=[ROOT/'build/notice-bank',ROOT/'build/notice-bank-uart'];manifests=[read(b/'manifest.json') for b in bases]
    sources={};products={};placement=[];calls=[]
    for base,m,binary in zip(bases,manifests,['NOTICE','NUART']):
        assert m['original_inputs']==[] and m['banked'] and m['owner_normal_compiled']
        for p,h in m['sources'].items():assert sha(ROOT/p)==h;sources[p]=h
        assert sha(base/(binary+'.EXE'))==m['binary_sha256']
        products[str((base/(binary+'.EXE')).relative_to(ROOT))]=m['binary_sha256']
        listing=base/(binary+'.map');s=symbols(listing);bank=s['_notice_show'][0];near=s['_notice_bank_service'][0]
        assert bank!=near and s['main_'][0]==near
        for name in ['_notice_recover','_notice_active','_notice_window_open','_notice_window_close','_notice_checkpoint_call','_notice_checkpoint_abort','_notice_call_native','_window_platform_allocate','window_save','window_restore']:
            assert s[name][0]==bank,name
        for name,(segment,_) in s.items():
            if name.startswith('_notice_bank_'):assert segment==near,name
        for old,new in m['aliases'].items():
            if old in s:assert s[old][0]!=bank,old
            if new in s:assert s[new][0]==bank or 'state' in new or new in ['notice_display_legacy','notice_display_columns','notice_display_segment','notice_display_bytes','notice_display_cells','notice_display_status_port','notice_text_video_segment','notice_text_cga_status_port','notice_transfer_dos_clock_sample'],new
        # Decode both C objects: near calls/jumps stay in this bank; every far
        # external call names a bank API or explicit near-platform adapter.
        for name in ['runtime','owner','owner-normal']:
            obj=base/(name+'.obj');dis=cohort/(base.name+'-'+name+'.dis')
            subprocess.run(['wdis','-e','-l='+str(dis),str(obj)],check=True)
            text=dis.read_text().split('\nSegment: CONST',1)[0]
            labels=set(re.findall(r'^[0-9a-f]{4}\s+([\w$]+):\s*$',text,re.M|re.I));count=0
            for address,encoded,op,target in re.findall(r'^([0-9a-f]{4})\s+((?:[0-9a-f]{2}\s+)+)(call|jmp)\s+(\S+)',text,re.M|re.I):
                opcode=encoded.split()[0].upper();count+=1
                if opcode in ['9A','EA']:
                    assert target.startswith(('_notice_bank_','_notice_window_')) and target in s,(name,target)
                elif opcode in ['E8','E9','EB']:
                    assert target in labels or (target in s and s[target][0]==bank),(name,target)
                else:raise AssertionError((name,address,op,target,'unreviewed indirect transfer'))
            assert count
            calls.append(dict(object=str(obj.relative_to(ROOT)),sha256=sha(obj),transfers=count,listing_sha256=sha(dis)))
        placement.append(dict(binary=binary,bank_segment=bank,callback_segment=near))
        selected.update([listing,base/'manifest.json',base/(binary+'.EXE')])
    # A fresh tree contains declared sources only, never an existing build or
    # original executable. Both manifests and every component product agree.
    with tempfile.TemporaryDirectory(prefix='pcplus-notice-bank-') as name:
        stage=Path(name)
        for path,h in sources.items():
            dest=stage/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,dest)
        with (cohort/'source-build.log').open('w') as log:subprocess.run(['python3',str(stage/'standalone/build_notice_bank.py')],cwd=stage,stdout=log,stderr=log,check=True)
        for base,m in zip(bases,manifests):assert read(stage/base.relative_to(ROOT)/'manifest.json')==m
        for name,h in manifests[0]['window_products'].items():products['build/notice-window/'+name]=h
        for name,h in products.items():assert sha(ROOT/name)==sha(stage/name)==h
    d=read(dos/'result.json');u=read(uart/'result.json');p=read(parent/'result.json')
    assert d['passed'] and d['assertions']==583 and d['allocations']==d['frees']==69 and all(d['checks'].values())
    assert (dos/'OUTPUT.TXT').read_text().strip()=='NOTICE PASS 583 checks 69 allocations 69 frees'
    assert sha(dos/'NOTICE.EXE')==manifests[0]['binary_sha256']
    for name,h in d['inputs'].items():assert sha(ROOT/name)==h
    for name,h in d['captures_sha256'].items():assert sha(dos/name)==h
    assert u['passed'] and len(u['cases'])==16 and {(r['port'],r['flow'],r['mode']) for r in u['cases']}==set(itertools.product([1,2],'NSHB','NE'))
    payload=bytes(i for i in range(256) if i not in (17,19))*2
    for r in u['cases']:
        folder=ROOT/r['folder'];assert folder.is_relative_to(uart) and r['passed'] and all(r['checks'].values())
        assert r['assertions']==538 and r['maximum']==508 and r['callbacks']>1
        assert sha(folder/'NUART.EXE')==manifests[1]['binary_sha256'] and (folder/'RX.BIN').read_bytes()==payload
        peer=read(folder/'peer.json');assert not peer['errors']
        events=peer['events'];assert all(a['seconds']<=b['seconds'] for a,b in zip(events,events[1:]))
        wire=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        assert wire==(folder/'wire.bin').read_bytes()==(b'\x11RPF\x13' if r['flow'] in 'SB' else b'RPF')
        sent=[bytes.fromhex(e['hex']) for e in events if e['kind']=='send-completed']
        assert sent==[(b'\x13'+payload+b'\x11') if r['flow'] in 'SB' else payload,b'READY!']
        assert events[-1]['kind']=='EOF' and sum(e['kind']=='EOF' for e in events)==1
        for name,h in r['captures_sha256'].items():assert sha(folder/name)==h
    for name,h in u['inputs'].items():assert sha(ROOT/name)==h
    assert p['passed'] and len(p['cases'])==13 and all(r['passed'] for r in p['cases'])
    for name,h in p['source_hashes'].items():assert sha(ROOT/name)==h
    app=ROOT/'build/aspect-notice-parent';am=read(app/'manifest.json');assert am['experimental_notice_bank_linked'] and not am['notice_PROGRAM_binding_accepted']
    assert sha(app/'ASPECT.EXE')==am['binary_sha256']==p['child_sha256']
    sm=symbols(app/'ASPECT.map');assert sm['_notice_show'][0]!=sm['main_'][0] and sm['_notice_bank_service'][0]==sm['main_'][0]
    segment=re.search(r'^_TEXT\s+CODE\s+\S+\s+[0-9a-f]+:([0-9a-f]+)\s+([0-9a-f]+)',(app/'ASPECT.map').read_text(),re.M|re.I)
    spare=65536-int(segment[1],16)-int(segment[2],16);assert spare>0
    nd=read(near_dos/'result.json');nu=read(near_uart/'result.json');nf=read(near_source/'result.json')
    assert nd['passed'] and nd['assertions']==583 and nd['allocations']==nd['frees']==69
    assert sha(near_dos/'NOTICE.EXE')==sha(ROOT/'build/notice/NOTICE.EXE')
    assert nu['passed'] and len(nu['cases'])==16 and all(r['passed'] and all(r['checks'].values()) for r in nu['cases'])
    assert {(r['port'],r['flow'],r['mode']) for r in nu['cases']}==set(itertools.product([1,2],'NSHB','NE'))
    for r in nu['cases']:
        folder=ROOT/r['folder'];assert folder.is_relative_to(near_uart)
        assert r['assertions']==538 and r['maximum']==508 and (folder/'RX.BIN').read_bytes()==payload
        assert sha(folder/'NUART.EXE')==sha(ROOT/'build/notice-uart/NUART.EXE')
        for name,h in r['captures_sha256'].items():assert sha(folder/name)==h
    assert nf['passed'] and nf['source_files']==63 and len(nf['products'])==33
    for name,h in nf['products'].items():assert sha(ROOT/name)==h
    for folder,report in [(near_dos,nd),(near_uart,nu),(near_source,nf)]:
        for name,h in report['inputs'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    for name,h in nd['captures_sha256'].items():assert sha(near_dos/name)==h
    wd=read(window_dos/'result.json');assert wd['passed'] and wd['assertions']==771 and all(wd['checks'].values())
    assert sha(window_dos/'WINDOW.EXE')==products['build/notice-window/WINDOW.EXE']
    for name,h in wd['inputs'].items():assert sha(ROOT/name)==h;selected.add(ROOT/name)
    for name,h in wd['captures_sha256'].items():assert sha(window_dos/name)==h
    selected.update(ROOT/path for path in sources)
    selected.update([app/'ASPECT.EXE',app/'ASPECT.map',app/'manifest.json'])
    selected.update(ROOT/path for path in p['source_hashes'])
    selected.update(ROOT/path for path in d['inputs']);selected.update(ROOT/path for path in u['inputs'])
    for folder in folders:selected.update(path for path in folder.rglob('*') if path.is_file())
    kept={}
    for path in sorted(selected):
        dest=cohort/'accepted'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        assert sha(path)==sha(dest);kept[str(dest.relative_to(ROOT))]=sha(dest)
    result=dict(passed=True,banked_notice_component_accepted=True,production_parent_link_accepted=True,PROGRAM_binding_accepted=False,full_application_accepted=False,notice_DOS_assertions=583,UART_cases=16,UART_assertions=8608,parent_workflows=13,parent_near_CODE_spare=spare,source_files=len(sources),products=products,placement=placement,C_object_transfers=calls,source_inputs=sources,parent_binary_sha256=p['child_sha256'],custody_sha256=kept,auditor_sha256=sha(Path(__file__)),scope='Complete notice/window/native helpers run in a separate DOS CS with explicit far CRT/callback bridges, isolated helper exports and bank-local recovery.583 real DOS video/cleanup checks and16 actual UART cases retain508 peer bytes before READY!.33 component products reproduce from declared sources;13 attached parent PROGRAM workflows prove production-bank coexistence only. Notice error/fault paths are not yet connected to PROGRAM. Normal105-slot application unchanged. Original sound/macros, arbitrary outer nonlocal faults, other views, BBS binding and physical hardware remain open.')
    result.update(near_regression_DOS_assertions=583,near_regression_UART_assertions=8608,window_regression_assertions=771,near_regression_products=nf['products'])
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','source_files','parent_near_CODE_spare','parent_workflows']}))
if __name__=='__main__':main()
