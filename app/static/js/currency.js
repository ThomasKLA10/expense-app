// Currency formatting and handling
document.addEventListener('DOMContentLoaded', function() {
    const select = document.getElementById('currency');
    if (select) {
        const options = [
            { value: 'EUR', flag: 'eu', symbol: '€', label: 'EUR' },
            { value: 'GBP', flag: 'gb', symbol: '£', label: 'GBP' },
            { value: 'NOK', flag: 'no', symbol: 'kr', label: 'NOK' },
            { value: 'USD', flag: 'us', symbol: '$', label: 'USD' }
        ];
        
        select.innerHTML = options.map(opt => `
            <option value="${opt.value}">
                <span class="fi fi-${opt.flag}"></span> ${opt.symbol} ${opt.label}
            </option>
        `).join('');
    }
});