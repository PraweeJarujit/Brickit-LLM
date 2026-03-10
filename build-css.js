#!/usr/bin/env node

/**
 * Build CSS with Tailwind CSS
 * Run this script to compile Tailwind CSS for production
 */

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔨 Building Tailwind CSS...');

// Ensure output directory exists
const outputDir = path.join(__dirname, 'css');
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

// Build command
const buildCommand = 'npx tailwindcss -i ./src/input.css -o ./css/output.css --minify';

exec(buildCommand, (error, stdout, stderr) => {
    if (error) {
        console.error('❌ Build failed:', error);
        console.error('Make sure you have installed tailwindcss:');
        console.error('npm install -D tailwindcss postcss autoprefixer');
        return;
    }
    
    if (stderr) {
        console.error('⚠️ Warnings:', stderr);
    }
    
    console.log('✅ CSS built successfully!');
    console.log('📁 Output: ./css/output.css');
    console.log('\n📝 Usage:');
    console.log('Replace CDN link in HTML files with:');
    console.log('<link rel="stylesheet" href="/css/output.css">');
});
