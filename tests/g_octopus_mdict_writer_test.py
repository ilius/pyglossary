#!/usr/bin/env python3
"""
Comprehensive test suite for octopus_mdict_writer plugin.
Tests all major features: aliases, MDD support, compression, images, special features.
"""

import os
import sys
import tempfile
import unittest

# Add pyglossary to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyglossary.plugins.octopus_mdict_writer.writer import Writer


class MockGlossary:
    """Mock glossary for testing with configurable options."""
    def __init__(self, config=None):
        self._config = config or {}

    def getInfo(self, key):
        infos = {
            "name": "Test MDict Writer",
            "description": "Comprehensive test dictionary"
        }
        return infos.get(key)

    def getConfig(self):
        return self._config


class MockDataEntry:
    """Mock data entry for binary content."""
    def __init__(self, filename, data_bytes):
        self.s_word = filename
        self.data = data_bytes

    def isData(self):
        return True


class MockTextEntry:
    """Mock text entry."""
    def __init__(self, terms, definition):
        self.l_term = terms
        self.defi = definition

    def isData(self):
        return False


class TestMdictWriter(unittest.TestCase):
    """Comprehensive test suite for MDict writer."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.sample_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x00\tpHYs\x00\x00\x0e\xc3\x00\x00\x0e\xc3\x01\xc7o\xa8d\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01]\xdb\x9d\xcc\x00\x00\x00\x00IEND\xaeB`\x82'

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_test_file(self, filename):
        """Create full path for test file."""
        return os.path.join(self.test_dir, filename)

    def test_multiple_aliases(self):
        """Test that multiple aliases create separate searchable entries."""
        glos = MockGlossary()
        writer = Writer(glos)

        # Test entries with aliases
        entries = [
            MockTextEntry(['test', 'Test'], 'A trial or examination.'),
            MockTextEntry(['hello'], 'A greeting word.'),
        ]

        # Feed entries to writer
        gen = writer.write()
        next(gen)
        for entry in entries:
            gen.send(entry)

        # Check entries before finishing (finish() clears them)
        self.assertEqual(len(writer._entries), 3)  # test, Test, hello
        self.assertIn('test', writer._entries)
        self.assertIn('Test', writer._entries)
        self.assertIn('hello', writer._entries)
        self.assertEqual(writer._entries['test'], 'A trial or examination.')
        self.assertEqual(writer._entries['Test'], 'A trial or examination.')  # Same definition

        # Don't call finish for tests that don't write files

    def test_mdd_support(self):
        """Test MDD file creation for binary data."""
        glos = MockGlossary()
        writer = Writer(glos)
        writer.open(self._create_test_file('test_mdd.mdx'))

        entries = [
            MockTextEntry(['word'], 'Definition with image: <img src="test.png">'),
            MockDataEntry('test.png', self.sample_png),
        ]

        # Process entries
        gen = writer.write()
        next(gen)
        for entry in entries:
            gen.send(entry)
        try:
            gen.send(None)
        except StopIteration:
            pass
        writer.finish()

        # Check files created
        mdx_file = self._create_test_file('test_mdd.mdx')
        mdd_file = self._create_test_file('test_mdd.mdd')

        self.assertTrue(os.path.exists(mdx_file), "MDX file should be created")
        self.assertTrue(os.path.exists(mdd_file), "MDD file should be created")

        # Check MDD file size (should contain PNG data)
        mdd_size = os.path.getsize(mdd_file)
        self.assertGreater(mdd_size, len(self.sample_png), "MDD should contain compressed data")

    def test_compression_enabled(self):
        """Test that compression is enabled by default."""
        glos = MockGlossary()
        writer = Writer(glos)

        # Check default compression setting
        self.assertEqual(writer._compression_type, 2)  # zlib

        # Create a file to verify compression works
        writer.open(self._create_test_file('compression_test.mdx'))

        # Add substantial content to test compression
        large_text = "This is test content for compression analysis. " * 500
        entries = [MockTextEntry(['content'], large_text)]

        gen = writer.write()
        next(gen)
        for entry in entries:
            gen.send(entry)
        try:
            gen.send(None)
        except StopIteration:
            pass
        writer.finish()

        # File should be created successfully
        self.assertTrue(os.path.exists(self._create_test_file('compression_test.mdx')))

    def test_image_references(self):
        """Test that image references work correctly."""
        glos = MockGlossary()
        writer = Writer(glos)
        writer.open(self._create_test_file('images.mdx'))

        entries = [
            MockTextEntry(['pic'], 'Image: <img src="photo.jpg">'),
            MockDataEntry('photo.jpg', self.sample_png),
        ]

        gen = writer.write()
        next(gen)
        for entry in entries:
            gen.send(entry)
        try:
            gen.send(None)
        except StopIteration:
            pass
        writer.finish()

        # Both files should exist
        self.assertTrue(os.path.exists(self._create_test_file('images.mdx')))
        self.assertTrue(os.path.exists(self._create_test_file('images.mdd')))

    def test_subfolder_images(self):
        """Test images in subfolder paths."""
        glos = MockGlossary()
        writer = Writer(glos)
        writer.open(self._create_test_file('subfolder.mdx'))

        entries = [
            MockTextEntry(['demo'], 'Image in subfolder: <img src="images/test.png">'),
            MockDataEntry('images/test.png', self.sample_png),
        ]

        gen = writer.write()
        next(gen)
        for entry in entries:
            gen.send(entry)

        # Check data entry before finishing
        self.assertIn('images/test.png', writer._data_entries)

        try:
            gen.send(None)
        except StopIteration:
            pass
        writer.finish()

        # Files should be created
        self.assertTrue(os.path.exists(self._create_test_file('subfolder.mdx')))
        self.assertTrue(os.path.exists(self._create_test_file('subfolder.mdd')))

    def test_special_features_audio_conversion(self):
        """Test audio tag conversion when enabled."""
        glos = MockGlossary({'audio': True})
        writer = Writer(glos)

        # Test audio conversion
        input_html = '<audio controls src="sound.mp3"></audio>'
        output_html = writer.fixDefi(input_html)

        self.assertIn('sound://sound.mp3', output_html)
        self.assertIn('<a href=', output_html)

    def test_special_features_link_processing(self):
        """Test internal link processing."""
        glos = MockGlossary()
        writer = Writer(glos)

        # Test bword:// link conversion
        input_html = '<a href="bword://hello">link</a>'
        output_html = writer.fixDefi(input_html)

        self.assertIn('href="hello"', output_html)
        self.assertNotIn('bword://', output_html)

    def test_special_features_file_paths(self):
        """Test file path processing."""
        glos = MockGlossary()
        writer = Writer(glos)

        # Test relative path conversion
        input_html = '<img src="./image.jpg">'
        output_html = writer.fixDefi(input_html)

        self.assertIn('src="file://image.jpg"', output_html)

    def test_combined_features(self):
        """Test multiple features working together."""
        glos = MockGlossary({'audio': True})
        writer = Writer(glos)
        writer.open(self._create_test_file('combined.mdx'))

        entries = [
            MockTextEntry(['multi', 'alias'], 'Definition with <a href="bword://link">link</a> and <img src="./pic.png">'),
            MockDataEntry('pic.png', self.sample_png),
        ]

        gen = writer.write()
        next(gen)
        for entry in entries:
            gen.send(entry)

        # Check entries before finishing
        self.assertEqual(len(writer._entries), 2)  # multi, alias
        self.assertIn('multi', writer._entries)
        self.assertIn('alias', writer._entries)
        self.assertIn('pic.png', writer._data_entries)

        try:
            gen.send(None)
        except StopIteration:
            pass
        writer.finish()

        # Check files created
        self.assertTrue(os.path.exists(self._create_test_file('combined.mdx')))
        self.assertTrue(os.path.exists(self._create_test_file('combined.mdd')))

    def test_writer_configuration(self):
        """Test that writer accepts configuration options."""
        config = {
            'encoding': 'utf-16',
            'compression_type': 0,  # No compression
            'audio': True,
        }
        glos = MockGlossary(config)
        writer = Writer(glos)

        # Check configuration was applied
        self.assertEqual(writer._encoding, 'utf-16')
        self.assertEqual(writer._compression_type, 0)
        self.assertTrue(writer._audio)

    def test_encoding_support(self):
        """Test that different encodings are supported."""
        test_encodings = ['utf-8', 'utf-16', 'gbk', 'big5']

        for encoding in test_encodings:
            with self.subTest(encoding=encoding):
                config = {'encoding': encoding}
                glos = MockGlossary(config)
                writer = Writer(glos)

                # Check encoding was applied
                self.assertEqual(writer._encoding, encoding)

                # Test file creation with this encoding
                writer.open(self._create_test_file(f'encoding_{encoding.replace("-", "")}.mdx'))

                entries = [MockTextEntry(['test'], 'Hello world')]
                gen = writer.write()
                next(gen)
                for entry in entries:
                    gen.send(entry)
                try:
                    gen.send(None)
                except StopIteration:
                    pass
                writer.finish()

                # File should be created
                self.assertTrue(os.path.exists(self._create_test_file(f'encoding_{encoding.replace("-", "")}.mdx')))


if __name__ == '__main__':
    unittest.main()
