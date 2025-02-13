// Currency formatting and handling
document.addEventListener('DOMContentLoaded', function() {
    const currencyOptions = [
        { value: 'EUR', flag: 'eu', symbol: '€', label: 'EUR' },
        { value: 'NOK', flag: 'no', symbol: 'kr', label: 'NOK' },
        { value: 'USD', flag: 'us', symbol: '$', label: 'USD' },
        { value: 'GBP', flag: 'gb', symbol: '£', label: 'GBP' },
        { value: 'CHF', flag: 'ch', symbol: 'Fr.', label: 'CHF' },
        { value: 'DKK', flag: 'dk', symbol: 'kr', label: 'DKK' },
        { value: 'SEK', flag: 'se', symbol: 'kr', label: 'SEK' },
        { value: 'HUF', flag: 'hu', symbol: 'Ft', label: 'HUF' },
        { value: 'AED', flag: 'ae', symbol: 'د.إ', label: 'AED' }
    ];
    
    // Function to initialize currency selects
    function initializeCurrencySelect(select) {
        select.innerHTML = currencyOptions.map(opt => `
            <option value="${opt.value}" data-symbol="${opt.symbol}">
                ${opt.symbol} ${opt.label}
            </option>
        `).join('');
    }

    // Initialize all currency selects on page load
    document.querySelectorAll('.currency-select').forEach(initializeCurrencySelect);

    // Initialize new currency selects when adding lines
    document.addEventListener('click', function(e) {
        if (e.target.matches('.add-line')) {
            // Wait for the new line to be added
            setTimeout(() => {
                const newLine = document.querySelector('.expense-line:last-child');
                if (newLine) {
                    const newSelect = newLine.querySelector('.currency-select');
                    if (newSelect) initializeCurrencySelect(newSelect);
                }
            }, 0);
        }
    });
});

// Update currency symbols map
window.CURRENCY_SYMBOLS = {
    'EUR': '€',
    'NOK': 'kr',
    'USD': '$',
    'GBP': '£',
    'CHF': 'Fr.',
    'DKK': 'kr',
    'SEK': 'kr',
    'HUF': 'Ft',
    'AED': 'د.إ'
};