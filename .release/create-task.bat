@ECHO OFF
REM https://msdn.microsoft.com/zh-cn/library/windows/desktop/bb736357(v=vs.85).aspx

SET RUNCMD="cmd /c ''%~dp0ddns.exe' -c '%~dp0config.json' >> '%~dp0run.log''"

SET RUN_USER=%USERNAME%
WHOAMI /GROUPS | FIND "12288" > NUL && SET RUN_USER="SYSTEM"

ECHO Create task run as %RUN_USER%
schtasks /Create /SC MINUTE /MO 5 /TR %RUNCMD% /TN "DDNS" /F /RU "%RUN_USER%"

PAUSE
