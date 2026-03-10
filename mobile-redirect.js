// Mobile Detection and Redirect Script
// Add this to your main ai-studio.html

(function() {
    // Detect if user is on mobile device
    function isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (window.innerWidth <= 768 && 'ontouchstart' in window);
    }
    
    // Check screen size for more accurate detection
    function isSmallScreen() {
        return window.innerWidth <= 768 || window.innerHeight <= 1024;
    }
    
    // Redirect to mobile version if needed
    function checkAndRedirect() {
        const currentUrl = window.location.pathname;
        
        // Only redirect from ai-studio page
        if (currentUrl === '/ai-studio' || currentUrl.endsWith('/ai-studio')) {
            if (isMobile() || isSmallScreen()) {
                // Check if user prefers desktop version
                const prefersDesktop = localStorage.getItem('brickkit-prefer-desktop');
                
                if (!prefersDesktop) {
                    window.location.href = '/ai-studio/mobile';
                }
            }
        }
    }
    
    // Add desktop preference toggle
    function addDesktopToggle() {
        if (isMobile() || isSmallScreen()) {
            const toggle = document.createElement('button');
            toggle.innerHTML = '📱 ใช้เวอร์ชันมือถือ';
            toggle.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50 text-sm';
            toggle.style.cssText = 'position: fixed; bottom: 1rem; right: 1rem; z-index: 9999;';
            
            toggle.addEventListener('click', function() {
                const prefersDesktop = localStorage.getItem('brickkit-prefer-desktop');
                
                if (prefersDesktop) {
                    // Remove preference and go to mobile
                    localStorage.removeItem('brickkit-prefer-desktop');
                    window.location.href = '/ai-studio/mobile';
                } else {
                    // Set preference and stay on desktop
                    localStorage.setItem('brickkit-prefer-desktop', 'true');
                    toggle.innerHTML = '💻 ใช้เวอร์ชันเดสก์ท็อป';
                }
            });
            
            document.body.appendChild(toggle);
        }
    }
    
    // Run checks
    checkAndRedirect();
    
    // Add toggle after page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addDesktopToggle);
    } else {
        addDesktopToggle();
    }
    
    // Listen for resize events
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(checkAndRedirect, 500);
    });
    
})();
