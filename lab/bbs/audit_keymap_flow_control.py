#!/usr/bin/env python3
"""Compare identical serial framing/pacing with RTS respected versus ignored."""
import argparse
import json
from pathlib import Path
from product_inputs import ROOT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('negative','positive','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    folders=[args.negative.resolve(),args.positive.resolve()]
    assert all(p.is_relative_to(ROOT/'build/bbs-lab/results') for p in folders)
    out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    runs=[json.loads((p/'proxy-integration.json').read_text()) for p in folders]
    modems=[json.loads((p/'modem.json').read_text()) for p in folders]
    checks=dict(same_frozen_inputs=runs[0]['product_inputs']==runs[1]['product_inputs'],
                same_generated_programs=runs[0]['generated_inputs']==runs[1]['generated_inputs'],
                explicit_control_modes=[m['flow_mode'] for m in modems]==['RTS-ignored-control','RTS-model'],
                both_raw_same_baud=all(m['raw'] and m['baud']==19200 and m['packet_delay_ms']==0 for m in modems),
                negative_overrun=(folders[0]/'EXITCODE.BIN').read_bytes()==bytes.fromhex('000000000600'),
                positive_exit_zero=(folders[1]/'EXITCODE.BIN').read_bytes()==bytes(6),
                negative_not_accepted=not runs[0]['passed'],positive_accepted=runs[1]['passed'],
                both_save_and_restore=all(r['keymap']['checks']['only_intended_KBD_edit'] and r['keymap']['checks']['exact_editor_frame'] for r in runs),
                same_final_KBD=(folders[0]/'BOARD.KBD').read_bytes()==(folders[1]/'BOARD.KBD').read_bytes())
    positive_flow=json.loads((folders[1]/'keymap-flow-audit.json').read_text())
    checks['positive_pause_independently_audited']=positive_flow['passed']
    for name,digest in runs[0]['product_inputs'].items():assert sha(ROOT/name)==digest,name
    names=['proxy-integration.json','modem.json','EXITCODE.BIN','BOARD.KBD','keymap-audit.json']
    result=dict(passed=all(checks.values()),checks=checks,
                parent_sha256=runs[1]['binary_sha256'],helper_sha256=runs[1]['keymap']['helper_sha256'],
                captures={str((folder/name).relative_to(ROOT)):sha(folder/name) for folder in folders for name in names},
                sources={str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__))},
                scope='One stock Synchronet paired control: same application/helper/programs, framing and single-byte pacing; only --ignore-rts changes delivery gating. Negative exits6 after save/frame return; positive restores/edits/aborts normally. Supports RTS-gating cause in this model, not physical modem equivalence or universal reliability.')
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['passed'],checks
    print('PASS matched RTS control: ignored exits6; respected saves/returns/edits with exit0')


if __name__=='__main__':main()
