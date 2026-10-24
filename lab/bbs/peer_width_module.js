'use strict';

// A synthetic menu loaded by the normal ENiGMA menu stack after authentication.
// No transport, terminal parser or server keyboard code is replaced.
const { MenuModule } = require('../../core/menu_module.js');
const fs = require('fs');
const path = require('path');
exports.moduleInfo = {
    name: 'PCPlus width lab', desc: 'Synthetic width and arrow navigation witness',
    author: 'LoC', packageName: 'loc.pcplus.width.lab',
};
exports.getModule = class WidthLab extends MenuModule {
    initSequence() {
        this.width = 132;
        this.selection = 0;
        this.pending = null;
        this.eventFile = path.resolve(__dirname, '../../logs/peer-width.jsonl');
        this.record('enter', { user: this.client.user.username });
        this.onKey = (ch, key) => {
            this.record('key', { ch, name: key && key.name });
            if (this.pending) return;
            if (key && key.name === 'right arrow') {
                this.selection++;
                this.paint();
            } else if (key && key.name === 'left arrow') {
                this.selection--;
                this.paint();
            } else if (ch && ch.toLowerCase() === 'n') {
                this.width = 80;
                this.paint();
            } else if (ch && ch.toLowerCase() === 'w') {
                this.width = 132;
                this.paint();
            } else if (ch && ch.toLowerCase() === 'q') {
                this.record('return', { width: 80 });
                this.client.term.termWidth = 80;
                this.client.term.rawWrite('\x1b[?3l');
                this.prevMenu();
            }
        };
        this.onCpr = args => {
            this.record('cpr', { args, expected: this.pending });
            this.pending = null;
        };
        this.onData = data => this.record('tcp_input', { hex: Buffer.from(data).toString('hex') });
        this.client.on('key press', this.onKey);
        this.client.on('cursor position report', this.onCpr);
        this.client.on('data', this.onData);
        this.paint();
    }

    record(kind, data) {
        fs.appendFileSync(this.eventFile, JSON.stringify({ kind, ...data }) + '\n');
    }

    paint() {
        const wide = this.width === 132;
        this.client.term.termWidth = this.width;
        // The text ends at column127 (or79); the actual DOS terminal supplies CPR.
        this.pending = [2, wide ? 128 : 80];
        this.record('paint', { width: this.width, selection: this.selection });
        const text = '\x1b[?3' + (wide ? 'h' : 'l') + '\x1b[2J\x1b[H' +
            'LoC WIDTH LAB ' + this.width + ' SELECT ' + this.selection +
            '\x1b[2;' + (wide ? '121' : '73') + 'HLOCWIDE\x1b[6n';
        this.client.term.rawWrite(text);
    }

    leave() {
        this.client.removeListener('key press', this.onKey);
        this.client.removeListener('cursor position report', this.onCpr);
        this.client.removeListener('data', this.onData);
        super.leave();
    }
};
