// BRICKIT Shared Utilities v2.1
// Enhanced with new features: Reviews, Wishlist, Promotions, Analytics, i18n
// Dark mode applied immediately (before DOM paint to prevent flash)
(function () {
    const stored = localStorage.getItem('BRICKIT_dark');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (stored === 'true' || (stored === null && prefersDark)) {
        document.documentElement.classList.add('dark');
    }
})();

// --- MULTI-LANGUAGE SYSTEM (i18n) ---
const translations = {
    th: {
        // Navigation
        'nav.design': 'ออกแบบ',
        'nav.how-it-works': 'วิธีใช้งาน',
        'nav.order': 'สั่งซื้อ',
        'nav.login': 'เข้าสู่ระบบ',
        'nav.logout': 'ออกจากระบบ',
        
        // Cart
        'cart.title': 'ตะกร้าสินค้า',
        'cart.empty': 'ไม่มีสินค้าในตะกร้า',
        'cart.start_shopping': 'เริ่มช้อปปิ้งสินค้าของเรา!',
        'cart.total': 'รวม:',
        'cart.checkout': 'สั่งซื้อ',
        'cart.added': 'เพิ่มลงตะกร้าแล้ว!',
        
        // Product Pages
        'product.add_to_cart': 'เพิ่มลงตะกร้า',
        'product.out_of_stock': 'สินค้าหมด',
        'product.in_stock': 'มีสินค้า',
        'product.quantity': 'จำนวน',
        'product.price': 'ราคา',
        'product.description': 'รายละเอียดสินค้า',
        
        // Size Categories
        'size.s': 'ขนาด S',
        'size.m': 'ขนาด M', 
        'size.l': 'ขนาด L',
        'size.all': 'ทุกขนาด',
        
        // User Interface
        'ui.loading': 'กำลังโหลด...',
        'ui.error': 'เกิดข้อผิดพลาด',
        'ui.success': 'สำเร็จ',
        'ui.cancel': 'ยกเลิก',
        'ui.confirm': 'ยืนยัน',
        'ui.save': 'บันทึก',
        'ui.edit': 'แก้ไข',
        'ui.delete': 'ลบ',
        'ui.close': 'ปิด',
        'ui.search': 'ค้นหา',
        'ui.filter': 'กรอง',
        'ui.sort': 'เรียงลำดับ',
        
        // Messages
        'msg.login_required': 'กรุณาเข้าสู่ระบบก่อน',
        'msg.added_to_wishlist': 'เพิ่มใน wishlist สำเร็จ!',
        'msg.removed_from_wishlist': 'ลบจาก wishlist สำเร็จ',
        'msg.already_in_wishlist': 'สินค้านี้อยู่ใน wishlist แล้ว',
        'msg.review_submitted': 'รีวิวของคุณถูกบันทึกแล้ว!',
        'msg.no_reviews': 'ยังไม่มีรีวิว',
        'msg.stock_low': 'สินค้าคงเหลือเพียง {count} ชิ้น',
        'msg.promo_invalid': 'โค้ดไม่ถูกต้องหรือหมดอายุ',
        'msg.promo_applied': 'ส่วนลด ${amount}!'
    },
    en: {
        // Navigation
        'nav.design': 'Design',
        'nav.how-it-works': 'How It Works',
        'nav.order': 'Order',
        'nav.login': 'Login',
        'nav.logout': 'Logout',
        
        // Cart
        'cart.title': 'Shopping Cart',
        'cart.empty': 'No items in cart',
        'cart.start_shopping': 'Start shopping our products!',
        'cart.total': 'Total:',
        'cart.checkout': 'Checkout',
        'cart.added': 'Added to cart!',
        
        // Product Pages
        'product.add_to_cart': 'Add to Cart',
        'product.out_of_stock': 'Out of Stock',
        'product.in_stock': 'In Stock',
        'product.quantity': 'Quantity',
        'product.price': 'Price',
        'product.description': 'Product Description',
        
        // Size Categories
        'size.s': 'Size S',
        'size.m': 'Size M',
        'size.l': 'Size L',
        'size.all': 'All Sizes',
        
        // User Interface
        'ui.loading': 'Loading...',
        'ui.error': 'Error',
        'ui.success': 'Success',
        'ui.cancel': 'Cancel',
        'ui.confirm': 'Confirm',
        'ui.save': 'Save',
        'ui.edit': 'Edit',
        'ui.delete': 'Delete',
        'ui.close': 'Close',
        'ui.search': 'Search',
        'ui.filter': 'Filter',
        'ui.sort': 'Sort',
        
        // Messages
        'msg.login_required': 'Please login first',
        'msg.added_to_wishlist': 'Added to wishlist successfully!',
        'msg.removed_from_wishlist': 'Removed from wishlist successfully',
        'msg.already_in_wishlist': 'This item is already in your wishlist',
        'msg.review_submitted': 'Your review has been submitted!',
        'msg.no_reviews': 'No reviews yet',
        'msg.stock_low': 'Only {count} items left in stock',
        'msg.promo_invalid': 'Invalid or expired promo code',
        'msg.promo_applied': 'Discount ${amount} applied!'
    }
};

// Language management
class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('BRICKIT_lang') || 'th';
        this.translations = translations;
        this.init();
    }
    
    init() {
        // Apply initial language
        this.applyLanguage();
        
        // Add language toggle button to navbar
        this.addLanguageToggle();
        
        // Listen for language changes
        window.addEventListener('languageChanged', () => {
            this.applyLanguage();
        });
    }
    
    addLanguageToggle() {
        const navbar = document.querySelector('header .flex.items-center.justify-end.gap-4');
        if (!navbar) return;
        
        // Create language toggle button
        const langToggle = document.createElement('button');
        langToggle.id = 'langToggle';
        langToggle.className = 'size-10 flex items-center justify-center rounded-lg bg-accent-green-light dark:bg-accent-green-dark text-text-main dark:text-white hover:bg-primary/20 transition-colors';
        langToggle.innerHTML = `<span class="text-sm font-bold">${this.currentLang.toUpperCase()}</span>`;
        langToggle.title = `Switch to ${this.currentLang === 'th' ? 'English' : 'ไทย'}`;
        
        // Insert before theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            navbar.insertBefore(langToggle, themeToggle);
        } else {
            navbar.appendChild(langToggle);
        }
        
        // Add click handler
        langToggle.addEventListener('click', () => this.toggleLanguage());
    }
    
    toggleLanguage() {
        this.currentLang = this.currentLang === 'th' ? 'en' : 'th';
        localStorage.setItem('BRICKIT_lang', this.currentLang);
        
        // Update button
        const langToggle = document.getElementById('langToggle');
        if (langToggle) {
            langToggle.innerHTML = `<span class="text-sm font-bold">${this.currentLang.toUpperCase()}</span>`;
            langToggle.title = `Switch to ${this.currentLang === 'th' ? 'English' : 'ไทย'}`;
        }
        
        // Trigger language change event
        window.dispatchEvent(new Event('languageChanged'));
    }
    
    translate(key, params = {}) {
        const translation = this.translations[this.currentLang][key] || this.translations.en[key] || key;
        
        // Replace parameters {param} with values
        return translation.replace(/\{(\w+)\}/g, (match, param) => params[param] || match);
    }
    
    applyLanguage() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.translate(key);
            
            // Handle different element types
            if (element.tagName === 'INPUT' && element.type === 'placeholder') {
                element.placeholder = translation;
            } else if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // Update HTML lang attribute
        document.documentElement.lang = this.currentLang;
        
        // Update RTL if needed (for future Arabic support)
        document.documentElement.dir = this.currentLang === 'ar' ? 'rtl' : 'ltr';
    }
    
    // Helper functions
    getCurrentLang() {
        return this.currentLang;
    }
    
    isThai() {
        return this.currentLang === 'th';
    }
}

// Initialize i18n system
const i18n = new I18n();

// Make it globally available
window.i18n = i18n;
window.translate = (key, params) => i18n.translate(key, params);

function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('BRICKIT_dark', String(isDark));
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

// Cart System
let cart = JSON.parse(localStorage.getItem('BRICKIT_cart')) || [];

function openCart() {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('cart-backdrop');
    if (!drawer) return;
    
    drawer.classList.remove('translate-x-full');
    if (backdrop) {
        backdrop.classList.remove('hidden');
        requestAnimationFrame(() => backdrop.classList.remove('opacity-0'));
    }
    updateCartUI();
}

function closeCart() {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('cart-backdrop');
    if (!drawer) return;
    
    drawer.classList.add('translate-x-full');
    if (backdrop) {
        backdrop.classList.add('opacity-0');
        setTimeout(() => backdrop.classList.add('hidden'), 300);
    }
}

function addToCart(name, price, image, quantity = 1) {
    const existingItem = cart.find(item => item.name === name);
    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({ name, price, image, quantity });
    }
    saveCart();
    updateCartUI();
    showToast(`${name} added to cart!`, 'success');
}

function removeFromCart(name) {
    cart = cart.filter(item => item.name !== name);
    saveCart();
    updateCartUI();
}

function updateQuantity(name, change) {
    const item = cart.find(item => item.name === name);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            removeFromCart(name);
        } else {
            saveCart();
            updateCartUI();
        }
    }
}

function saveCart() {
    localStorage.setItem('BRICKIT_cart', JSON.stringify(cart));
}

function updateCartUI() {
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    
    if (!cartItems || !cartTotal) return;
    
    if (cart.length === 0) {
        cartItems.innerHTML = '<p class="text-slate-500 dark:text-slate-400 text-center py-8">ตะกร้าว่าง</p>';
        cartTotal.textContent = '$0.00';
        return;
    }

    cartItems.innerHTML = cart.map(item => `
        <div class="flex gap-3 p-3 bg-surface-light dark:bg-surface-dark rounded-lg">
            <img src="${item.image}" alt="${item.name}" class="w-16 h-16 object-cover rounded-lg"/>
            <div class="flex-1">
                <h4 class="font-medium text-slate-900 dark:text-white text-sm">${item.name}</h4>
                <p class="text-primary font-bold">$${item.price}</p>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="updateQuantity('${item.name}', -1)" class="w-6 h-6 rounded bg-slate-100 dark:bg-slate-800 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-700">
                    <span class="material-symbols-outlined text-[12px]">remove</span>
                </button>
                <span class="text-sm font-medium w-8 text-center">${item.quantity}</span>
                <button onclick="updateQuantity('${item.name}', 1)" class="w-6 h-6 rounded bg-slate-100 dark:bg-slate-800 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-700">
                    <span class="material-symbols-outlined text-[12px]">add</span>
                </button>
            </div>
        </div>
    `).join('');

    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    cartTotal.textContent = `$${total.toFixed(2)}`;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `p-4 rounded-lg shadow-lg transform transition-all duration-300 ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-blue-500 text-white'
    }`;
    toast.textContent = message;
    
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// User Management
function logout() {
    localStorage.removeItem('BRICKIT_user');
    window.location.href = '/login';
}

function getCurrentUser() {
    const userData = localStorage.getItem('BRICKIT_user');
    return userData ? JSON.parse(userData) : null;
}

document.addEventListener('DOMContentLoaded', () => {
    _syncDarkIcons(document.documentElement.classList.contains('dark'));
    const bd = document.getElementById('mobile-backdrop');
    if (bd) bd.addEventListener('click', closeMobileMenu);
    
    // Initialize cart
    updateCartUI();
    
    // Update user status
    const user = getCurrentUser();
    const userNavStatus = document.getElementById('user-nav-status');
    if (user && userNavStatus) {
        userNavStatus.innerHTML = `
            <span class="text-xs font-bold text-primary">${user.username}</span>
            <button onclick="logout()" class="text-[10px] text-gray-400 hover:text-red-500 underline font-bold">Logout</button>
        `;
        userNavStatus.classList.remove('hidden');
    }
});

// --- NEW FEATURES v2.0 ---

// Wishlist System
let wishlist = JSON.parse(localStorage.getItem('BRICKIT_wishlist')) || [];

function addToWishlist(productId) {
    const user = getCurrentUser();
    if (!user) {
        showToast('กรุณาเข้าสู่ระบบก่อน', 'error');
        return;
    }

    if (wishlist.includes(productId)) {
        showToast('สินค้านี้อยู่ใน wishlist แล้ว', 'warning');
        return;
    }

    wishlist.push(productId);
    localStorage.setItem('BRICKIT_wishlist', JSON.stringify(wishlist));
    
    // Sync with server
    fetch('/api/wishlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: user.id,
            product_id: productId
        })
    }).then(r => r.json()).then(data => {
        showToast('เพิ่มใน wishlist สำเร็จ!', 'success');
        updateWishlistUI();
    }).catch(error => {
        console.error('Error adding to wishlist:', error);
        showToast('เกิดข้อผิดพลาด', 'error');
    });
}

function removeFromWishlist(productId) {
    const user = getCurrentUser();
    if (!user) return;

    wishlist = wishlist.filter(id => id !== productId);
    localStorage.setItem('BRICKIT_wishlist', JSON.stringify(wishlist));
    
    // Find and remove from server
    fetch(`/api/users/${user.id}/wishlist`)
        .then(r => r.json())
        .then(items => {
            const item = items.find(i => i.product_id === productId);
            if (item) {
                fetch(`/api/wishlist/${item.id}`, { method: 'DELETE' })
                    .then(() => {
                        showToast('ลบจาก wishlist สำเร็จ', 'success');
                        updateWishlistUI();
                    });
            }
        });
}

function updateWishlistUI() {
    const wishlistButtons = document.querySelectorAll('[data-wishlist-btn]');
    wishlistButtons.forEach(btn => {
        const productId = parseInt(btn.dataset.productId);
        const icon = btn.querySelector('i');
        
        if (wishlist.includes(productId)) {
            icon.classList.remove('far');
            icon.classList.add('fas', 'text-red-500');
        } else {
            icon.classList.remove('fas', 'text-red-500');
            icon.classList.add('far');
        }
    });
}

// Review System
function submitReview(productId, rating, comment) {
    const user = getCurrentUser();
    if (!user) {
        showToast('กรุณาเข้าสู่ระบบก่อน', 'error');
        return;
    }

    fetch(`/api/products/${productId}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: user.id,
            rating: rating,
            comment: comment
        })
    }).then(r => r.json()).then(data => {
        showToast('รีวิวของคุณถูกบันทึกแล้ว!', 'success');
        loadProductReviews(productId);
    }).catch(error => {
        console.error('Error submitting review:', error);
        showToast('เกิดข้อผิดพลาด', 'error');
    });
}

function loadProductReviews(productId) {
    fetch(`/api/products/${productId}/reviews`)
        .then(r => r.json())
        .then(reviews => {
            displayReviews(reviews);
        });
}

function displayReviews(reviews) {
    const container = document.getElementById('reviews-container');
    if (!container) return;

    if (reviews.length === 0) {
        container.innerHTML = '<p class="text-gray-500">ยังไม่มีรีวิว</p>';
        return;
    }

    container.innerHTML = reviews.map(review => `
        <div class="border-b pb-4 mb-4">
            <div class="flex items-center mb-2">
                <span class="font-medium">ผู้ใช้ ${review.user_id}</span>
                <div class="ml-2 text-yellow-400">
                    ${'★'.repeat(review.rating)}${'☆'.repeat(5-review.rating)}
                </div>
                ${review.is_verified ? '<span class="ml-2 text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Verified Purchase</span>' : ''}
            </div>
            <p class="text-gray-600">${review.comment}</p>
            <p class="text-xs text-gray-400 mt-1">${new Date(review.created_at).toLocaleDateString('th-TH')}</p>
        </div>
    `).join('');
}

// Promotion System
function validatePromoCode(code, orderAmount) {
    const user = getCurrentUser();
    if (!user) {
        showToast('กรุณาเข้าสู่ระบบก่อน', 'error');
        return;
    }

    fetch('/api/promotions/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            code: code,
            user_id: user.id,
            order_amount: orderAmount
        })
    }).then(r => r.json()).then(data => {
        if (data.discount_amount) {
            showToast(`ส่วนลด $${data.discount_amount.toFixed(2)}!`, 'success');
            applyDiscount(data.discount_amount);
        }
    }).catch(error => {
        console.error('Error validating promo:', error);
        showToast('โค้ดไม่ถูกต้องหรือหมดอายุ', 'error');
    });
}

function applyDiscount(amount) {
    const totalElement = document.getElementById('cart-total');
    if (totalElement) {
        const current = parseFloat(totalElement.textContent.replace('$', ''));
        totalElement.textContent = `$${(current - amount).toFixed(2)}`;
    }
}

// Stock Check
function checkStock(productId, quantity) {
    fetch(`/api/products/${productId}/stock`)
        .then(r => r.json())
        .then(stock => {
            if (stock.quantity < quantity) {
                showToast(`สินค้าคงเหลือเพียง ${stock.quantity} ชิ้น`, 'warning');
                return false;
            }
            return true;
        })
        .catch(error => {
            console.error('Error checking stock:', error);
            return false;
        });
}

// User Activity Tracking
function trackActivity(activityType, data = {}) {
    const user = getCurrentUser();
    if (!user) return;

    fetch('/api/activities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: user.id,
            activity_type: activityType,
            data: data,
            ip_address: 'client', // Would be filled by server
            user_agent: navigator.userAgent
        })
    });
}

// Auto-track page views
document.addEventListener('DOMContentLoaded', () => {
    const user = getCurrentUser();
    if (user) {
        trackActivity('page_view', {
            page: window.location.pathname,
            title: document.title
        });
    }
});

// Initialize new features
document.addEventListener('DOMContentLoaded', () => {
    updateWishlistUI();
    
    // Add wishlist button handlers
    document.querySelectorAll('[data-wishlist-btn]').forEach(btn => {
        btn.addEventListener('click', () => {
            const productId = parseInt(btn.dataset.productId);
            if (wishlist.includes(productId)) {
                removeFromWishlist(productId);
            } else {
                addToWishlist(productId);
            }
        });
    });

    // Track product views
    document.querySelectorAll('[data-product-id]').forEach(element => {
        element.addEventListener('click', () => {
            const productId = element.dataset.productId;
            trackActivity('view_product', { product_id: productId });
        });
    });
});