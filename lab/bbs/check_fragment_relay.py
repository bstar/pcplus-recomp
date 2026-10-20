"""Exercise pacing with real sockets, binary bytes and early disconnect."""
import asyncio
import unittest

from fragment_relay import fragment_relay


class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def test_binary_and_keys(self):
        payload = bytes(range(256)) + b'\x1b[A\x1b[6~\x1b[H\xff\xff\x00'
        observed = bytearray()
        finished = asyncio.Event()

        async def echo(reader, writer):
            try:
                data = await reader.readexactly(len(payload))
                observed.extend(data)
                writer.write(data)
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
                finished.set()

        server = await asyncio.start_server(echo, '127.0.0.1', 0)
        try:
            async with fragment_relay(server.sockets[0].getsockname()[1], 1) as (port, report):
                reader, writer = await asyncio.open_connection('127.0.0.1', port)
                writer.write(payload)
                await writer.drain()
                self.assertEqual(await asyncio.wait_for(reader.readexactly(len(payload)), 5), payload)
                self.assertEqual(await asyncio.wait_for(reader.read(), 5), b'')
                writer.close()
                await writer.wait_closed()
                await asyncio.wait_for(finished.wait(), 5)
            self.assertEqual(observed, payload)
            self.assertTrue(report['byte_conservation'])
            self.assertEqual(report['errors'], [])
            upstream = next(s for s in report['streams'] if s['direction'] == 'client_to_server')
            self.assertEqual(upstream['writes'], len(payload))
        finally:
            server.close()
            await server.wait_closed()

    async def test_cleanup_with_pending_bytes(self):
        finished = asyncio.Event()

        async def consume(reader, writer):
            try:
                await reader.read()
            finally:
                writer.close()
                await writer.wait_closed()
                finished.set()

        server = await asyncio.start_server(consume, '127.0.0.1', 0)
        try:
            async with fragment_relay(server.sockets[0].getsockname()[1], 30) as (port, report):
                reader, writer = await asyncio.open_connection('127.0.0.1', port)
                writer.write(bytes(range(256)))
                await writer.drain()
                # Require an admitted byte, without completing the paced send.
                for _ in range(100):
                    if any(s['read_bytes'] for s in report['streams']):
                        break
                    await asyncio.sleep(.001)
                self.assertTrue(any(s['read_bytes'] for s in report['streams']))
            self.assertEqual(await asyncio.wait_for(reader.read(), 5), b'')
            writer.close()
            await writer.wait_closed()
            await asyncio.wait_for(finished.wait(), 5)
            self.assertFalse(report['byte_conservation'])
        finally:
            server.close()
            await server.wait_closed()


if __name__ == '__main__':
    unittest.main()
