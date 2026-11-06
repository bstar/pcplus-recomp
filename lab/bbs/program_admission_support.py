"""Build an optional passive ASPECT launch-result witness into the UMB observer."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def instrument(source, binary):
    binary = Path(binary)
    symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',
        binary.with_name('terminal.map').read_text(), re.M | re.I)}
    fields = {'PSP': 'process_psp', 'PROGRAM_KIND': 'terminal_program_kind',
              'PROGRAM_STATUS': 'terminal_program_status', 'PROCESS_STATUS': 'process_status',
              'DOS_ERROR': 'process_dos_error', 'CHILD_STATUS': 'process_child_status',
              'KEEP': 'process_keep_paragraphs', 'RESULT': 'terminal_program_result'}
    segment = symbols['process_psp'][0]
    assert all(symbols[n][0] == segment for n in fields.values())
    values = {n: symbols[s][1] for n, s in fields.items()}
    values.update(DATA_SEGMENT=segment, ISR_SEGMENT=symbols['uart_receive_interrupt'][0],
                  ISR_OFFSET=symbols['uart_receive_interrupt'][1])
    defines = ''.join(f'%define ADMISSION_{n} {v}\n' for n, v in values.items())
    marker = 'resident_end:\n'
    assert source.count(marker) == 1
    source = source.replace(marker, (ROOT / 'standalone/program_admission_watch.inc').read_text() + '\n' + marker)
    marker = '\ninstall:\n'
    assert source.count(marker) == 1
    source = source.replace(marker, marker + ' call admission_install\n')
    marker = ' cmp word [es:di],REPORT_MAGIC\n jne failed\n'
    assert source.count(marker) == 1
    # Preserve the ES:DI report binding around mainline DOS collection.
    source = source.replace(marker, marker + ' push es\n push di\n call admission_collect\n pop di\n pop es\n')
    return defines + source
