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

document.addEventListener('DOMContentLoaded', function () {
    function showAllFacets(container) {
        const items = container.querySelectorAll('.facet-item');
        items.forEach(item => item.classList.remove('hidden'));
    }
    function hideExtraFacets(container) {
        const items = container.querySelectorAll('.facet-item');
        items.forEach((item, idx) => {
            if (idx >= 8) {
                item.classList.add('hidden');
            } else {
                item.classList.remove('hidden');
            }
        });
    }
    // Toggle logic
    document.querySelectorAll('.facet-toggle').forEach(button => {
        const targetId = button.dataset.target;
        const container = document.getElementById(targetId);
        const hideLink = document.querySelector('.facet-hide-link[data-target="' + targetId + '"]');
        if (!container || !hideLink) return;
        button.addEventListener('click', function () {
            showAllFacets(container);
            button.style.display = 'none';
            hideLink.style.display = 'inline';
        });
        // Initial state: ensure only first 8 are shown
        hideExtraFacets(container);
    });
    document.querySelectorAll('.facet-hide-link').forEach(link => {
        const targetId = link.dataset.target;
        const container = document.getElementById(targetId);
        const button = document.querySelector('.facet-toggle[data-target="' + targetId + '"]');
        if (!container || !button) return;
        link.addEventListener('click', function (e) {
            e.preventDefault();
            hideExtraFacets(container);
            link.style.display = 'none';
            button.style.display = 'inline-block';
        });
    });

    // --- Facet Autocomplete Logic ---
    function setupFacetAutocomplete({inputId, suggestionsId, facetId, inputType}) {
        const input = document.getElementById(inputId);
        const suggestionsBox = document.getElementById(suggestionsId);
        const facet = document.getElementById(facetId);
        if (!input || !suggestionsBox || !facet) return;

        // Get all label elements and their text
        const labels = Array.from(facet.querySelectorAll('.facet-item'));
        const options = labels.map(label => {
            const inputEl = label.querySelector('input');
            return {
                value: inputEl.value,
                text: label.textContent.trim(),
                inputEl,
                label
            };
        });

        input.addEventListener('input', function() {
            const val = input.value.trim().toLowerCase();
            suggestionsBox.innerHTML = '';
            if (!val) {
                suggestionsBox.style.display = 'none';
                return;
            }
            // Filter options
            const matches = options.filter(opt => opt.text.toLowerCase().includes(val));
            if (matches.length === 0) {
                suggestionsBox.style.display = 'none';
                return;
            }
            matches.forEach(opt => {
                const div = document.createElement('div');
                div.className = 'facet-suggestion-item';
                div.textContent = opt.text;
                div.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    // Select the option
                    if (inputType === 'radio') {
                        opt.inputEl.checked = true;
                        // Optionally, submit the form if needed
                        const form = input.closest('form');
                        if (form) form.submit();
                    } else if (inputType === 'checkbox') {
                        opt.inputEl.checked = !opt.inputEl.checked;
                        // Optionally, trigger onchange
                        opt.inputEl.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    input.value = '';
                    suggestionsBox.innerHTML = '';
                    suggestionsBox.style.display = 'none';
                });
                suggestionsBox.appendChild(div);
            });
            suggestionsBox.style.display = 'block';
        });
        // Hide suggestions when focus is lost
        input.addEventListener('blur', function() {
            setTimeout(() => {
                suggestionsBox.innerHTML = '';
                suggestionsBox.style.display = 'none';
            }, 100);
        });
    }

    setupFacetAutocomplete({
        inputId: 'brandSearch',
        suggestionsId: 'brandSuggestions',
        facetId: 'brandFacet',
        inputType: 'radio'
    });
    setupFacetAutocomplete({
        inputId: 'countrySearch',
        suggestionsId: 'countrySuggestions',
        facetId: 'countryFacet',
        inputType: 'radio'
    });
    setupFacetAutocomplete({
        inputId: 'typeSearch',
        suggestionsId: 'typeSuggestions',
        facetId: 'typeFacet',
        inputType: 'checkbox'
    });

    function updateFacetDependencies() {
        // Get selected brand and country
        const selectedBrandInput = document.querySelector('#brandFacet input[type=radio]:checked');
        const selectedCountryInput = document.querySelector('#countryFacet input[type=radio]:checked');
        const brandCountryMap = window.brandCountryMap;

        // 1. Disable unrelated countries if a brand is selected
        if (selectedBrandInput) {
            const brandSlug = selectedBrandInput.value;
            const brandCountry = brandCountryMap[brandSlug];
            document.querySelectorAll('#countryFacet .facet-item').forEach(label => {
                const input = label.querySelector('input');
                if (label.textContent.trim() !== brandCountry) {
                    input.disabled = true;
                    label.classList.add('disabled');
                } else {
                    input.disabled = false;
                    label.classList.remove('disabled');
                }
            });
        } else {
            // Enable all countries if no brand is selected
            document.querySelectorAll('#countryFacet .facet-item').forEach(label => {
                const input = label.querySelector('input');
                input.disabled = false;
                label.classList.remove('disabled');
            });
        }

        // 2. Disable unrelated brands if a country is selected
        if (selectedCountryInput) {
            const countryName = selectedCountryInput.value;
            document.querySelectorAll('#brandFacet .facet-item').forEach(label => {
                const input = label.querySelector('input');
                const brandSlug = input.value;
                if (brandCountryMap[brandSlug] !== countryName) {
                    input.disabled = true;
                    label.classList.add('disabled');
                } else {
                    input.disabled = false;
                    label.classList.remove('disabled');
                }
            });
        } else {
            // Enable all brands if no country is selected
            document.querySelectorAll('#brandFacet .facet-item').forEach(label => {
                const input = label.querySelector('input');
                input.disabled = false;
                label.classList.remove('disabled');
            });
        }
    }

    document.querySelectorAll('#brandFacet input[type=radio]').forEach(input => {
        input.addEventListener('change', updateFacetDependencies);
    });
    document.querySelectorAll('#countryFacet input[type=radio]').forEach(input => {
        input.addEventListener('change', updateFacetDependencies);
    });
    // Run on page load
    updateFacetDependencies();

    // --- Show 'Применить' link on facet change ---
    const form = document.querySelector('.filters-sidebar form');
    function showApplyLink(linkId) {
        document.querySelectorAll('.apply-facet-link').forEach(l => l.style.display = 'none');
        const link = document.getElementById(linkId);
        if (link) link.style.display = 'inline';
    }
    // Brand
    document.querySelectorAll('#brandFacet input[type=radio]').forEach(input => {
        input.addEventListener('change', function() {
            showApplyLink('applyBrand');
        });
    });
    // Country
    document.querySelectorAll('#countryFacet input[type=radio]').forEach(input => {
        input.addEventListener('change', function() {
            showApplyLink('applyCountry');
        });
    });
    // Type (checkboxes)
    document.querySelectorAll('#typeFacet input[type=checkbox]').forEach(input => {
        input.addEventListener('change', function() {
            showApplyLink('applyType');
        });
    });
    // On click of any apply link, submit the form
    document.querySelectorAll('.apply-facet-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            link.style.display = 'none';
            if (form) form.submit();
        });
    });
});

// --- Currency Formatting ---
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.price').forEach(function (el) {
        console.log("💸 Currency formatter loaded!", el, {
            locale: el.getAttribute('data-locale'),
            currency: el.getAttribute('data-currency'),
            text: el.textContent.trim()
        });

        const locale = el.getAttribute('data-locale');
        const currency = el.getAttribute('data-currency');
        const rawText = el.textContent.trim();
        // Match the number (including decimals, spaces, commas)
        const match = rawText.match(/([\d\s.,]+)/);
        if (!locale || !currency || !match) {
            console.warn('⚠️ Missing locale, currency, or price match', {locale, currency, rawText, match});
            return;
        }
        let num = match[1];
        num = num.replace(/\s/g, '').replace(',', '.');
        const value = parseFloat(num);
        if (isNaN(value)) {
            console.warn('⚠️ Could not parse price value', {num, rawText});
            return;
        }
        try {
            el.textContent = new Intl.NumberFormat(locale, { style: 'currency', currency: currency }).format(value);
            console.log('✅ Formatted:', el.textContent);
        } catch (e) {
            el.textContent = value.toLocaleString(locale) + ' ' + currency;
            console.error('❌ Intl.NumberFormat error', {locale, currency, value, e});
        }
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
