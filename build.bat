@echo off
REM Gera dist\Ametista\Ametista.exe (portátil, sem exigir Python)
pip install -r requirements-build.txt || exit /b 1
pyinstaller --noconfirm --clean --onedir --windowed --name Ametista ^
  --icon assets\icons\ametista.ico --collect-all tkinterdnd2 main.py
xcopy /E /I /Y assets dist\Ametista\assets
xcopy /E /I /Y config dist\Ametista\config
echo Pronto: dist\Ametista\Ametista.exe
