'use strict';
// Official configuration/FileEntry readback for the isolated synthetic server.
const assert = require('assert/strict');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const candidate = fs.realpathSync(process.argv[2]);
const metadata = JSON.parse(fs.readFileSync(path.join(candidate, 'instance.json')));
assert.equal(metadata.candidate, candidate);
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
assert.equal(hash(path.join(candidate, 'core/client.js')), metadata.client_sha256);
assert.equal(hash(path.join(candidate, 'core/key_stream.js')), metadata.key_stream_sha256);
assert.equal(hash(path.join(candidate, 'config/config.hjson')), metadata.config_sha256);
process.chdir(candidate);
const common = require(path.join(candidate, 'core/oputil/oputil_common.js'));
common.initConfigAndDatabases(error => {
    if (error) throw error;
    const config = require(path.join(candidate, 'core/config.js')).get();
    const mutablePaths = {};
    for (const key of ['logs', 'db', 'modsDb', 'dropFiles', 'emailInbound']) {
        const actual = path.resolve(config.paths[key]);
        assert.ok(actual.startsWith(candidate + path.sep), key + ' must be isolated');
        mutablePaths[key] = actual;
    }
    assert.equal(config.loginServers.telnet.address, '127.0.0.1');
    assert.equal(config.loginServers.telnet.port, 23234);
    const FileEntry = require(path.join(candidate, 'core/file_entry.js'));
    FileEntry.findByFileNameWildcard('PCXTEST.BIN', (error, entries) => {
        if (error) throw error;
        assert.equal(entries.length, 1);
        const entry = entries[0];
        const expected = path.join(candidate, 'file_base/pcplus_transfer/PCXTEST.BIN');
        assert.equal(fs.realpathSync(entry.filePath), expected);
        assert.equal(entry.fileSha256, hash(expected));
        assert.equal(entry.meta.byte_size, fs.statSync(expected).size);
        assert.equal(entry.meta.byte_size, 11521);
        console.log(JSON.stringify({
            passed: true, mutable_paths: mutablePaths,
            server: { address: config.loginServers.telnet.address, port: config.loginServers.telnet.port },
            file: { name: entry.fileName, path: entry.filePath, sha256: entry.fileSha256,
                bytes: entry.meta.byte_size, download_count: entry.meta.dl_count },
            helper_sha256: hash(path.join(candidate, 'helpers/sexyz')),
            scope: 'Official configuration and FileEntry API; isolated paths and physical file corroborated; no additional BBS connection'
        }, null, 2));
        process.exit(0);
    });
});
