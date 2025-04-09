fetch("https://cn-auto-backend.onrender.com/api/cars")
    .then(response => response.json())
    .then(data => console.log(data));

document.addEventListener('DOMContentLoaded', function() {
    // Переключение изображений в галерее
    const thumbnails = document.querySelectorAll('.thumbnails img');
    const mainImage = document.querySelector('.main-image');

    if (thumbnails.length && mainImage) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                mainImage.src = this.src.replace('/thumbs/', '/');
            });
        });
    }

    // Обработка формы заявки
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            alert('Заявка отправлена! Мы свяжемся с вами в ближайшее время.');
        });
    }
});

const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const mobileMenu = document.querySelector('.mobile-menu');

if (mobileMenuToggle && mobileMenu) {
    mobileMenuToggle.addEventListener('click', function() {
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