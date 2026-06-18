@echo off
cd /d D:\GITwork
python -m pytest src/tests/ -v --tb=short
pause
