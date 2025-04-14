// Facet toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    const closeButton = document.querySelector('.mobile-menu-close');
    const body = document.body;

    function closeMenu() {
        menuToggle.classList.remove('active');
        mobileMenu.classList.remove('active');
        body.style.overflow = '';
    }

    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', function() {
            menuToggle.classList.toggle('active');
            mobileMenu.classList.toggle('active');
            body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : '';
        });
    }

    // Close button handler
    if (closeButton) {
        closeButton.addEventListener('click', closeMenu);
    }

    // Close mobile menu when clicking on a link
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');
    mobileLinks.forEach(link => {
        link.addEventListener('click', closeMenu);
    });

    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
            closeMenu();
        }
    });

    // Facet toggles
    const facetToggles = document.querySelectorAll('.facet-toggle');
    
    facetToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const facetItems = this.closest('.facet-group').querySelector('.facet-items');
            facetItems.classList.toggle('collapsed');
            this.textContent = facetItems.classList.contains('collapsed') ? 'Показать все' : 'Скрыть';
        });
    });
});
