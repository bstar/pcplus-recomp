#!/usr/bin/env python3
"""Separate EOF-position candidate on top of the verified finite-credit patch."""
import hashlib,json,sys
from pathlib import Path


def digest(body):return hashlib.sha256(body).hexdigest()


def main():
 folder=Path(sys.argv[1]).resolve();source=folder/'zmodem.c'
 cut=json.loads((folder/'source-manifest.json').read_text())
 credit=json.loads((folder/'send-credit-manifest.json').read_text())
 assert cut['upstream_commit']==credit['upstream_commit']=='e7a825704ef5329c7ef8408749671291a85ef7f2'
 before=source.read_bytes();assert digest(before)==credit['after_sha256']
 text=before.decode();start=text.index('\nBOOL zmodem_handle_zrpos(')+1
 end=text.index('\nBOOL zmodem_handle_zack(',start);body=text[start:end]
 old='if (zm->rxd_header_pos < zm->current_file_size) {'
 assert body.count(old)==1
 body=body.replace(old,'''/* EOF is a valid restart position, including offset zero for an
         * empty file. Positions beyond EOF remain invalid. */
        if (zm->rxd_header_pos <= zm->current_file_size) {''')
 after=(text[:start]+body+text[end:]).encode();source.write_bytes(after)
 proof=dict(upstream_commit=cut['upstream_commit'],original_source_digest=cut['source_digest'],
  before_sha256=digest(before),after_sha256=digest(after),changed_function='zmodem_handle_zrpos',
  credit_manifest_sha256=digest((folder/'send-credit-manifest.json').read_bytes()),
  patcher_sha256=digest(Path(__file__).read_bytes()),
  scope='Separate candidate permitting restart exactly at EOF, including empty files. The finite-credit sender patch remains unchanged; offsets beyond EOF remain rejected. No DOS/BBS/audio acceptance follows from patching/building alone.')
 (folder/'eof-position-manifest.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
