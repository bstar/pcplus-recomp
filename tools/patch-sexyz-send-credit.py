#!/usr/bin/env python3
"""Apply a finite receive-credit sender candidate to the verified source cut."""
import hashlib,json,sys
from pathlib import Path


def digest(body):return hashlib.sha256(body).hexdigest()


def main():
 folder=Path(sys.argv[1]).resolve();source=folder/'zmodem.c';manifest=json.loads((folder/'source-manifest.json').read_text())
 assert manifest['upstream_commit']=='e7a825704ef5329c7ef8408749671291a85ef7f2'
 before=source.read_bytes();assert digest(before)==manifest['files']['zmodem.c']
 text=before.decode();start=text.index('\nint zmodem_send_from(')+1;end=text.index('\nBOOL zmodem_send_file(',start)
 body=text[start:end];changes=[]
 def replace(old,new,count=1):
  nonlocal body
  assert body.count(old)==count,(old,body.count(old));body=body.replace(old,new);changes.append(dict(needle=old,count=count))
 replace('unsigned subpkts_sent = 0;','unsigned subpkts_sent = 0;\n\tunsigned block_limit;')
 replace('len = fread(zm->tx_data_subpacket, sizeof(BYTE), zm->block_size, fp);','''/* A finite ZRINIT credit bounds both packets and the unacknowledged
         * synchronous group. Decide the actual read size before fread; a
         * credit-clipped full read is not end of file. */
        block_limit = zm->block_size;
        if (zm->recv_bufsize != 0) {
            unsigned available;
            if (buf_sent >= zm->recv_bufsize)
                return ZFERR;
            available = zm->recv_bufsize - buf_sent;
            if (block_limit > available)
                block_limit = available;
        }
        len = fread(zm->tx_data_subpacket, sizeof(BYTE), block_limit, fp);''')
 replace('len < zm->block_size','len < block_limit',3)
 replace('zm->max_window_size / zm->block_size / 4','zm->max_window_size / block_limit / 4')
 replace('else    /* Send a ZCRCW frame */\n\t\t\t\t\tbuf_sent = 0;',
         'else    /* Credit is released after the matching ZACK below. */\n\t\t\t\t\ttx_type = ZCRCW;')
 replace('\t\tlprintf(zm, LOG_DEBUG, "%lu Sending %s data subpacket',
         '''        /* Also checkpoint a credit-filling recovery packet. */
        if (zm->recv_bufsize && buf_sent + len == zm->recv_bufsize && len == block_limit)
            tx_type = ZCRCW;

\t\tlprintf(zm, LOG_DEBUG, "%lu Sending %s data subpacket''')
 replace('buf_sent += len;','buf_sent = tx_type == ZCRCW ? 0 : buf_sent + len;')
 after=(text[:start]+body+text[end:]).encode();source.write_bytes(after)
 proof=dict(upstream_commit=manifest['upstream_commit'],original_source_digest=manifest['source_digest'],
  file='zmodem.c',before_sha256=digest(before),after_sha256=digest(after),changed_function='zmodem_send_from',changes=changes,
  patcher_sha256=digest(Path(__file__).read_bytes()),scope='Isolated sender candidate only. Enforce finite ZRINIT packet and synchronous-group credit, compare EOF against actual read limit, and release credit after verified ZCRCW acknowledgment. No change to default zero-credit/unlimited capability, receive/finish implementation, DOS client, live BBS or compatibility acceptance.')
 (folder/'send-credit-manifest.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
