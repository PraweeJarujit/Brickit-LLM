#!/usr/bin/env python3
"""
Script to update all HTML pages to use consistent design system
"""

import os
import re

def update_page_header(filepath):
    """Update header to use consistent design system"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace old head section
    old_head_pattern = r'<head>.*?</head>'
    new_head = '''<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>{} - BRICKIT</title>
    <link href="styles.css" rel="stylesheet"/>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <script src="/shared.js"></script>
</head>'''
    
    # Get page title
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1) if title_match else "BRICKIT"
    
    content = re.sub(old_head_pattern, new_head.format(title), content, flags=re.DOTALL)
    
    # Replace old header structure
    old_header_pattern = r'<header class=".*?</header>'
    new_header = '''<header class="header">
    <div class="layout-container">
        <div class="header-content">
            <a class="logo" href="/">
                <div class="logo-icon">
                    <svg fill="currentColor" viewbox="0 0 48 48"><path d="M4 4H17.3334V17.3334H30.6666V30.6666H44V44H4V4Z"></path></svg>
                </div>
                <h2 class="logo-text">BRICKIT</h2>
            </a>
            <div class="nav">
                <nav class="nav">
                    <a class="nav-link" href="/size-s">Shop</a>
                    <a class="nav-link" href="#">About</a>
                    <a class="nav-link" href="#">Sustainability</a>
                    <a class="nav-link" href="/ai-studio">AI Studio</a>
                    <a class="nav-link" href="/orders">My Orders</a>
                </nav>
            </div>
            <div class="flex gap-2 justify-end">
                <button onclick="toggleDarkMode()" class="btn btn-secondary" title="Toggle dark mode">
                    <span class="material-symbols-outlined" data-dark-icon>dark_mode</span>
                </button>
                <button class="btn btn-secondary">
                    <span class="material-symbols-outlined">search</span>
                </button>
                <button class="btn btn-secondary relative">
                    <span class="material-symbols-outlined">shopping_bag</span>
                    <span class="absolute top-2 right-2 size-2 bg-primary rounded-full"></span>
                </button>
                <a href="/login" class="btn btn-secondary">
                    <span class="material-symbols-outlined">account_circle</span>
                </a>
            </div>
        </div>
    </div>
</header>'''
    
    content = re.sub(old_header_pattern, new_header, content, flags=re.DOTALL)
    
    # Replace body class
    content = re.sub(
        r'<body[^>]*>',
        '<body class="font-display antialiased">',
        content
    )
    
    # Update main content containers
    content = re.sub(
        r'<main[^>]*>',
        '<main class="layout-container section">',
        content
    )
    
    # Update product grids
    content = re.sub(
        r'class="grid[^"]*grid-cols-[^"]*gap-[^"]*"',
        'class="product-grid"',
        content
    )
    
    # Update cards
    content = re.sub(
        r'class="[^"]*rounded[^"]*border[^"]*bg-[^"]*p-[^"]*"',
        'class="card"',
        content
    )
    
    # Update buttons
    content = re.sub(
        r'class="[^"]*rounded[^"]*bg-[^"]*hover:bg-[^"]*text-[^"]*font-[^"]*"',
        'class="btn btn-primary"',
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {filepath}")

def main():
    """Update all HTML files"""
    html_files = [
        'size-l.html',
        'login.html', 
        'checkout.html',
        'orders.html'
    ]
    
    for filename in html_files:
        if os.path.exists(filename):
            update_page_header(filename)
        else:
            print(f"File {filename} not found")

if __name__ == "__main__":
    main()
