#!/bin/sh
# Diagnostic-only read access to existing modem dumps on a separate virtio port.
set -eu
dev=/dev/virtio-ports/pcplus.trace
while [ ! -c "$dev" ]; do sleep 0.1; done
exec 3<>"$dev"
while IFS= read -r command <&3; do
    [ "$command" = DUMP ] || exit 64
    for name in modem_rx_8k.raw modem_rx.raw modem_tx.raw; do
        file=/tmp/$name
        [ -f "$file" ] || exit 65
        size=$(wc -c < "$file")
        printf '%s %s\n' "$name" "$size" >&3
        head -c "$size" "$file" >&3
    done
    printf 'DONE\n' >&3
done
