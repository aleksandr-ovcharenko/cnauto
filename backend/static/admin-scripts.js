// admin-scripts.js: Currency formatting for admin pages

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.price').forEach(function (el) {
        console.log("[ADMIN] 💸 Currency formatter loaded!", el, {
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
            console.warn('[ADMIN] ⚠️ Missing locale, currency, or price match', {locale, currency, rawText, match});
            return;
        }
        let num = match[1];
        num = num.replace(/\s/g, '').replace(',', '.');
        const value = parseFloat(num);
        if (isNaN(value)) {
            console.warn('[ADMIN] ⚠️ Could not parse price value', {num, rawText});
            return;
        }
        try {
            el.textContent = new Intl.NumberFormat(locale, { style: 'currency', currency: currency }).format(value);
            console.log('[ADMIN] ✅ Formatted:', el.textContent);
        } catch (e) {
            el.textContent = value.toLocaleString(locale) + ' ' + currency;
            console.error('[ADMIN] ❌ Intl.NumberFormat error', {locale, currency, value, e});
        }
    });
});
