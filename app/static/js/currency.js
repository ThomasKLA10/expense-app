// Currency formatting and handling
document.addEventListener('DOMContentLoaded', function() {
    const currencyOptions = [
        { value: 'EUR', flag: 'eu', symbol: '€', label: 'EUR' },
        { value: 'GBP', flag: 'gb', symbol: '£', label: 'GBP' },
        { value: 'NOK', flag: 'no', symbol: 'kr', label: 'NOK' },
        { value: 'USD', flag: 'us', symbol: '$', label: 'USD' }
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

// Export for use in other files
window.CURRENCY_SYMBOLS = {
    'EUR': '€',
    'GBP': '£',
    'NOK': 'kr',
    'USD': '$'
};