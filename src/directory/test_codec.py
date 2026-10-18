#!/usr/bin/env python3
"""Synthetic, source-only directory tests. No installed directory is read."""
import random
import struct
import unittest
from codec import (DialingDirectory201, DirectoryRecord201, DIRECTORY_SIZE,
                   HEADER_SIZE, RECORD_SIZE, STRING_FIELDS, WORD_FIELDS, BYTE_FIELDS)


class CodecTests(unittest.TestCase):
    def test_complete_layout_has_no_gaps_or_overlap(self):
        spans = [(offset, size) for offset, size in STRING_FIELDS.values()]
        spans += [(offset, 2) for offset in WORD_FIELDS.values()]
        spans += [(offset, 1) for offset in BYTE_FIELDS.values()]
        positions = [p for offset, size in spans for p in range(offset, offset + size)]
        self.assertEqual(sorted(positions), list(range(114)))

    def test_synthetic_disk_layout(self):
        raw = bytearray(DIRECTORY_SIZE)
        raw[225:230] = b'ATDT\0'  # tenth 25-byte header string (J)
        offset = 250 + 199 * 114  # final record, numbered 200 in the program
        raw[offset:offset + 5] = b'NODE\0'
        raw[offset + 0x19:offset + 0x1f] = b'J5551\0'
        struct.pack_into('<H', raw, offset + 0x2e, 8)
        raw[offset + 0x30:offset + 0x34] = bytes([4, 7, 2, 1])
        struct.pack_into('<H', raw, offset + 0x46, 65535)
        raw[offset + 0x68] = 8
        image = DialingDirectory201.from_bytes(raw)
        record = image.record(200)
        self.assertEqual(image.dial_code('J'), b'ATDT')
        self.assertEqual(record.string('name'), b'NODE')
        self.assertEqual(record.string('number'), b'J5551')
        for name, value in [('baud_index', 8), ('parity_index', 4), ('data_bits', 7),
                            ('stop_bits', 2), ('duplex_index', 1),
                            ('completed_call_count', 65535), ('port_override', 8)]:
            self.assertEqual(record.integer(name), value)
        self.assertEqual(image.to_bytes(), raw)

    def test_all_bytes_round_trip_without_enum_or_string_validation(self):
        rng = random.Random(201)
        for _ in range(20):
            raw = rng.randbytes(DIRECTORY_SIZE)
            image = DialingDirectory201.from_bytes(raw)
            for index in range(1, 201):
                image = image.with_record(index, image.record(index))
            self.assertEqual(image.to_bytes(), raw)

    def test_edits_preserve_padding_and_unrelated_records(self):
        raw = bytes([0xa5]) * DIRECTORY_SIZE + b'opaque extension'
        image = DialingDirectory201.from_bytes(raw, allow_trailing=True)
        entry = image.record(17).with_string('script', b'LOGIN').with_integer('port_override', 2)
        changed = image.with_record(17, entry).with_dial_code('A', b'ATDT')
        want = bytearray(raw)
        base = 250 + 16 * 114
        want[base + 0x34:base + 0x3a] = b'LOGIN\0'
        want[base + 0x68] = 2
        want[:5] = b'ATDT\0'
        self.assertEqual(changed.to_bytes(), want)
        self.assertEqual(changed.trailing_bytes, b'opaque extension')
        self.assertEqual(changed.record(17).string('script'), b'LOGIN')

    def test_defaults(self):
        image = DialingDirectory201.blank()
        self.assertEqual(len(image.to_bytes()), 23050)
        self.assertEqual(image.dial_code('J'), b'')
        self.assertEqual(image.record(1), image.record(200))
        self.assertEqual(image.record(1).integer('baud_index'), 2)
        self.assertEqual(image.record(1).integer('terminal_id'), 6)
        self.assertEqual(image.record(1).string('last_call_date'), b'00/00/00')

    def test_strings_boundaries_and_invalid_edit_are_lossless(self):
        original = DirectoryRecord201(bytes([0xff]) * RECORD_SIZE)
        for name, (_, size) in STRING_FIELDS.items():
            with self.assertRaises(ValueError): original.string(name)
            with self.assertRaises(ValueError): original.with_string(name, b'x' * size)
            with self.assertRaises(ValueError): original.with_string(name, b'x\0y')
            edited = original.with_string(name, b'x' * (size - 1))
            self.assertEqual(edited.string(name), b'x' * (size - 1))
        self.assertEqual(original.to_bytes(), bytes([0xff]) * RECORD_SIZE)
        with self.assertRaises(TypeError): original.with_string('name', 'text')
        for name in WORD_FIELDS:
            for value in (-1, 65536, True):
                with self.assertRaises(ValueError): original.with_integer(name, value)
        for name in BYTE_FIELDS:
            with self.assertRaises(ValueError): original.with_integer(name, 256)

    def test_size_index_and_suffix_checks(self):
        for size in (0, DIRECTORY_SIZE - 1, DIRECTORY_SIZE + 1):
            with self.assertRaises(ValueError): DialingDirectory201.from_bytes(bytes(size))
        for index in (0, 201, -1, True):
            with self.assertRaises(ValueError): DialingDirectory201.blank().record(index)
        for letter in ('K', 'a', '', 'AA'):
            with self.assertRaises(ValueError): DialingDirectory201.blank().dial_code(letter)
        with self.assertRaises(ValueError): DialingDirectory201.from_bytes(bytes(10), allow_trailing=True)


if __name__ == '__main__':
    unittest.main()
