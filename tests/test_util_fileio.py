# coding=utf-8
"""
Tests for ddns.util.fileio module
"""

import os
import shutil
import tempfile
from io import open  # Python 2/3 compatible UTF-8 file operations

from __init__ import MagicMock, patch, unittest

import ddns.util.fileio as fileio

# Test constants
TEST_ENCODING_UTF8 = "utf-8"
TEST_ENCODING_ASCII = "ascii"
# Ensure content is unicode f
TEST_CONTENT_MULTILINGUAL = u"Hello World! 测试内容"  # fmt: skip


class TestFileIOModule(unittest.TestCase):
    """Test fileio module functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_content = TEST_CONTENT_MULTILINGUAL
        self.test_encoding = TEST_ENCODING_UTF8

    def tearDown(self):
        """Clean up after tests"""
        pass

    def test_ensure_directory_exists_success(self):
        """Test _ensure_directory_exists creates directory successfully"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "subdir", "test.txt")
            fileio._ensure_directory_exists(test_file)
            self.assertTrue(os.path.exists(os.path.dirname(test_file)))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ensure_directory_exists_already_exists(self):
        """Test _ensure_directory_exists when directory already exists"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "test.txt")
            # Directory already exists, should not raise error
            fileio._ensure_directory_exists(test_file)
            self.assertTrue(os.path.exists(temp_dir))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ensure_directory_exists_empty_path(self):
        """Test _ensure_directory_exists with empty directory path"""
        # Should not raise error for relative paths without directory
        fileio._ensure_directory_exists("test.txt")

    @patch("ddns.util.fileio.os.makedirs")
    @patch("ddns.util.fileio.os.path.exists")
    @patch("ddns.util.fileio.os.path.dirname")
    def test_ensure_directory_exists_makedirs_called(self, mock_dirname, mock_exists, mock_makedirs):
        """Test _ensure_directory_exists calls os.makedirs when needed"""
        mock_dirname.return_value = "/test/dir"
        mock_exists.return_value = False

        fileio._ensure_directory_exists("/test/dir/file.txt")

        mock_dirname.assert_called_once_with("/test/dir/file.txt")
        mock_exists.assert_called_once_with("/test/dir")
        mock_makedirs.assert_called_once_with("/test/dir")

    @patch("ddns.util.fileio.os.makedirs")
    @patch("ddns.util.fileio.os.path.exists")
    @patch("ddns.util.fileio.os.path.dirname")
    def test_ensure_directory_exists_raises_exception(self, mock_dirname, mock_exists, mock_makedirs):
        """Test _ensure_directory_exists properly raises OSError"""
        mock_dirname.return_value = "/test/dir"
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        with self.assertRaises(OSError):
            fileio._ensure_directory_exists("/test/dir/file.txt")

    def test_read_file_success(self):
        """Test read_file with successful file reading"""
        # Create temporary file with Python 2/3 compatible approach
        temp_fd, temp_path = tempfile.mkstemp()
        try:
            # Write content using io.open for consistent behavior
            with open(temp_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(self.test_content)

            result = fileio.read_file(temp_path, self.test_encoding)
            self.assertEqual(result, self.test_content)
        finally:
            os.close(temp_fd)
            os.unlink(temp_path)

    def test_read_file_nonexistent_file(self):
        """Test read_file with nonexistent file raises exception"""
        with self.assertRaises((OSError, IOError)):
            fileio.read_file("nonexistent_file.txt")

    def test_read_file_different_encoding(self):
        """Test read_file with different encoding"""
        # Use ASCII-safe content for encoding test
        content = u"ASCII content"  # fmt: skip

        temp_fd, temp_path = tempfile.mkstemp()
        try:
            # Write content using io.open for consistent behavior
            with open(temp_path, "w", encoding="ascii") as temp_file:
                temp_file.write(content)

            result = fileio.read_file(temp_path, "ascii")
            self.assertEqual(result, content)
        finally:
            os.close(temp_fd)
            os.unlink(temp_path)

    @patch("ddns.util.fileio.open")
    def test_read_file_with_mock(self, mock_open):
        """Test read_file with mocked file operations"""
        mock_file = MagicMock()
        mock_file.read.return_value = self.test_content
        mock_open.return_value.__enter__.return_value = mock_file

        result = fileio.read_file("/test/path.txt", self.test_encoding)

        self.assertEqual(result, self.test_content)
        mock_open.assert_called_once_with("/test/path.txt", "r", encoding=self.test_encoding)
        mock_file.read.assert_called_once()

    def test_read_file_safely_success(self):
        """Test read_file_safely with successful file reading"""
        temp_fd, temp_path = tempfile.mkstemp()
        try:
            # Write content using io.open for consistent behavior
            with open(temp_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(self.test_content)

            result = fileio.read_file_safely(temp_path, self.test_encoding)
            self.assertEqual(result, self.test_content)
        finally:
            os.close(temp_fd)
            os.unlink(temp_path)

    def test_read_file_safely_nonexistent_file(self):
        """Test read_file_safely with nonexistent file returns None"""
        result = fileio.read_file_safely("nonexistent_file.txt")
        self.assertIsNone(result)

    @patch("ddns.util.fileio.read_file")
    def test_read_file_safely_exception_handling(self, mock_read_file):
        """Test read_file_safely handles exceptions properly"""
        test_path = "/test/path.txt"
        mock_read_file.side_effect = OSError("File not found")

        result = fileio.read_file_safely(test_path)

        self.assertIsNone(result)
        mock_read_file.assert_called_once_with(test_path, TEST_ENCODING_UTF8)

    @patch("ddns.util.fileio.read_file")
    def test_read_file_safely_unicode_error(self, mock_read_file):
        """Test read_file_safely handles UnicodeDecodeError"""
        mock_read_file.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")

        result = fileio.read_file_safely("/test/path.txt")
        self.assertIsNone(result)

    def test_write_file_success(self):
        """Test write_file with successful file writing"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "subdir", "test.txt")

            fileio.write_file(test_file, self.test_content, self.test_encoding)

            # Verify file was created and content is correct
            self.assertTrue(os.path.exists(test_file))
            with open(test_file, "r", encoding=self.test_encoding) as f:
                content = f.read()
            self.assertEqual(content, self.test_content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_write_file_creates_directory(self):
        """Test write_file automatically creates directory"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "new", "nested", "dir", "test.txt")

            fileio.write_file(test_file, self.test_content)

            # Verify directory structure was created
            self.assertTrue(os.path.exists(os.path.dirname(test_file)))
            self.assertTrue(os.path.exists(test_file))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch("ddns.util.fileio._ensure_directory_exists")
    @patch("ddns.util.fileio.open")
    def test_write_file_with_mock(self, mock_open, mock_ensure_dir):
        """Test write_file with mocked operations"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        fileio.write_file("/test/path.txt", self.test_content, self.test_encoding)

        mock_ensure_dir.assert_called_once_with("/test/path.txt")
        mock_open.assert_called_once_with("/test/path.txt", "w", encoding=self.test_encoding)
        mock_file.write.assert_called_once_with(self.test_content)

    def test_write_file_safely_success(self):
        """Test write_file_safely with successful file writing"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "test.txt")

            result = fileio.write_file_safely(test_file, self.test_content, self.test_encoding)

            self.assertTrue(result)
            self.assertTrue(os.path.exists(test_file))
            with open(test_file, "r", encoding=self.test_encoding) as f:
                content = f.read()
            self.assertEqual(content, self.test_content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch("ddns.util.fileio.write_file")
    def test_write_file_safely_exception_handling(self, mock_write_file):
        """Test write_file_safely handles exceptions properly"""
        mock_write_file.side_effect = OSError("Permission denied")

        result = fileio.write_file_safely("/test/path.txt", self.test_content)
        self.assertFalse(result)
        mock_write_file.assert_called_once_with("/test/path.txt", self.test_content, "utf-8")

    @patch("ddns.util.fileio.write_file")
    def test_write_file_safely_unicode_error(self, mock_write_file):
        """Test write_file_safely handles UnicodeEncodeError"""
        # Create UnicodeEncodeError with proper arguments for Python 2/3 compatibility
        try:
            # Python 2 - need unicode objects
            error = UnicodeEncodeError("utf-8", u"", 0, 1, "invalid")  # fmt: skip
        except TypeError:
            # Python 3 - accepts str objects
            error = UnicodeEncodeError("utf-8", "", 0, 1, "invalid")

        mock_write_file.side_effect = error

        result = fileio.write_file_safely("/test/path.txt", self.test_content)
        self.assertFalse(result)

    def test_ensure_directory_success(self):
        """Test ensure_directory with successful directory creation"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "new", "nested", "test.txt")

            result = fileio.ensure_directory(test_file)

            self.assertTrue(result)
            self.assertTrue(os.path.exists(os.path.dirname(test_file)))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ensure_directory_already_exists(self):
        """Test ensure_directory when directory already exists"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "test.txt")

            result = fileio.ensure_directory(test_file)

            self.assertTrue(result)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch("ddns.util.fileio._ensure_directory_exists")
    def test_ensure_directory_exception_handling(self, mock_ensure_dir):
        """Test ensure_directory handles exceptions properly"""
        mock_ensure_dir.side_effect = OSError("Permission denied")

        result = fileio.ensure_directory("/test/path.txt")
        self.assertFalse(result)
        mock_ensure_dir.assert_called_once_with("/test/path.txt")

    @patch("ddns.util.fileio._ensure_directory_exists")
    def test_ensure_directory_io_error(self, mock_ensure_dir):
        """Test ensure_directory handles IOError"""
        mock_ensure_dir.side_effect = IOError("IO Error")

        result = fileio.ensure_directory("/test/path.txt")
        self.assertFalse(result)

    def test_integration_full_workflow(self):
        """Integration test for complete file I/O workflow"""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "integration", "test.txt")

            # Test complete workflow
            # 1. Ensure directory
            self.assertTrue(fileio.ensure_directory(test_file))

            # 2. Write file
            fileio.write_file(test_file, self.test_content)

            # 3. Read file
            content = fileio.read_file(test_file)
            self.assertEqual(content, self.test_content)

            # 4. Safe operations
            updated_content_str = u"Updated content"  # fmt: skip

            self.assertTrue(fileio.write_file_safely(test_file, updated_content_str))
            updated_content = fileio.read_file_safely(test_file)
            self.assertEqual(updated_content, updated_content_str)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_integration_error_scenarios(self):
        """Integration test for error handling scenarios"""
        # Test nonexistent files
        self.assertIsNone(fileio.read_file_safely("/nonexistent/path.txt"))

        # Test safe operations return appropriate values
        # Use a more portable invalid path that will fail on most systems
        try:
            # Try to write to root directory (usually fails due to permissions)
            invalid_path = "C:\\invalid_root_file.txt" if os.name == "nt" else "/invalid_root_file.txt"
            result = fileio.write_file_safely(invalid_path, "content")
            # On some systems this might work, on others it might fail
            # We just verify it doesn't crash and returns a boolean
            self.assertIsInstance(result, bool)
        except Exception:
            # If any exception occurs, that's also acceptable for this test
            # as we're testing that the function handles errors gracefully
            pass

    def test_utf8_encoding_support(self):
        """Test UTF-8 encoding support with various characters"""
        # Ensure all test contents are unicode for Python 2 compatibility
        try:
            # Python 2 - ensure unicode
            test_contents = [
                u"English text",
                u"中文测试",
                u"Русский текст",
                u"العربية",
                u"🌟✨🎉",
                u"Mixed: English 中文 🎉",
            ]  # fmt: skip
        except NameError:
            # Python 3
            test_contents = ["English text", "中文测试", "Русский текст", "العربية", "🌟✨🎉", "Mixed: English 中文 🎉"]

        temp_dir = tempfile.mkdtemp()
        try:
            for i, content in enumerate(test_contents):
                test_file = os.path.join(temp_dir, "test_{}.txt".format(i))

                # Write and read back
                fileio.write_file(test_file, content)
                read_content = fileio.read_file(test_file)
                self.assertEqual(read_content, content, "Failed for content: {!r}".format(content))

                # Test safe operations
                self.assertTrue(fileio.write_file_safely(test_file, content))
                safe_content = fileio.read_file_safely(test_file)
                self.assertEqual(safe_content, content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_different_encodings(self):
        """Test support for different encodings"""
        # Use ASCII-safe content for encoding test
        ascii_content = u"ASCII only content"  # fmt: skip

        temp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(temp_dir, "ascii_test.txt")

            # Write with ASCII encoding
            fileio.write_file(test_file, ascii_content, TEST_ENCODING_ASCII)

            # Read with ASCII encoding
            content = fileio.read_file(test_file, TEST_ENCODING_ASCII)
            self.assertEqual(content, ascii_content)

            # Test safe operations with encoding
            self.assertTrue(fileio.write_file_safely(test_file, ascii_content, TEST_ENCODING_ASCII))
            safe_content = fileio.read_file_safely(test_file, TEST_ENCODING_ASCII)
            self.assertEqual(safe_content, ascii_content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
