#!/usr/bin/env python3
"""Rebuild the paused ASIO-overlay development checkpoint from committed source.

Regenerates the products named in docs/CODEX_HANDOFF_PCPLUS_SCREEN_COMMANDS.md
after build/ has been removed, and verifies each against its recorded SHA256.
Child flags that were only stored in the (deleted) manifests are recovered by
trying the valid combinations and accepting only an exact hash match.

Run inside the pinned toolchain:  ./tools/dev --command python3 tools/rebuild-asio-checkpoint.py
Uses no original executable. Intermediate builds are removed once matched.
"""
import hashlib, itertools, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
RECIPE = json.loads((ROOT / 'standalone/keymap_connection_candidate_recipe.json').read_text())

EXPECTED = {
    'parent': '7f5b3b0303eac3f4e4a1ee1bb15715015221ec6a656ad128830045de1c5619d5',
    'compiler': 'ce833af2eb8bf56acb61ee89b7a5f659d668882e5530cfe65fe8c2a901e2f459',
    'child_base': 'a46cabb419da041539dbc4ca91d8fadeaa0ba39f4e55c62dde6cd9cb2a0af344',
    'child_overlay': '1a0369887a08084365cbd04dc3f41daa2545088b5a01382f22d3ee9179519fa4',
    'asio_overlay': '47a3a7f961a67b0fda1e916e1e63c35e65a5d984b56cabb267e309f156f07004',
}
TARGET = {
    'parent': BUILD / 'screen-parent-v6-20261119',
    'compiler': BUILD / 'connection-compiler-v1-20261118',
    'child_overlay': BUILD / 'screen-child-overlay-v4-20261119',
    'asio_overlay': BUILD / 'asio-shared-overlay-v1-20261119',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args, log):
    with log.open('a') as handle:
        handle.write('\n$ ' + ' '.join(map(str, args)) + '\n'); handle.flush()
        return subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, stdout=handle, stderr=handle).returncode


def child_call(output, flags):
    opts = dict(parent_render=True, notice_bank=True, notice_sound=True, notice_input=True, notice_help=True,
                help_resource=True, serial_bank=True, register_handoff=True, custom_irq=True, get_display=True,
                get_policy=True, get_vm=True, near_globals=True, compiler_parent_lease=True, overlay_ready=True,
                directory_baud=True, directory_fields=True, directory_proto=True, clock_builtins=True,
                terminal_builtins=True, aspect_hitkey=True, aspect_state_builtins=True, aspect_screen_commands=True,
                **RECIPE['aspect_options'], **flags)
    code = ('import sys;from pathlib import Path;sys.path.insert(0,"standalone");'
            'from build_aspect_process import main;main(output=Path(%r),**%r)' % (str(output), opts))
    return ['-c', code]


def main():
    BUILD.mkdir(exist_ok=True)
    log = BUILD / 'rebuild-asio-checkpoint.log'
    result = {}

    # Parent TERMINAL.EXE (capability27).
    base_flags = [*RECIPE['terminal_flags'], '--aspect-get-display', '--aspect-get-policy', '--compiler-lease-bridge',
                  '--aspect-terminal-query', '--aspect-hitkey', '--aspect-state-builtins', '--aspect-screen-commands']
    if not (TARGET['parent'] / 'TERMINAL.EXE').exists():
        for extra in ([], ['--chat-send-mode']):
            out = BUILD / 'rebuild-parent-try'
            shutil.rmtree(out, ignore_errors=True)
            if run(['standalone/build_terminal.py', *base_flags, *extra, '--output-dir', out], log) == 0 \
                    and sha(out / 'TERMINAL.EXE') == EXPECTED['parent']:
                out.rename(TARGET['parent']); result['parent_flags'] = extra; break
            print('parent mismatch with', extra or 'no extra flags', flush=True)
        else:
            sys.exit('parent: no flag set reproduced ' + EXPECTED['parent'])
    print('parent OK', flush=True)

    # Development GET compiler (current source).
    if not (TARGET['compiler'] / 'ASPCOMP.EXE').exists():
        assert run(['standalone/build_aspect_compiler_dos.py', '--get', '--connection', '--output', TARGET['compiler']], log) == 0
        got = sha(TARGET['compiler'] / 'ASPCOMP.EXE')
        if got != EXPECTED['compiler']:
            sys.exit('compiler: got %s, expected %s' % (got, EXPECTED['compiler']))
    print('compiler OK', flush=True)

    # Child base: search the unrecorded Help/snapshot/heap flags.
    base = BUILD / 'screen-child-base-v4-20261119'
    chains = [dict(defer_help_resource=d, early_help_model=e, help_parent_snapshot=h)
              for d, e, h in [(1, 1, 1), (1, 1, 0), (1, 0, 0), (0, 0, 0)]]
    combos = [dict(heap_growth_bytes=heap, disk_script_snapshots=bool(disk), **{k: bool(v) for k, v in chain.items()})
              for chain in chains for heap in (256, 512, 128) for disk in (1, 0)]
    child_flags = None
    if (base / 'ASPECT.EXE').exists() and sha(base / 'ASPECT.EXE') == EXPECTED['child_base']:
        child_flags = json.loads((base / 'rebuild-flags.json').read_text())
    for flags in ([] if child_flags else combos):
        shutil.rmtree(base, ignore_errors=True)
        if run(child_call(base, flags), log) == 0 and sha(base / 'ASPECT.EXE') == EXPECTED['child_base']:
            child_flags = flags; (base / 'rebuild-flags.json').write_text(json.dumps(flags, indent=2) + '\n'); break
        print('child base mismatch', flags, flush=True)
    if not child_flags:
        sys.exit('child base: no combination reproduced ' + EXPECTED['child_base'])
    result['child_flags'] = child_flags
    print('child base OK', child_flags, flush=True)

    # Ordinary capability27 overlay child.
    overlay_flags = None
    if not (TARGET['child_overlay'] / 'ASPECT.EXE').exists():
        for n in range(4, -1, -1):
            for chosen in itertools.combinations(['--notice', '--program', '--screen', '--checked-io'], n):
                if '--program' in chosen and '--notice' not in chosen:
                    continue
                shutil.rmtree(TARGET['child_overlay'], ignore_errors=True)
                if run(['standalone/build_aspect_standard_overlay.py', '--base', base, '--output', TARGET['child_overlay'], *chosen], log) == 0 \
                        and sha(TARGET['child_overlay'] / 'ASPECT.EXE') == EXPECTED['child_overlay']:
                    overlay_flags = list(chosen); break
                print('overlay mismatch', chosen, flush=True)
            if overlay_flags is not None:
                break
        else:
            sys.exit('child overlay: no flag set reproduced ' + EXPECTED['child_overlay'])
        (TARGET['child_overlay'] / 'rebuild-flags.json').write_text(json.dumps(overlay_flags) + '\n')
    overlay_flags = json.loads((TARGET['child_overlay'] / 'rebuild-flags.json').read_text())
    result['overlay_flags'] = overlay_flags
    print('child overlay OK', overlay_flags, flush=True)

    # Experimental serial-overlay-ready base plus --serial relink.
    serial_base = BUILD / 'asio-serial-base-v1-20261119'
    if not (TARGET['asio_overlay'] / 'ASPECT.EXE').exists():
        shutil.rmtree(serial_base, ignore_errors=True)
        assert run(child_call(serial_base, dict(child_flags, serial_overlay_ready=True)), log) == 0
        assert run(['standalone/build_aspect_standard_overlay.py', '--base', serial_base, '--output', TARGET['asio_overlay'],
                    *overlay_flags, '--serial'], log) == 0
    got = sha(TARGET['asio_overlay'] / 'ASPECT.EXE')
    result['asio_overlay_sha256'] = got
    result['asio_overlay_matches_record'] = got == EXPECTED['asio_overlay']
    print('asio overlay', 'OK' if got == EXPECTED['asio_overlay'] else 'DIFFERS ' + got, flush=True)

    shutil.rmtree(BUILD / 'rebuild-parent-try', ignore_errors=True)
    result['expected'] = EXPECTED
    result['original_inputs'] = []
    (BUILD / 'rebuild-asio-checkpoint.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
