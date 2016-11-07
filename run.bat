@ECHO OFF

IF "%1" EQU "" (
    python "%~dp0run.py" -c "%~dp0config.json"
    PAUSE
) ELSE (
    python "%~dp0run.py" -c "%~dp0config.json" >> "%1"
)