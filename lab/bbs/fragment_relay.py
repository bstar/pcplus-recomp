"""Loopback-only, byte-preserving network fragmentation experiment.

Pacing writes does not guarantee TCP receive-event boundaries. Actual menu
outcomes remain the acceptance criterion. No Telnet/ANSI decoding is performed.
"""
import asyncio
from contextlib import asynccontextmanager
import hashlib


@asynccontextmanager
async def fragment_relay(port, delay_ms):
    if not 0 < delay_ms <= 30:
        raise ValueError('Use a byte delay in 1..30 ms')
    tasks = set()
    streams = []
    errors = []

    async def accept(reader, writer):
        task = asyncio.current_task()
        tasks.add(task)
        peer = None
        try:
            remote, peer = await asyncio.open_connection('127.0.0.1', port)

            async def pump(source, destination, paced):
                received, sent = hashlib.sha256(), hashlib.sha256()
                entry = dict(direction='client_to_server' if paced else 'server_to_client',
                             read_bytes=0, written_bytes=0, writes=0)
                streams.append(entry)
                try:
                    while data := await source.read(4096):
                        received.update(data)
                        entry['read_bytes'] += len(data)
                        pieces = (bytes([b]) for b in data) if paced else (data,)
                        for piece in pieces:
                            if paced:
                                await asyncio.sleep(delay_ms / 1000)
                            destination.write(piece)
                            await destination.drain()
                            sent.update(piece)
                            entry['written_bytes'] += len(piece)
                            entry['writes'] += 1
                finally:
                    entry['read_sha256'] = received.hexdigest()
                    entry['written_sha256'] = sent.hexdigest()
                    destination.close()

            pumps = [asyncio.create_task(pump(reader, peer, True)),
                     asyncio.create_task(pump(remote, writer, False))]
            try:
                await asyncio.gather(*pumps)
            finally:
                for pump_task in pumps:
                    if not pump_task.done():
                        pump_task.cancel()
                await asyncio.gather(*pumps, return_exceptions=True)
        except (ConnectionError, OSError) as error:
            errors.append(type(error).__name__)
        finally:
            writer.close()
            if peer:
                peer.close()
            tasks.discard(task)

    listener = await asyncio.start_server(accept, '127.0.0.1', 0)
    report = dict(requested_byte_delay_ms=delay_ms, streams=streams, errors=errors,
                  scope='One-byte client writes paced on loopback; TCP receive boundaries and physical modem timing are not guaranteed.')
    try:
        yield listener.sockets[0].getsockname()[1], report
    finally:
        listener.close()
        pending = list(tasks)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        # Python 3.13+ waits for accepted transports as well as the listener.
        # Close/cancel their owners before waiting for server shutdown.
        await listener.wait_closed()
        report['byte_conservation'] = bool(streams) and all(
            s['read_bytes'] == s['written_bytes'] and
            s.get('read_sha256') == s.get('written_sha256') for s in streams)
        report['client_bytes'] = sum(s['written_bytes'] for s in streams
                                     if s['direction'] == 'client_to_server')
