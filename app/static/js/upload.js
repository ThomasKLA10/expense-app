// Exchange rate API integration
async function getExchangeRate(date, currency) {
    console.log('=== getExchangeRate called ===');
    
    // Format today's date
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    
    // If future date, use today's date
    const selectedDate = new Date(date);
    const useDate = selectedDate > today ? todayStr : date;
    
    console.log(`Using date ${useDate} for ${currency} (original date: ${date})`);
    
    try {
        // Use date-specific endpoint for historical rates
        const url = `https://api.frankfurter.app/${useDate}?from=EUR&to=${currency}`;
        console.log('Fetching from URL:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        console.log('Full API Response:', data);
        
        if (data && data.rates && data.rates[currency]) {
            const rate = data.rates[currency];
            console.log(`Got rate for ${currency}:`, rate);
            
            // Show the exchange rate info
            let conversionInfo = document.querySelector('.exchange-rates');
            if (!conversionInfo) {
                conversionInfo = document.createElement('div');
                conversionInfo.className = 'exchange-rates small bg-light rounded p-2 mt-2 mb-3';
                document.querySelector('.expense-lines').insertAdjacentElement('afterend', conversionInfo);
            }
            
            // Calculate the conversion for the current amount
            const amount = parseFloat(document.querySelector('input[type="number"]').value) || 0;
            const convertedAmount = amount / rate;
            
            // If using today's rate for future date, show a notice
            const dateNotice = selectedDate > today 
                ? `<span class="badge bg-info text-dark">Using today's rate</span>`
                : '';
            
            conversionInfo.innerHTML = `
                <div class="d-flex justify-content-between align-items-center text-muted mb-1">
                    <span>Exchange Rate (${data.date})</span>
                    ${dateNotice}
                </div>
                <div class="d-flex gap-3 text-dark">
                    <span>1 EUR = ${rate.toFixed(4)} ${currency}</span>
                    <span class="text-muted">|</span>
                    <span>1 ${currency} = ${(1/rate).toFixed(4)} EUR</span>
                </div>
                <div class="text-primary mt-1">
                    ${amount} ${currency} × ${(1/rate).toFixed(4)} = ${convertedAmount.toFixed(2)} EUR
                </div>
            `;
            
            return rate;
        }
        throw new Error('Invalid API response');
    } catch (error) {
        console.error('Error fetching rate:', error);
        
        // Show error message to user
        let errorDiv = document.querySelector('.exchange-rate-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'exchange-rate-error alert alert-danger mt-3';
            document.querySelector('.expense-lines').insertAdjacentElement('afterend', errorDiv);
        }
        errorDiv.innerHTML = `
            <strong>Error getting exchange rate!</strong><br>
            Please try again or contact support if the problem persists.
        `;
        return null;
    }
}

// Calculate total
async function calculateTotal() {
    console.log('=== calculateTotal called ===');
    let totalEUR = 0;
    
    // Clear any previous error messages
    const errorDiv = document.querySelector('.exchange-rate-error');
    if (errorDiv) errorDiv.remove();
    
    const lines = document.querySelectorAll('.expense-line');
    
    for (const line of lines) {
        const amountInput = line.querySelector('input[type="number"]');
        const currencySelect = line.querySelector('select');
        const dateInput = line.querySelector('input[type="date"]');
        
        if (!amountInput || !currencySelect || !dateInput) continue;
        
        const amount = parseFloat(amountInput.value) || 0;
        const currency = currencySelect.value;
        const date = dateInput.value;
        
        if (currency === 'EUR') {
            totalEUR += amount;
        } else if (date && amount && currency) {
            const rate = await getExchangeRate(date, currency);
            
            if (rate) {
                const convertedAmount = amount / rate;
                totalEUR += convertedAmount;
            }
        }
    }
    
    document.getElementById('total-amount').textContent = `€${totalEUR.toFixed(2)}`;
}

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DOM Content Loaded ===');
    
    // Debug: Log all currency selects
    const selects = document.querySelectorAll('select');
    console.log('Found currency selects:', selects.length);
    
    // Create a function to handle any input changes
    const handleInputChange = async (target) => {
        console.log('Input changed:', target.tagName, target.type, target.value);
        if (target.matches('input[type="number"], select, input[type="date"]')) {
            await calculateTotal();
        }
    };

    // Listen for changes on any input or select using event delegation
    document.addEventListener('change', async function(e) {
        console.log('Change event fired on:', e.target.tagName);
        await handleInputChange(e.target);
        
        // Remove any existing conversion displays when changing currency
        if (e.target.matches('select')) {
            const lineConversions = document.querySelectorAll('.line-conversion');
            lineConversions.forEach(el => el.remove());
        }
    });
    
    // Listen for input on number fields (for real-time updates)
    document.addEventListener('input', async function(e) {
        console.log('Input event fired on:', e.target.tagName);
        await handleInputChange(e.target);
    });

    // Add line button functionality
    document.querySelector('.add-line').addEventListener('click', function() {
        const template = `
            <div class="expense-line mb-3">
                <div class="row g-3 align-items-center">
                    <div class="col-md-2">
                        <input type="date" class="form-control" placeholder="Date">
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" placeholder="Description">
                    </div>
                    <div class="col-md-3">
                        <div class="input-group">
                            <div class="input-group-text p-0">
                                <select class="form-select border-0 currency-select" style="width: 80px">
                                    <!-- Options will be populated by currency.js -->
                                </select>
                            </div>
                            <input type="number" class="form-control amount-input" step="0.01" placeholder="0.00">
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="input-group">
                            <input type="file" class="form-control" accept="image/*,.pdf">
                        </div>
                    </div>
                    <div class="col-md-1">
                        <button type="button" class="btn btn-outline-danger delete-line">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.querySelector('.expense-lines').insertAdjacentHTML('beforeend', template);
        calculateTotal(); // Recalculate total after adding new line
    });

    // Delete line button functionality using event delegation
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-line')) {
            e.target.closest('.expense-line').remove();
            calculateTotal(); // Recalculate total after removing line
        }
    });

    // Initial calculation
    calculateTotal();
    
    console.log('Event listeners added');
});