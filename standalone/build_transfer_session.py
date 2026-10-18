#!/usr/bin/env python3
"""Build exact native session fragments with explicit source-owned fixture IO."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-session';OUT.mkdir(parents=True,exist_ok=True);MODULE=ROOT/'reconstruction/transfer_session'
proof=json.loads((MODULE/'provenance.json').read_text());sources=[MODULE/u['source'] for u in proof['units']]
for unit in proof['units']:
 output=OUT/(Path(unit['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/unit['source']),'-o',str(output)],check=True);raw=output.read_bytes();assert len(raw)==unit['bytes'] and hashlib.sha256(raw).hexdigest()==unit['sha256']
sources+=[ROOT/'reconstruction/transfer_receive/cancel.asm',ROOT/'standalone/transfer_session_host.asm']
state=set(proof['state'].values())-{'session_context','session_payload','session_baud_table','session_baud_table_high','session_integrity_labels','session_download_prefix','session_open_mode'}
(OUT/'session_state.inc').write_text('\n'.join(f'global {n}\n{n}: dw '+('4' if n=='session_protocol' else '0') for n in sorted(state))+'\n')
(OUT/'session_externs.inc').write_text('\n') # Host and native fragments link named global state normally.
objects=[]
for path in sources:
 obj=OUT/(path.parent.name+'_'+path.stem+'.obj');objects.append(str(obj));subprocess.run(['nasm','-fobj','-DTRANSFER_SESSION_OMF','-DTRANSFER_SESSION_DIAGNOSTIC','-DTRANSFER_RECEIVE_OMF','-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(OUT)+'/',str(path),'-o',str(obj)],check=True)
(OUT/'main.c').write_text('unsigned __cdecl transfer_session_dos_test(void);int main(void){return transfer_session_dos_test();}\n')
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=transfer_session.map','-fe=SESSION.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
result={'kind':'source-only-native-session-fragments-memory-UART-nonlocal-context-fixture','binary_sha256':hashlib.sha256((OUT/'SESSION.EXE').read_bytes()).hexdigest(),'exact_session_bytes':sum(x['bytes'] for x in proof['units']),'additional_exact_double_CAN_bytes':32,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'limitations':proof['limitations']};(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built SESSION.EXE;',result['exact_session_bytes'],'exact session bytes')
