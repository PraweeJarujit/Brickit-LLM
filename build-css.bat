@echo off
echo 🔨 Building Tailwind CSS...

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing Tailwind CSS dependencies...
    npm install -D tailwindcss postcss autoprefixer
)

REM Create css directory if it doesn't exist
if not exist "css" mkdir css

REM Build CSS
echo 🔄 Compiling CSS...
npx tailwindcss -i ./src/input.css -o ./css/output.css --minify

if %ERRORLEVEL% EQU 0 (
    echo ✅ CSS built successfully!
    echo 📁 Output: ./css/output.css
    echo.
    echo 📝 Replace CDN link in HTML files with:
    echo ^<link rel="stylesheet" href="/css/output.css"^>
) else (
    echo ❌ Build failed!
    echo Make sure Tailwind CSS is installed:
    echo npm install -D tailwindcss postcss autoprefixer
)

pause
