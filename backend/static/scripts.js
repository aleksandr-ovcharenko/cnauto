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

// Скрипт для изменения класса sticky при прокрутке страницы
window.addEventListener('scroll', function() {
    const header = document.querySelector('.header');
    if (window.scrollY > 50) { // Если прокрутка больше 50px
        header.classList.add('sticky');
    } else {
        header.classList.remove('sticky');
    }
});

// Swiper для популярных авто
new Swiper('.swiper-popular', {
    loop: true,
    spaceBetween: 20,
    slidesPerView: 1,
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev'
    },
    autoplay: {
        delay: 3000,
        disableOnInteraction: false,
    },
    breakpoints: {
        768: { slidesPerView: 2 },
        1024: { slidesPerView: 3 }
    }
});

// Swiper для каталога
new Swiper('.swiper-catalog', {
    spaceBetween: 20,
    slidesPerView: 1.1,
    breakpoints: {
        768: { slidesPerView: 2 },
        1024: { slidesPerView: 3 }
    }
});

thumbs.forEach(thumb => {
    thumb.addEventListener('click', function () {
        mainImage.src = this.src.replace('/thumbs/', '/');

        thumbs.forEach(t => t.classList.remove('active'));
        this.classList.add('active');
    });
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

console.log("main image", document.querySelector('.main-image'));
console.log("thumbnails", document.querySelectorAll('.thumbnails img'));


document.addEventListener('DOMContentLoaded', function () {
    const mainImage = document.querySelector('.main-image');
    const thumbnails = document.querySelectorAll('.thumbnails img');

    console.log("Main:", mainImage, "Thumbnails:", thumbnails);

    if (mainImage && thumbnails.length) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function () {
                mainImage.src = this.src;
            });
        });
    }
});

thumbnails.forEach(thumb => {
    thumb.addEventListener('click', function () {
        mainImage.src = this.src;

        thumbnails.forEach(t => t.classList.remove('selected'));
        this.classList.add('selected');
    });
});