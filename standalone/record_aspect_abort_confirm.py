#!/usr/bin/env python3
"""Bind native component comparisons, REA instruction coverage and original-free products."""
import argparse,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('original','source-proof','evidence-directory','cohort','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();cohort=a.cohort.resolve();target=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert target.is_relative_to(ROOT/'docs/validation') and not target.exists()
    proof_path=ROOT/'reconstruction/script_abort/provenance.json';proof=read(proof_path)
    original=a.original.resolve();assert sha(original)==proof['source_sha256'];blob=original.read_bytes()
    base=ROOT/'build/aspect-abort-confirm';native=read(base/'original-checks.json')
    source=a.source_proof.resolve();fresh=read(source/'result.json')
    assert source.is_relative_to(ROOT/'build') and fresh['passed'] and fresh['original_inputs']==[]
    assert not (source/'tree/analysis').exists()
    assert native['passed'] and native['cases']==native['original_comparisons']==fresh['cases']==4610
    assert native['case_results_sha256']==fresh['case_results_sha256']
    assert native['checker_sha256']==sha(ROOT/'standalone/check_aspect_abort_confirm.py')
    assert native['source_sha256']==sha(ROOT/'reconstruction/script_abort/confirm.asm')
    assert native['products']==fresh['products'] and len(fresh['products'])==4
    selected={Path(__file__).resolve(),proof_path,base/'original-checks.json',ROOT/'nix/flake.lock'}
    for name,digest in fresh['sources'].items():
        assert sha(ROOT/name)==sha(source/'tree'/name)==digest,name
        selected.add(ROOT/name)
    for name,digest in fresh['products'].items():
        assert sha(base/name)==sha(source/'tree/build/aspect-abort-confirm'/name)==digest,name
        selected.add(base/name)
    observed=set(native['instruction_addresses']);expected=set();evidence_ids=[]
    for row,name in zip(proof['ranges'],('confirm','yesno')):
        product=base/f"unit-{row['unit']}.bin"
        assert product.read_bytes()==blob[row['file_offset']:row['file_offset']+row['bytes']]
        assert sha(product)==row['sha256']
        evidence=a.evidence_directory.resolve()/(name+'.evidence.json');d=read(evidence)
        assert d['evidence_id']==row['evidence_id'] and d['subject']['digest']['sha256']==proof['source_sha256']
        assert d['normalized_result']['procedure']['body']['total_bytes']==row['bytes']
        expected.update(int(line.split(': ',1)[0],16)-0x10000 for line in d['normalized_result']['assembly'])
        mapping=a.evidence_directory.resolve()/(name+'-mapping.evidence.json');m=read(mapping)
        assert m['evidence_id']==row['mapping_evidence_id'] and m['normalized_result']['file_offset']==row['file_offset']
        evidence_ids.extend((d['evidence_id'],m['evidence_id']));selected.update((evidence,mapping))
    assert len(expected)==91 and expected<=observed
    selected.update(p for p in source.rglob('*') if p.is_file())
    # Keep the failed relocation-independent build attempt. Its CPU outcomes
    # match, but absolute source filenames made the two OMF headers differ.
    for earlier in (base/'source-proof-01',base/'absolute-path-build-01'):
        assert earlier.is_dir();selected.update(p for p in earlier.rglob('*') if p.is_file())
    assert not (base/'source-proof-01/result.json').exists()
    cohort.mkdir();files={}
    for p in sorted(selected):
        assert p.is_relative_to(ROOT) and p!=original
        copy=cohort/p.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,copy)
        assert sha(copy)==sha(p);files[str(copy.relative_to(ROOT))]=sha(copy)
    result=dict(passed=True,recovered_instruction_bytes=197,component_cases=4610,
        original_comparisons=4610,native_instruction_addresses_covered=91,
        original_free_products=fresh['products'],original_free_build_inputs=fresh['sources'],
        native_source_sha256=proof['source_sha256'],evidence_ids=evidence_ids,
        production_abort_confirmation_accepted=False,full_F02_accepted=False,full_F13_accepted=False,
        failed_reproducibility_attempt_retained=True,custody_sha256=files,sealer_sha256=sha(Path(__file__)),
        scope='Source-built native4E6B confirmation wrapper plus6DDE yes/no helper. Every low-byte key, two high-byte forms, defaultNo/Yes, three cursor modes and wrapper composition; non-Boolean Enter defaults also checked. All91 source instruction addresses execute. Window drawing, cursor, keyboard and bell services are modeled; OMF products are assembled, not yet linked into a production DOS owner. Matching original-file ranges and an isolated tree with no originals verify byte identity and four reproducible products. The first OMF reproducibility attempt remains failed because absolute source filenames entered its headers; relative source invocation fixes that without altering native code. Production still cancels immediately on outer Escape. Live serial, actual DOS modal interaction and all full application/physical gates remain unaccepted.')
    with target.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,component_cases=4610,original_free_products=4,custody_files=len(files))))

if __name__=='__main__':main()
