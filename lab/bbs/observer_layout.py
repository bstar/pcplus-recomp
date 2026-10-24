"""Keep the video-pattern observer while omitting its resident screen copy."""


def compact_watcher(watch):
    declaration = 'console: times 4000 db 0\n'
    start = ' test [sample+2],bx\n'
    end = '.seen:\n'
    assert watch.count(declaration) == watch.count(start) == watch.count(end) == 1
    low, high = watch.index(start), watch.index(end)
    assert low < high and 'rep movsw' in watch[low:high]
    watch = watch[:low] + watch[high:]
    watch = watch.replace(declaration, '')
    for before, after in [('mov cx,4008', 'mov cx,8'), ('cmp ax,4008', 'cmp ax,8'),
                          ('buffer: times 4008 db 0', 'buffer: times 8 db 0')]:
        assert before in watch
        watch = watch.replace(before, after)
    assert 'console' not in watch and '4008' not in watch
    return watch
