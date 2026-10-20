@echo off
setlocal EnableExtensions
rem Sendero del Inmortal — atajos para Windows nativo (cmd).
rem Uso: make.bat [install|backend|test|lint|front-install|front|test-front|clean|help]

set "ROOT=%~dp0"
set "PORT=8765"
set "PYEXE=%ROOT%python\.venv\Scripts\python.exe"
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=help"

if /i "%TARGET%"=="help"    goto :help
if /i "%TARGET%"=="install" goto :install
if /i "%TARGET%"=="backend" goto :backend
if /i "%TARGET%"=="test"    goto :test
if /i "%TARGET%"=="lint"    goto :lint
if /i "%TARGET%"=="front-install" goto :front_install
if /i "%TARGET%"=="front"   goto :front
if /i "%TARGET%"=="test-front" goto :test_front
if /i "%TARGET%"=="clean"   goto :clean
echo Target desconocido: %TARGET%
goto :help

:help
echo.
echo Uso: make.bat [target]
echo.
echo   install       Crea venv + instala dependencias
echo   backend       Arranca la API en http://127.0.0.1:%PORT%
echo   test          Tests del backend
echo   lint          Lint del backend (ruff)
echo   front-install Instala dependencias del front (web/, npm)
echo   front         Arranca el front en http://127.0.0.1:5173
echo   test-front    Tests del front (vitest)
echo   clean         Borra caches
echo.
goto :eof

:ensure_venv
if exist "%PYEXE%" goto :eof
echo Creando venv de Python...
python -m venv "%ROOT%python\.venv"
if errorlevel 1 (
    echo No se encontro "python". Prueba con "py -3 -m venv python\.venv"
    exit /b 1
)
"%PYEXE%" -m pip install -q -r "%ROOT%python\requirements.txt"
goto :eof

:install
call :ensure_venv
if errorlevel 1 exit /b 1
"%PYEXE%" -m pip install -q -r "%ROOT%python\requirements.txt"
echo Instalado. Ejecuta: make.bat backend
goto :eof

:backend
call :ensure_venv
if errorlevel 1 exit /b 1
pushd "%ROOT%python"
set "PORT=%PORT%"
"%PYEXE%" -m app.main
popd
goto :eof

:test
call :ensure_venv
if errorlevel 1 exit /b 1
pushd "%ROOT%python"
"%PYEXE%" -m pytest tests/ -q
popd
goto :eof

:lint
call :ensure_venv
if errorlevel 1 exit /b 1
"%PYEXE%" -m ruff check "%ROOT%python\app" "%ROOT%python\tests"
goto :eof

:front_install
pushd "%ROOT%web"
call npm install
popd
goto :eof

:front
pushd "%ROOT%web"
call npm run dev
popd
goto :eof

:test_front
pushd "%ROOT%web"
call npm run test
popd
goto :eof

:clean
for /d /r "%ROOT%python" %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"
if exist "%ROOT%python\.pytest_cache" rmdir /s /q "%ROOT%python\.pytest_cache"
echo Limpio.
goto :eof
