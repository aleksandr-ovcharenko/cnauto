fetch("https://cn-auto-backend.onrender.com/api/cars")
    .then(response => response.json())
    .then(data => console.log(data));

// Обработка формы заявки
const contactForm = document.querySelector('.contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
        e.preventDefault();
        alert('Заявка отправлена! Мы свяжемся с вами в ближайшее время.');
    });
}


const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const mobileMenu = document.querySelector('.mobile-menu');

if (mobileMenuToggle && mobileMenu) {
    mobileMenuToggle.addEventListener('click', function () {
        this.classList.toggle('active');
        mobileMenu.classList.toggle('active');
    });
}

// Закрытие меню при клике на ссылку
const mobileLinks = document.querySelectorAll('.mobile-nav-link');
mobileLinks.forEach(link => {
    link.addEventListener('click', () => {
        mobileMenu.classList.remove('active');
        mobileMenuToggle.classList.remove('active');
    });
});

// Скрипт для изменения класса sticky при прокрутке страницы
window.addEventListener('scroll', function () {
    const header = document.querySelector('.header');
    if (window.scrollY > 50) { // Если прокрутка больше 50px
        header.classList.add('sticky');
    } else {
        header.classList.remove('sticky');
    }
});

// Swiper для популярных авто
new Swiper('.swiper-popular', {
    loop: true, spaceBetween: 20, slidesPerView: 1, navigation: {
        nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev'
    }, autoplay: {
        delay: 3000, disableOnInteraction: false,
    }, breakpoints: {
        768: {slidesPerView: 2}, 1024: {slidesPerView: 3}
    }
});

// Swiper для каталога
new Swiper('.swiper-catalog', {
    spaceBetween: 20, slidesPerView: 1.1, breakpoints: {
        768: {slidesPerView: 2}, 1024: {slidesPerView: 3}
    }
});

fetch("https://cn-auto-backend.onrender.com/api/cars")
    .then(res => res.json())
    .then(data => {
        console.log(data);
        // update UI here if needed
    })
    .catch(err => {
        console.error("Ошибка при получении данных:", err);
    });

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
});

// Facet toggle logic без id
document.addEventListener('DOMContentLoaded', function () {
    const toggleButtons = document.querySelectorAll(".facet-toggle");

    toggleButtons.forEach(button => {
        const targetId = button.dataset.target;
        const container = document.getElementById(targetId);

        if (!container) return;

        button.addEventListener("click", () => {
            const hiddenItems = container.querySelectorAll(".facet-item.hidden");
            const isExpanded = button.dataset.expanded === "true";

            hiddenItems.forEach(item => {
                item.style.display = isExpanded ? "none" : "flex";
            });

            button.dataset.expanded = (!isExpanded).toString();
            button.textContent = isExpanded ? "Показать ещё" : "Скрыть";
        });
    });
});


window.addEventListener('load', function () {
    const mainImage = document.querySelector('.main-image');
    const thumbnails = document.querySelectorAll('.product-thumbs .car-thumb');

    console.log("📸 Найдено миниатюр:", thumbnails.length);
    if (!mainImage) {
        console.warn("❌ Главная картинка не найдена (main-image)");
        return;
    }

    if (thumbnails.length === 0) {
        console.warn("❌ Миниатюры не найдены в DOM");
        return;
    }

    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function () {
            const fullSrc = this.getAttribute('data-full') || this.src;
            console.log("🔁 Замена картинки:", fullSrc);

            mainImage.src = fullSrc;

            thumbnails.forEach(t => t.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
});
