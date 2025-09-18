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

    def createWriter(self, writer_class):
        """Create a writer instance and apply configuration options."""
        writer = writer_class(self)
        # Apply configuration options like PyGlossary does
        for name, value in self._config.items():
            setattr(writer, f"_{name}", value)
        return writer


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
        entry_dict = dict(writer._entries)  # Convert list of tuples to dict for easier testing
        self.assertIn('test', entry_dict)
        self.assertIn('Test', entry_dict)
        self.assertIn('hello', entry_dict)
        self.assertEqual(entry_dict['test'], 'A trial or examination.')
        self.assertEqual(entry_dict['Test'], 'A trial or examination.')  # Same definition

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
        writer = glos.createWriter(Writer)

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
        entry_dict = dict(writer._entries)  # Convert list of tuples to dict for easier testing
        self.assertIn('multi', entry_dict)
        self.assertIn('alias', entry_dict)
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
        writer = glos.createWriter(Writer)

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
                writer = glos.createWriter(Writer)

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

    def test_mdd_key_format(self):
        """Test that MDD keys are stored with correct leading backslash format.

        MDX format expects MDD keys to have leading backslashes for proper referencing.
        This test ensures cross-platform compatibility and correct CSS/image references.
        """
        glos = MockGlossary()
        writer = Writer(glos)
        writer.open(self._create_test_file('mdd_keys.mdx'))

        # Create entries with various filename formats
        entries = [
            MockTextEntry(['test'], 'Entry with <link rel="stylesheet" href="file://style.css">'),
            MockDataEntry('style.css', b'body { color: red; }'),
            MockDataEntry('images/logo.png', self.sample_png),
            MockDataEntry('data/subfolder/file.js', b'console.log("test");'),
        ]

        # Process entries to populate writer's data structures
        gen = writer.write()
        next(gen)
        for entry in entries:
            gen.send(entry)

        # Check that data entries are stored with correct filenames
        self.assertIn('style.css', writer._data_entries)
        self.assertIn('images/logo.png', writer._data_entries)
        self.assertIn('data/subfolder/file.js', writer._data_entries)

        # Write the files (this is where MDD keys are formatted)
        try:
            gen.send(None)
        except StopIteration:
            pass
        writer.finish()

        # Verify files were created
        mdx_file = self._create_test_file('mdd_keys.mdx')
        mdd_file = self._create_test_file('mdd_keys.mdd')
        self.assertTrue(os.path.exists(mdx_file))
        self.assertTrue(os.path.exists(mdd_file))

        # Verify MDD keys have correct format (with leading backslash)
        # We need to read the MDD file to check the keys
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mdict-utils'))
            from mdict_utils.base.readmdict import MDD

            mdd = MDD(mdd_file)
            keys = list(mdd.keys())

            # Keys should have leading backslash and use backslashes as separators
            expected_keys = [b'\\style.css', b'\\images\\logo.png', b'\\data\\subfolder\\file.js']
            self.assertEqual(sorted(keys), sorted(expected_keys))

            # Verify data integrity
            self.assertEqual(len(keys), 3)
            for key in keys:
                self.assertTrue(key.startswith(b'\\'), f"Key {key} should start with backslash")

        except ImportError:
            # If mdict-utils is not available, skip MDD verification
            self.skipTest("mdict-utils not available for MDD key verification")

    def test_link_to_link_bug_prevention(self):
        """Test that @@@LINK= entries are handled correctly.

        bugfix from: https://github.com/digitalpalidictionary/dpd-db (very large dict with complex use of aliases)
        """
        glos = MockGlossary()
        writer = Writer(glos)
        writer.open(self._create_test_file('link_sorting.mdx'))

        # Create entries with different keys to test link handling
        entries = [
            MockTextEntry(['main_entry'], 'The primary definition'),     # Main definition
            MockTextEntry(['synonym1'], '@@@LINK=main_entry'),           # Link to main
            MockTextEntry(['synonym2'], '@@@LINK=main_entry'),           # Another link
            MockTextEntry(['regular'], 'A regular definition'),          # Regular entry
        ]

        gen = writer.write()
        next(gen)
        for entry in entries:
            gen.send(entry)

        # Check that entries were stored correctly
        self.assertEqual(len(writer._entries), 4)
        entry_dict = dict(writer._entries)  # Convert list of tuples to dict for easier testing
        self.assertEqual(entry_dict['main_entry'], 'The primary definition')
        self.assertEqual(entry_dict['synonym1'], '@@@LINK=main_entry')
        self.assertEqual(entry_dict['synonym2'], '@@@LINK=main_entry')
        self.assertEqual(entry_dict['regular'], 'A regular definition')

        try:
            gen.send(None)
        except StopIteration:
            pass
        writer.finish()

        # File should be created successfully
        # The link-to-link bug prevention happens in MDictWriter._build_offset_table
        # when sorting entries with identical keys (rare case)
        self.assertTrue(os.path.exists(self._create_test_file('link_sorting.mdx')))


if __name__ == '__main__':
    unittest.main()
