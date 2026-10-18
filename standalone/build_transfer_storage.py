#!/usr/bin/env python3
"""Compose recovered receiver with scheduled UART and actual DOS file backend."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-storage'
args=[sys.executable,str(ROOT/'standalone/build_transfer_session_composite.py'),'--output-dir',str(OUT),'--adapter',str(ROOT/'standalone/transfer_storage_io.asm'),'--driver',str(ROOT/'standalone/transfer_storage_host.c')]
for name in ['download_file.c','native_file_bridge.c']:args+=['--c-source',str(ROOT/'src/transfer'/name)]
args+=['--c-source',str(ROOT/'standalone/transfer_storage_fs.c')]
subprocess.run(args,check=True)
p=OUT/'manifest.json';d=json.loads(p.read_text());d['kind']='one-owner-native-receiver-actual-DOS-staged-storage-controlled-UART';d['limitations']=['One native receive owner, handshake, checksum/block validation, retry/context, periodic10240-byte and EOT file controllers execute with maintained real DOS file callbacks.','Scheduled synthetic UART/time/UI fixture; no physical serial timing, actual UART port, peer BBS or terminal UI claim.','Native final write/close failures remain in exact owner; maintained storage first-error and explicit post-owner install gate prevent failed local file installation.','Native ACK-before-final-file-commit remains a wire-policy gap.','Ordinary XMODEM unknown length retains complete padded blocks; batch/window/streaming metadata and otherprotocols remain open.'];d['sources']['src/transfer/download_fs.c']=hashlib.sha256((ROOT/'src/transfer/download_fs.c').read_bytes()).hexdigest();d['sources']['standalone/transfer_session_composite_io.asm']=hashlib.sha256((ROOT/'standalone/transfer_session_composite_io.asm').read_bytes()).hexdigest();p.write_text(json.dumps(d,indent=2)+'\n');print('Built real-DOS-storage TRANSFER.EXE',d['binary_sha256'])
