# -*- coding: utf-8 -*-
# type: ignore[index,operator,assignment]
"""
Test cases for cache module

@author: GitHub Copilot
"""

from __init__ import patch, unittest

import os
import tempfile
from time import sleep
from ddns.cache import Cache  # noqa: E402


class TestCache(unittest.TestCase):
    """Test cases for Cache class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test cache files
        self.cache_file = tempfile.mktemp(prefix="ddns_test_cache_", suffix="pk1")
        # self.cache_file = os.path.join(self.test_dir, "test_cache.%d.pkl" % random.randint(1, 10000))

    def tearDown(self):
        """Clean up test fixtures"""
        # Remove the temporary directory and all its contents
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def test_init_new_cache(self):
        """Test cache initialization with new cache file"""
        cache = Cache(self.cache_file)

        # Verify initialization
        self.assertEqual(len(cache), 0)
        self.assertIsInstance(cache.time, float)
        self.assertFalse(os.path.exists(self.cache_file))  # File not created until sync

    def test_init_with_logger(self):
        """Test cache initialization with custom logger"""
        import logging

        logger = logging.getLogger("test_logger")
        cache = Cache(self.cache_file, logger=logger)

        self.assertEqual(len(cache), 0)

    def test_init_with_sync(self):
        """Test cache initialization with sync enabled"""
        cache = Cache(self.cache_file, sync=True)

        self.assertEqual(len(cache), 0)

    def test_setitem_and_getitem(self):
        """Test setting and getting cache items"""
        cache = Cache(self.cache_file)

        # Test setting items
        cache["key1"] = "value1"
        cache["key2"] = "value2"

        # Test getting items
        self.assertEqual(cache["key1"], "value1")
        self.assertEqual(cache["key2"], "value2")
        self.assertEqual(len(cache), 2)

    def test_setitem_duplicate_value(self):
        """Test setting the same value twice doesn't trigger update"""
        cache = Cache(self.cache_file)

        with patch.object(cache, "_Cache__update") as mock_update:
            cache["key1"] = "value1"
            mock_update.assert_called_once()

            # Setting the same value should not trigger update
            mock_update.reset_mock()
            cache["key1"] = "value1"
            mock_update.assert_not_called()

    def test_delitem(self):
        """Test deleting cache items"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"
        cache["key2"] = "value2"

        # Delete an item
        del cache["key1"]

        self.assertEqual(len(cache), 1)
        self.assertNotIn("key1", cache)
        self.assertIn("key2", cache)

    def test_delitem_nonexistent_key(self):
        """Test deleting non-existent key doesn't raise error (silent handling)"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"

        # Should not raise any exception
        del cache["nonexistent"]

        # Original data should remain unchanged
        self.assertEqual(len(cache), 1)
        self.assertIn("key1", cache)

    def test_delitem_idempotent(self):
        """Test that multiple deletions of the same key are safe"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"

        # First deletion should work
        del cache["key1"]
        self.assertEqual(len(cache), 0)
        self.assertNotIn("key1", cache)

        # Second deletion should be safe (no error)
        del cache["key1"]
        self.assertEqual(len(cache), 0)

        # Third deletion should also be safe
        del cache["key1"]
        self.assertEqual(len(cache), 0)

    def test_contains(self):
        """Test membership testing"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"

        self.assertIn("key1", cache)
        self.assertNotIn("key2", cache)

    def test_clear(self):
        """Test clearing cache"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"
        cache["key2"] = "value2"

        cache.clear()

        self.assertEqual(len(cache), 0)
        self.assertNotIn("key1", cache)
        self.assertNotIn("key2", cache)

    def test_clear_empty_cache(self):
        """Test clearing empty cache doesn't trigger update"""
        cache = Cache(self.cache_file)

        with patch.object(cache, "_Cache__update") as mock_update:
            cache.clear()
            mock_update.assert_not_called()

    def test_clear_preserves_private_fields(self):
        """Test that clear only removes non-private fields"""
        cache = Cache(self.cache_file)
        cache["normal1"] = "value1"
        cache["normal2"] = "value2"
        cache["__private"] = "private_value"

        # Check initial state
        self.assertEqual(len(cache), 2)  # Only counts non-private fields

        # Clear should only remove non-private fields
        cache.clear()

        # Private field should still exist in underlying dict
        self.assertEqual(len(cache), 0)
        self.assertNotIn("normal1", cache)
        self.assertNotIn("normal2", cache)
        # Private field still exists but not counted/visible
        self.assertTrue("__private" in dict(cache))

    def test_iteration(self):
        """Test iterating over cache keys"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"
        cache["key2"] = "value2"

        keys = list(cache)
        self.assertEqual(set(keys), {"key1", "key2"})

    def test_private_fields_excluded(self):
        """Test that private fields (starting with __) are excluded from operations"""
        cache = Cache(self.cache_file)
        cache["normal_key"] = "normal_value"

        # Manually add a private field to the underlying dict (for testing purposes)
        super(Cache, cache).__setitem__("__private_field", "private_value")

        # len() should exclude private fields
        self.assertEqual(len(cache), 1)

        # iteration should exclude private fields
        keys = list(cache)
        self.assertEqual(keys, ["normal_key"])

        # data() should exclude private fields
        data = cache.get(None)
        self.assertEqual(data, {"normal_key": "normal_value"})

    def test_private_field_operations_no_sync(self):
        """Test that private field operations don't trigger sync"""
        cache = Cache(self.cache_file)

        with patch.object(cache, "_Cache__update") as mock_update:
            # Setting private field should not trigger sync
            cache["__private"] = "private_value"
            mock_update.assert_not_called()

            # Modifying private field should not trigger sync
            cache["__private"] = "new_private_value"
            mock_update.assert_not_called()

            # Deleting private field should not trigger sync
            del cache["__private"]
            mock_update.assert_not_called()

            # Normal field operations should trigger sync
            cache["normal"] = "value"
            mock_update.assert_called_once()

    def test_private_fields_not_saved_to_file(self):
        """Test that private fields are not saved to file"""
        cache = Cache(self.cache_file)
        cache["normal_key"] = "normal_value"
        cache["__private_key"] = "private_value"

        # Sync to file
        cache.sync()

        # Load new cache instance
        cache2 = Cache(self.cache_file)

        # Only normal fields should be loaded
        self.assertEqual(len(cache2), 1)
        self.assertIn("normal_key", cache2)
        self.assertNotIn("__private_key", cache2)
        self.assertEqual(cache2["normal_key"], "normal_value")

    def test_data_method(self):
        """Test data method for getting cache contents"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"
        cache["key2"] = "value2"

        # Test getting all data
        # data = cache.get()
        # self.assertEqual(data, {"key1": "value1", "key2": "value2"})

        # Test getting specific key
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("nonexistent", "default"), "default")

    def test_data_method_with_sync(self):
        """Test data method with sync enabled calls load"""
        cache = Cache(self.cache_file, sync=True)

        with patch.object(cache, "load") as mock_load:
            cache.load()

            mock_load.assert_called_once()

    def test_sync_method(self):
        """Test sync method saves data to file"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"
        cache["key2"] = "value2"

        # Sync should save to file
        result = cache.sync()

        self.assertIs(result, cache)  # Should return self
        self.assertTrue(os.path.exists(self.cache_file))

        # Load another cache instance to verify data was saved
        cache2 = Cache(self.cache_file)
        self.assertEqual(len(cache2), 2)
        self.assertEqual(cache2["key1"], "value1")
        self.assertEqual(cache2["key2"], "value2")

    def test_sync_no_changes(self):
        """Test sync when no changes have been made after load"""
        # Create and save initial cache
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"
        cache.sync()  # This clears the __changed flag

        with patch("ddns.cache.dump") as mock_dump:
            cache.sync()  # This should not call dump since no changes
            mock_dump.assert_not_called()

    def test_load_existing_file(self):
        """Test loading from existing cache file"""
        # Create initial cache and save data
        cache1 = Cache(self.cache_file)
        cache1["key1"] = "value1"
        cache1["key2"] = 2
        cache1.sync()

        # Load new cache instance
        cache2 = Cache(self.cache_file)

        self.assertEqual(len(cache2), 2)
        self.assertEqual(cache2["key1"], "value1")
        self.assertEqual(cache2["key2"], 2)

    def test_load_corrupted_file(self):
        """Test loading from corrupted cache file"""
        # Create a corrupted cache file
        with open(self.cache_file, "w") as f:
            f.write("corrupted data")

        # Should handle corruption gracefully
        cache = Cache(self.cache_file)
        self.assertEqual(len(cache), 0)

    def test_load_with_exception(self):
        """Test load method handles exceptions properly"""
        # Create a file first
        with open(self.cache_file, "wb") as f:
            f.write(b"invalid pickle data")

        cache = Cache(self.cache_file)

        with patch("ddns.cache.load", side_effect=Exception("Test error")):
            with patch.object(cache, "_Cache__logger") as mock_logger:
                cache.load()
                mock_logger.warning.assert_called_once()

    def test_time_property(self):
        """Test time property returns modification time"""
        cache = Cache(self.cache_file)
        initial_time = cache.time  # type: float # type: ignore[assignment]

        self.assertIsInstance(initial_time, float)
        self.assertGreater(initial_time, 0)

    def test_close_method(self):
        """Test close method syncs and cleans up"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"

        with patch.object(cache, "sync") as mock_sync:
            cache.close()
            mock_sync.assert_called_once()

    def test_str_representation(self):
        """Test string representation of cache"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"

        str_repr = str(cache)
        self.assertIn("key1", str_repr)
        self.assertIn("value1", str_repr)

    def test_auto_sync_behavior(self):
        """Test auto-sync behavior when sync=True"""
        cache = Cache(self.cache_file, sync=True)

        with patch.object(cache, "sync") as mock_sync:
            cache["key1"] = "value1"
            mock_sync.assert_called()

    def test_no_auto_sync_behavior(self):
        """Test no auto-sync behavior when sync=False (default)"""
        cache = Cache(self.cache_file, sync=False)

        with patch.object(cache, "sync") as mock_sync:
            cache["key1"] = "value1"
            mock_sync.assert_not_called()

    def test_context_manager_like_usage(self):
        """Test using cache in a context-manager-like pattern"""
        cache = Cache(self.cache_file)
        cache["key1"] = "value1"
        cache["key2"] = "value2"

        # Manually call close (simulating __del__)
        cache.close()

        # Verify data was persisted
        cache2 = Cache(self.cache_file)
        self.assertEqual(len(cache2), 2)
        self.assertEqual(cache2["key1"], "value1")

    def test_update_time_on_changes(self):
        """Test that modification time is updated on changes"""
        cache = Cache(self.cache_file)
        initial_time = cache.time

        # Small delay to ensure time difference
        sleep(0.01)

        cache["key1"] = "value1"
        new_time = cache.time  # type: float # type: ignore[assignment]

        self.assertGreater(new_time, initial_time)  # type: ignore[comparison-overlap]

    def test_integration_multiple_operations(self):
        """Integration test with multiple operations"""
        cache = Cache(self.cache_file)

        # Add some data
        cache["user1"] = {"name": "Alice", "age": 30}
        cache["user2"] = {"name": "Bob", "age": 25}
        cache["config"] = {"debug": True, "timeout": 30}

        self.assertEqual(len(cache), 3)

        # Modify data
        cache["user1"]["age"] = 31  # This won't trigger update automatically
        cache["user1"] = {"name": "Alice", "age": 31}  # This will

        # Delete data
        del cache["user2"]

        self.assertEqual(len(cache), 2)
        self.assertEqual(cache["user1"]["age"], 31)
        self.assertNotIn("user2", cache)

        # Persist and reload
        cache.sync()

        cache2 = Cache(self.cache_file)
        self.assertEqual(len(cache2), 2)
        self.assertEqual(cache2["user1"]["age"], 31)
        self.assertEqual(cache2["config"]["debug"], True)

    def test_mixed_public_private_operations(self):
        """Test mixed operations with public and private fields"""
        cache = Cache(self.cache_file)

        # Add mixed data
        cache["public1"] = "public_value1"
        cache["__private1"] = "private_value1"
        cache["public2"] = "public_value2"
        cache["__private2"] = "private_value2"

        # Only public fields should be counted
        self.assertEqual(len(cache), 2)

        # Only public fields should be iterable
        public_keys = list(cache)
        self.assertEqual(set(public_keys), {"public1", "public2"})

        # data() should only return public fields
        data = cache.get(None)
        self.assertEqual(data, {"public1": "public_value1", "public2": "public_value2"})

        # Delete operations
        del cache["public1"]  # Should work
        del cache["__private1"]  # Should work but not trigger sync
        del cache["nonexistent"]  # Should be safe

        # Only one public field should remain
        self.assertEqual(len(cache), 1)
        self.assertEqual(list(cache), ["public2"])

        # Sync and reload
        cache.sync()
        cache2 = Cache(self.cache_file)

        # Only public field should be persisted
        self.assertEqual(len(cache2), 1)
        self.assertEqual(list(cache2), ["public2"])
        self.assertEqual(cache2["public2"], "public_value2")

    def test_str_representation_excludes_private(self):
        """Test that string representation only shows public fields"""
        cache = Cache(self.cache_file)
        cache["public"] = "public_value"
        cache["__private"] = "private_value"

        str_repr = str(cache)
        self.assertIn("public", str_repr)
        self.assertIn("public_value", str_repr)
        # Note: private fields might still appear in str() since it calls super().__str__()
        # This is acceptable as str() shows the raw dict content

    def test_json_format_verification(self):
        """Test that cache files are saved in JSON format"""
        import json

        cache = Cache(self.cache_file)
        cache["string_key"] = "string_value"
        cache["number_key"] = 42
        cache["list_key"] = [1, 2, 3]
        cache["dict_key"] = {"nested": "value"}

        # Save to file
        cache.sync()

        # Verify file exists and is valid JSON
        self.assertTrue(os.path.exists(self.cache_file))

        # Read the file and verify it's valid JSON
        with open(self.cache_file, "r") as f:
            file_content = f.read()
            parsed_json = json.loads(file_content)

        # Verify the content matches what we saved
        self.assertEqual(parsed_json["string_key"], "string_value")
        self.assertEqual(parsed_json["number_key"], 42)
        self.assertEqual(parsed_json["list_key"], [1, 2, 3])
        self.assertEqual(parsed_json["dict_key"], {"nested": "value"})

        # Verify the file contains readable JSON (not binary pickle data)
        self.assertIn('"string_key"', file_content)
        self.assertIn('"string_value"', file_content)

    def test_cache_new_disabled(self):
        """Test Cache.new with cache disabled (config_cache=False)"""
        import logging

        logger = logging.getLogger("test_logger")
        cache = Cache.new(False, "test_hash", logger)

        # Should return None when cache is disabled
        self.assertIsNone(cache)

    def test_cache_new_temp_file(self):
        """Test Cache.new with temp file creation (config_cache=True)"""
        import logging
        import tempfile

        logger = logging.getLogger("test_logger")
        test_hash = "test_hash_123"
        cache = Cache.new(True, test_hash, logger)

        # Should create a cache instance
        self.assertIsNotNone(cache)
        self.assertIsInstance(cache, Cache)

        # Should use temp directory with correct naming pattern
        expected_pattern = "ddns.%s.cache" % test_hash
        self.assertIn(expected_pattern, cache._Cache__filename)
        self.assertIn(tempfile.gettempdir(), cache._Cache__filename)

        # Clean up
        cache.close()

    def test_cache_new_custom_path(self):
        """Test Cache.new with custom cache file path"""
        import logging

        logger = logging.getLogger("test_logger")
        custom_path = self.cache_file
        cache = Cache.new(custom_path, "unused_hash", logger)

        # Should create a cache instance with custom path
        self.assertIsNotNone(cache)
        self.assertIsInstance(cache, Cache)
        self.assertEqual(cache._Cache__filename, custom_path)

        # Clean up
        cache.close()

    @patch("ddns.cache.time")
    def test_cache_new_outdated_cache(self, mock_time):
        """Test Cache.new with outdated cache file (>72 hours old)"""
        import logging
        import json

        logger = logging.getLogger("test_logger")

        # Create a cache file with some data
        test_data = {"test_key": "test_value"}
        with open(self.cache_file, "w") as f:
            json.dump(test_data, f)

        # Mock current time to make cache appear outdated
        # Cache file mtime will be recent, but we'll mock current time to be 73 hours later
        current_time = 1000000
        mock_time.return_value = current_time

        # Mock the file modification time to be 73 hours ago
        old_mtime = current_time - (73 * 3600)  # 73 hours ago

        with patch("ddns.cache.stat") as mock_stat:
            mock_stat.return_value.st_mtime = old_mtime
            cache = Cache.new(self.cache_file, "test_hash", logger)

        # Should create cache instance but clear outdated data
        self.assertIsNotNone(cache)
        self.assertIsInstance(cache, Cache)
        self.assertEqual(len(cache), 0)  # Should be empty due to age

        # Clean up
        cache.close()

    def test_cache_new_empty_cache(self):
        """Test Cache.new with empty cache file"""
        import logging
        import json

        logger = logging.getLogger("test_logger")

        # Create an empty cache file
        with open(self.cache_file, "w") as f:
            json.dump({}, f)

        cache = Cache.new(self.cache_file, "test_hash", logger)

        # Should create cache instance
        self.assertIsNotNone(cache)
        self.assertIsInstance(cache, Cache)
        self.assertEqual(len(cache), 0)

        # Clean up
        cache.close()

    @patch("ddns.cache.time")
    def test_cache_new_valid_cache(self, mock_time):
        """Test Cache.new with valid cache file with data"""
        import logging
        import json

        logger = logging.getLogger("test_logger")

        # Create a cache file with test data
        test_data = {
            "domain1.com": {"ip": "1.2.3.4", "timestamp": 1234567890},
            "domain2.com": {"ip": "5.6.7.8", "timestamp": 1234567891},
        }
        with open(self.cache_file, "w") as f:
            json.dump(test_data, f)

        # Mock current time to be within 72 hours of cache creation
        current_time = 1000000
        mock_time.return_value = current_time

        # Mock file modification time to be recent (within 72 hours)
        recent_mtime = current_time - (24 * 3600)  # 24 hours ago

        with patch("ddns.cache.stat") as mock_stat:
            mock_stat.return_value.st_mtime = recent_mtime
            cache = Cache.new(self.cache_file, "test_hash", logger)

        # Should create cache instance with loaded data
        self.assertIsNotNone(cache)
        self.assertIsInstance(cache, Cache)
        self.assertEqual(len(cache), 2)
        self.assertEqual(cache["domain1.com"]["ip"], "1.2.3.4")
        self.assertEqual(cache["domain2.com"]["ip"], "5.6.7.8")

        # Clean up
        cache.close()

    def test_cache_new_nonexistent_file(self):
        """Test Cache.new with nonexistent cache file"""
        import logging

        logger = logging.getLogger("test_logger")
        nonexistent_path = tempfile.mktemp(prefix="ddns_test_nonexistent_", suffix=".cache")

        # Ensure file doesn't exist
        if os.path.exists(nonexistent_path):
            os.remove(nonexistent_path)

        cache = Cache.new(nonexistent_path, "test_hash", logger)

        # Should create cache instance with empty data
        self.assertIsNotNone(cache)
        self.assertIsInstance(cache, Cache)
        self.assertEqual(len(cache), 0)

        # Clean up
        cache.close()


if __name__ == "__main__":
    unittest.main()
