rmdir /q /s build dist

pyinstaller --onefile --noconfirm pkg\\pyinstaller\\pyglossary.spec

REM pyinstaller --onefile --noconfirm --windowed --noupx pyglossary.pyw
