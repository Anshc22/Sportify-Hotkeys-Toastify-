@echo off
REM Clean previous builds
rmdir /s /q build
rmdir /s /q dist

REM Build executable
pyinstaller toastify.spec

REM Copy additional files
copy spotify_config.json dist\
copy .custom_color dist\
copy .window_position dist\

REM Create portable zip
cd dist
tar -a -c -f Toastify_portable.zip Toastify.exe spotify_config.json .custom_color .window_position
cd ..

echo Build complete! Check the dist folder.
pause