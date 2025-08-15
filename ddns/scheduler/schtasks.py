# -*- coding:utf-8 -*-
"""
schtasks-based task scheduler
@author: NewFuture
"""

import os
import re
import tempfile

from ..util.try_run import try_run
from ._base import BaseScheduler


class SchtasksScheduler(BaseScheduler):
    """schtasks-based task scheduler"""

    NAME = "DDNS"

    def _schtasks(self, *args):
        """Helper to run schtasks commands with consistent error handling"""
        result = try_run(["schtasks"] + list(args), logger=self.logger)
        return result is not None

    def _extract_xml(self, xml_text, tag_name):
        """Extract XML tag content using regex for better performance and flexibility"""
        pattern = r"<{0}[^>]*>(.*?)</{0}>".format(re.escape(tag_name))
        match = re.search(pattern, xml_text, re.DOTALL)
        return match.group(1).strip() if match else None

    def is_installed(self):
        result = try_run(["schtasks", "/query", "/tn", self.NAME], logger=self.logger) or ""
        return self.NAME in result

    def get_status(self):
        # Use XML format for language-independent parsing
        task_xml = try_run(["schtasks", "/query", "/tn", self.NAME, "/xml"], logger=self.logger)
        status = {"scheduler": "schtasks", "installed": bool(task_xml)}

        if not task_xml:
            return status  # Task not installed, return minimal status

        status["enabled"] = self._extract_xml(task_xml, "Enabled") != "false"
        command = self._extract_xml(task_xml, "Command")
        arguments = self._extract_xml(task_xml, "Arguments")
        status["command"] = "{} {}".format(command, arguments) if command and arguments else command

        # Parse interval: PT10M -> 10, fallback to original string
        interval_str = self._extract_xml(task_xml, "Interval")
        interval_match = re.search(r"PT(\d+)M", interval_str) if interval_str else None
        status["interval"] = int(interval_match.group(1)) if interval_match else interval_str

        # Show description if exists, otherwise show installation date
        description = self._extract_xml(task_xml, "Description") or self._extract_xml(task_xml, "Date")
        if description:
            status["description"] = description
        return status

    def install(self, interval, ddns_args=None):
        # Build command line as array: prefer pythonw for script mode, or compiled exe directly
        cmd_array = self._build_ddns_command(ddns_args)
        workdir = os.getcwd()

        # Split array into executable and arguments for schtasks XML format
        # For Windows scheduler, prefer pythonw.exe to avoid console window
        executable = cmd_array[0].replace("python.exe", "pythonw.exe")
        arguments = self._quote_command_array(cmd_array[1:]) if len(cmd_array) > 1 else ""

        # Create XML task definition with working directory support
        description = self._get_description()

        # Use template string to generate Windows Task Scheduler XML
        xml_content = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{description}</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>1900-01-01T00:00:00</StartBoundary>
      <Repetition>
        <Interval>PT{interval}M</Interval>
      </Repetition>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>{exe}</Command>
      <Arguments>{arguments}</Arguments>
      <WorkingDirectory>{dir}</WorkingDirectory>
    </Exec>
  </Actions>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
  </Settings>
</Task>""".format(description=description, interval=interval, exe=executable, arguments=arguments, dir=workdir)

        # Write XML to temp file and use it to create task
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            xml_file = f.name

        try:
            success = self._schtasks("/Create", "/XML", xml_file, "/TN", self.NAME, "/F")
            return success
        finally:
            os.unlink(xml_file)

    def uninstall(self):
        success = self._schtasks("/Delete", "/TN", self.NAME, "/F")
        return success

    def enable(self):
        return self._schtasks("/Change", "/TN", self.NAME, "/Enable")

    def disable(self):
        return self._schtasks("/Change", "/TN", self.NAME, "/Disable")
