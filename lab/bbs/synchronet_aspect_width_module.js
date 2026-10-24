// Explicit synthetic command-shell wrapper. The stock shell runs after Q.
require('sbbsdefs.js', 'K_NONE');
require('key_defs.js', 'KEY_RIGHT');
var width = 132;
var selection = 0;
var events = new File(system.logs_dir + 'peer-width.jsonl');
if (!events.open('a')) throw new Error('Cannot open width witness');
function record(kind, data) {
    data.kind = kind;
    events.writeln(JSON.stringify(data));
    events.flush();
}
function paint() {
    console.screen_columns = width;
    record('paint', { width: width, selection: selection });
    console.write('\x1b[?3' + (width === 132 ? 'h' : 'l') + '\x1b[2J\x1b[H' +
        'LoC WIDTH LAB ' + width + ' SELECT ' + selection +
        '\x1b[2;' + (width === 132 ? '121' : '73') + 'HLOCWIDE');
    // Native Synchronet query/parser, not a reply supplied by this fixture.
    var position = console.getxy();
    record('cpr', { position: position, expected: { x: width === 132 ? 128 : 80, y: 2 } });
}
record('enter', { user: user.alias });
console.write('\r\nLoC ASPECT WIDTH READY\r\n');
record('ready', {});
var startKey = '';
while (bbs.online && !js.terminated && startKey.toUpperCase() !== 'A') {
    startKey = console.inkey(K_NONE, 30000);
}
if (!bbs.online || js.terminated) exit();
record('start', { key: startKey });
paint();
while (bbs.online && !js.terminated) {
    var key = console.inkey(K_NONE, 30000);
    record('key', { key: key });
    if (key === KEY_RIGHT) selection++;
    else if (key === KEY_LEFT) selection--;
    else if (key.toLowerCase() === 'n') width = 80;
    else if (key.toLowerCase() === 'w') width = 132;
    else if (key.toLowerCase() === 'q') break;
    else continue;
    paint();
}
console.screen_columns = 80;
console.write('\x1b[?3l');
record('return', { width: 80, online: bbs.online });
events.close();
load(system.exec_dir + 'default.js');
