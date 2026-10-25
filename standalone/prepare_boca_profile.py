#!/usr/bin/env python3
"""Prepare a private Boca/SPA2102 profile from an identified PCPlus 2.01 PRM.

Not a build input. Never edits the original profile or writes a removable card.
The caller must identify the source format; length alone cannot identify it.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from package_special_edition import ROOT, launch

sys.path.insert(0, str(ROOT / 'src/config'))
from prm import BAUD_RATES, LegacyPrm201, SerialSettings


def prepare(source, output, com=3, irq=5, baud=19200):
    raw = source.read_bytes()
    profile = LegacyPrm201(raw)
    # Preserve modem-specific commands: no assumed Rockwell initialization and
    # no reset or persistent modem NVRAM write is added by this utility.
    profile = profile.with_serial(SerialSettings(com-1, BAUD_RATES.index(baud), 0, 1, 8))
    for key, value in [('terminal_id', 6), ('translation_mode', 0),
                       ('software_flow', 0), ('hardware_flow', 1),
                       ('modem_autobaud', 0), ('dial_timeout_seconds', 90),
                       ('abort_drop_dtr', 1)]:
        profile = profile.with_word(key, value)
    staged = bytearray(profile.to_bytes())
    base = (0x3f8, 0x2f8, 0x3e8, 0x2e8)[com-1]
    struct.pack_into('<H', staged, 0x174+2*(com-1), base)
    struct.pack_into('<H', staged, 0x184+2*(com-1), irq)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    (output / 'BOCA.PRM').write_bytes(staged)
    # Use the package's environment-preserving launcher. Numeric dial target
    # reaches SynthModem; LOC is entered at CONNECT>, after carrier is raised.
    (output / 'LOC.BAT').write_bytes(launch().replace(
        b'@PCPLUS.PRM', b'@BOCA.PRM /D:555 /I:20'))
    digest = lambda data: hashlib.sha256(data).hexdigest()
    result = dict(kind='private-boca-profile', source_sha256=digest(raw),
                  profile_sha256=digest(staged), com=com, io_base=base, irq=irq,
                  baud=baud, line='8N1', flow='RTS/CTS', terminal='ANSI/CP437',
                  changed_offsets=[i for i, (a,b) in enumerate(zip(raw, staged)) if a != b],
                  modem_commands_preserved=True, original_unchanged=True,
                  physical_modem_verified=False, card_written=False)
    assert source.read_bytes() == raw
    (output / 'profile.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True,
                        help='Explicitly identified original-format 2.01 PRM')
    parser.add_argument('--output', type=Path, required=True,
                        help='New private directory under ignored build/')
    parser.add_argument('--com', type=int, choices=range(1,5), default=3)
    parser.add_argument('--irq', type=int, choices=[3,4,5,7], default=5)
    parser.add_argument('--baud', type=int, choices=BAUD_RATES, default=19200)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT/'build') or out.exists():
        parser.error('output must be a new directory under build/')
    prepare(args.input.resolve(), out, args.com, args.irq, args.baud)
    print('Prepared BOCA.PRM and LOC.BAT at', out)
    print('Original profile preserved; modem flow-control settings need physical confirmation.')


if __name__ == '__main__':
    main()
