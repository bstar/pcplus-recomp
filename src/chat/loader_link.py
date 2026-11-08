"""Source-only resident Chat loader and its separately loadable MZ module."""
import shutil
import subprocess
from build_chat_module import SOURCES, build
from build_path_session import object_segments
from omf_imports import records, externals


def build_loader(root, out, presentation=False, timing=False,foreground=False,redisplay=False,send_mode=False):
    if foreground:timing=True
    if timing:presentation=True
    module = build(out / 'chat-module', presentation=presentation, timing=timing,foreground=foreground,redisplay=redisplay,send_mode=send_mode)
    cobj, aobj = out / 'chat-loader.obj', out / 'chat-load-kernel.obj'
    flags = ['-ox', '-os', '-oe=0']
    subprocess.run(['wcc', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-ecc',
                    '-nt=CHAT_LOAD_CODE', '-nc=FARCODE', *flags,
                    *(['-dCHAT_PRESENTATION'] if presentation else []),
                    *(['-dCHAT_TEXT','-dCHAT_TIMING'] if timing else []),
                    *(['-dCHAT_FOREGROUND_TEXT'] if foreground else []),
                    *(['-dCHAT_REDISPLAY'] if redisplay else []),
                    *(['-dCHAT_SEND_MODE'] if send_mode else []),
                    '-i='+str(out / 'chat-module'), '-fo='+str(cobj),
                    str(root / 'src/chat/loader.c')], cwd=out, check=True)
    subprocess.run(['nasm', '-fobj', '-DCHAT_LOADER_BANK',
                    str(root / 'src/chat/overlay_load.asm'), '-o', str(aobj)], check=True)
    imports = [name.decode() for kind, data, raw in records(cobj.read_bytes())
               if kind == 0x8c for name, index in externals(data)]
    assert set(imports) == {'_small_code_', '_chat_file_open', '_chat_file_read',
                            '_chat_file_close', '_chat_dos_overlay_load', '_chat_module_image_valid'}, imports
    sizes = []
    for obj in (cobj, aobj):
        segments = object_segments(obj)
        assert all(not s['bytes'] for n, s in segments.items() if n != 'CHAT_LOAD_CODE'), segments
        sizes.append(segments['CHAT_LOAD_CODE']['bytes'])
    # NASM's kernel contribution explicitly requests paragraph alignment.
    # The C contribution begins the bank; include the intervening linker pad.
    size = ((sizes[0]+15)//16)*16 + sizes[1]
    shutil.copyfile(out / 'chat-module/PCCHAT.OVL', out / 'PCCHAT.OVL')
    inputs = list(dict.fromkeys(list(module['sources']) + ['src/chat/loader.c', 'src/chat/loader.h',
                  'src/chat/overlay_load.asm', 'src/chat/loader_link.py',
                  'standalone/build_path_session.py', 'standalone/omf_imports.py']))
    return dict(objects=[cobj, aobj], inputs=[root / n for n in inputs],
                module=module, code_bytes=size, object_code_bytes=sum(sizes), near_data_bytes=0,
                compiler_flags=flags, imports=imports,
                foreground_binding=False, storage_lease=False)
