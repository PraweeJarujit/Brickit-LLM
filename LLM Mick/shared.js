// BRICKKIT Shared Utilities v1.0
// Dark mode applied immediately (before DOM paint to prevent flash)
(function () {
    const stored = localStorage.getItem('brickkit_dark');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (stored === 'true' || (stored === null && prefersDark)) {
        document.documentElement.classList.add('dark');
    }
})();

function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('brickkit_dark', String(isDark));
    _syncDarkIcons(isDark);
}

function _syncDarkIcons(isDark) {
    document.querySelectorAll('[data-dark-icon]').forEach(el => {
        el.textContent = isDark ? 'light_mode' : 'dark_mode';
    });
}

// Mobile Menu
function openMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    const backdrop = document.getElementById('mobile-backdrop');
    if (!menu) return;
    menu.classList.remove('translate-x-full');
    if (backdrop) {
        backdrop.classList.remove('hidden');
        requestAnimationFrame(() => backdrop.classList.remove('opacity-0'));
    }
}

function closeMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    const backdrop = document.getElementById('mobile-backdrop');
    if (!menu) return;
    menu.classList.add('translate-x-full');
    if (backdrop) {
        backdrop.classList.add('opacity-0');
        setTimeout(() => backdrop.classList.add('hidden'), 300);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    _syncDarkIcons(document.documentElement.classList.contains('dark'));
    const bd = document.getElementById('mobile-backdrop');
    if (bd) bd.addEventListener('click', closeMobileMenu);
});
