# -*- coding:utf-8 -*-
"""
Unit tests for XML utilities
"""

import unittest

from ddns.util.xml import dict_to_xml


class TestXmlUtils(unittest.TestCase):
    """Test XML utility functions"""

    def test_simple_dict_to_xml(self):
        """Test simple dictionary conversion"""
        data = {"name": "test", "value": "123"}
        result = dict_to_xml(data, root="root")
        self.assertIn("<name>test</name>", result)
        self.assertIn("<value>123</value>", result)
        self.assertIn('<?xml version="1.0" encoding="UTF-16"?>', result)

    def test_nested_dict_to_xml(self):
        """Test nested dictionary conversion"""
        data = {"person": {"name": "John", "address": {"city": "New York"}}}
        result = dict_to_xml(data, root="data")
        self.assertIn("<person>", result)
        self.assertIn("<name>John</name>", result)
        self.assertIn("<address>", result)
        self.assertIn("<city>New York</city>", result)

    def test_list_values(self):
        """Test dictionary with list values"""
        data = {"fruits": ["apple", "banana"]}
        result = dict_to_xml(data, root="data")
        self.assertIn("<fruits>apple</fruits>", result)
        self.assertIn("<fruits>banana</fruits>", result)

    def test_special_characters_handling(self):
        """Test XML with special characters (no escaping)"""
        data = {"message": 'Hello <world> & "friends"'}
        result = dict_to_xml(data, root="data")
        self.assertIn("<world>", result)
        self.assertIn("&", result)
        self.assertIn('"friends"', result)

    def test_namespace_support(self):
        """Test XML with namespace"""
        data = {"test": "value"}
        result = dict_to_xml(data, root="root", namespace="http://example.com/ns")
        self.assertIn('xmlns="http://example.com/ns"', result)

    def test_empty_dict(self):
        """Test empty dictionary conversion"""
        data = {"empty": {}}
        result = dict_to_xml(data, root="root")
        self.assertIn("<empty></empty>", result)

    def test_no_root_tag(self):
        """Test conversion with minimal root tag"""
        data = {"test": "value"}
        result = dict_to_xml(data, root="root")
        self.assertIn("<test>value</test>", result)

    def test_windows_task_scheduler_xml(self):
        """Test Windows Task Scheduler XML generation with complete template"""
        # Test data that matches schtasks scheduler structure
        data = {
            "Actions": {
                "Exec": {
                    "Arguments": "run.py --config config.json",
                    "Command": "python.exe",
                    "WorkingDirectory": "C:\\GitHub\\DDNS",
                }
            },
            "RegistrationInfo": {"Description": "Test Task Description"},
            "Settings": {
                "DisallowStartIfOnBatteries": "false",
                "MultipleInstancesPolicy": "IgnoreNew",
                "StopIfGoingOnBatteries": "false",
            },
            "Triggers": {
                "TimeTrigger": {
                    "Enabled": "true",
                    "Repetition": {"Interval": "PT30M"},
                    "StartBoundary": "1900-01-01T00:00:00",
                }
            },
        }

        result = dict_to_xml(
            data, root="Task", namespace="http://schemas.microsoft.com/windows/2004/02/mit/task", version="1.2"
        )

        expected_xml = """<?xml version="1.2" encoding="UTF-16"?><Task xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"><Actions><Exec><Arguments>run.py --config config.json</Arguments><Command>python.exe</Command><WorkingDirectory>C:\\GitHub\\DDNS</WorkingDirectory></Exec></Actions><RegistrationInfo><Description>Test Task Description</Description></RegistrationInfo><Settings><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries></Settings><Triggers><TimeTrigger><Enabled>true</Enabled><Repetition><Interval>PT30M</Interval></Repetition><StartBoundary>1900-01-01T00:00:00</StartBoundary></TimeTrigger></Triggers></Task>"""

        self.assertEqual(result, expected_xml)

    def test_macos_launchd_plist_xml(self):
        """Test macOS launchd plist XML generation with complete template"""
        # Test complete plist structure matching actual launchd.py implementation
        data = {
            "Description": "auto-update v4.0.0 installed on 2025-08-13 16:50:37",
            "Label": "cc.newfuture.ddns",
            "ProgramArguments": ["/usr/bin/python3", "-m", "ddns"],
            "RunAtLoad": True,
            "StartInterval": 300,
            "WorkingDirectory": "/opt/DDNS",
        }

        # Generate complete plist using dict_to_xml with plist as root and version
        complete_plist = dict_to_xml(
            {"dict": data},
            root="plist",
            encoding="UTF-8",
            version="1.0",
            root_version="1.0"
        )

        # Expected XML should include complete plist structure
        expected_xml = """<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict><Description>auto-update v4.0.0 installed on 2025-08-13 16:50:37</Description><Label>cc.newfuture.ddns</Label><ProgramArguments>/usr/bin/python3</ProgramArguments><ProgramArguments>-m</ProgramArguments><ProgramArguments>ddns</ProgramArguments><RunAtLoad>True</RunAtLoad><StartInterval>300</StartInterval><WorkingDirectory>/opt/DDNS</WorkingDirectory></dict></plist>"""

        # Test that the generated XML matches expected output
        self.assertEqual(complete_plist, expected_xml)


if __name__ == "__main__":
    unittest.main()
