@ECHO OFF
REM https://msdn.microsoft.com/zh-cn/library/windows/desktop/bb736357(v=vs.85).aspx
REM schtasks /Create 
REM [/S system [/U username [/P [password]]]]
REM [/RU username [/RP [password]] /SC schedule [/MO modifier] [/D day]
REM [/M months] [/I idletime] /TN taskname /TR taskrun [/ST starttime]
REM [/RI interval] [ {/ET endtime | /DU duration} [/K] 
REM [/XML xmlfile] [/V1]] [/SD startdate] [/ED enddate] [/IT] [/Z] [/F]

IF %ERRORLEVEL% EQU 0 (
  echo run task as SYSTEM
  schtasks /Create /SC MINUTE /MO 5 /TR "%~dp0run.bat" /TN "DDNS" /F /RU "SYSTEM"
) ELSE (
  echo run task as USER
  schtasks /Create /SC MINUTE /MO 5 /TR "%~dp0run.bat" /TN "DDNS" /F
) 
PAUSE
