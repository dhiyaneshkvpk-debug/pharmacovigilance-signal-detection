@echo off
REM Runs everything: steps 1-3, then opens the dashboard.
REM Double-click this file (after you have created the venv and copied the zip files).
cd /d "%~dp0"
call venv\Scripts\activate
python step1_data_processing.py   || goto :error
python step2_statistical_analysis.py || goto :error
python step3_machine_learning.py  || goto :error
streamlit run app.py
goto :eof
:error
echo.
echo Something failed - read the message above.
pause
