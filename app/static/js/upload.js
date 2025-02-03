// Exchange rate API integration
async function getExchangeRate(date, currency, expenseLine) {
    console.log('=== getExchangeRate called ===');
    
    try {
        // Use the specific date for historical rates
        const url = `https://api.frankfurter.app/${date}?from=EUR&to=${currency}`;
        console.log('Fetching from URL:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        console.log('Full API Response:', data);
        
        if (data && data.rates && data.rates[currency]) {
            const rate = data.rates[currency];
            console.log(`Got rate for ${currency}:`, rate);
            
            // Show the exchange rate info for this specific line
            let conversionInfo = expenseLine.querySelector('.line-conversion');
            if (!conversionInfo) {
                conversionInfo = document.createElement('div');
                conversionInfo.className = 'line-conversion small text-muted mt-2';
                expenseLine.appendChild(conversionInfo);
            }
            
            // Calculate the conversion for the current amount
            const amount = parseFloat(expenseLine.querySelector('input[type="number"]').value) || 0;
            const convertedAmount = amount / rate;
            
            conversionInfo.innerHTML = `
                <div>Exchange Rate (${date})</div>
                <div class="text-primary">
                    ${amount} ${currency} × ${(1/rate).toFixed(4)} = ${convertedAmount.toFixed(2)} EUR
                </div>
            `;
            
            return rate;
        }
        throw new Error('Invalid API response');
    } catch (error) {
        console.error('Error fetching rate:', error);
        // Silently fail and return null - no error message displayed
        return null;
    }
}

// Calculate total
async function calculateTotal() {
    console.log('=== calculateTotal called ===');
    let totalEUR = 0;
    
    const lines = document.querySelectorAll('.expense-line');
    
    for (const line of lines) {
        const amountInput = line.querySelector('.amount-input');
        const currencySelect = line.querySelector('.currency-select');
        const dateInput = line.querySelector('input[type="date"]');
        
        if (!amountInput || !currencySelect || !dateInput) continue;
        
        const amount = parseFloat(amountInput.value) || 0;
        const currency = currencySelect.value;
        const date = dateInput.value || new Date().toISOString().split('T')[0];
        
        if (currency === 'EUR') {
            totalEUR += amount;
            console.log(`Adding EUR amount: ${amount}`);
        } else if (amount && currency) {
            // Get the conversion info div to extract the converted amount
            const conversionInfo = line.querySelector('.line-conversion');
            if (conversionInfo) {
                const conversionText = conversionInfo.querySelector('.text-primary').textContent;
                const convertedAmount = parseFloat(conversionText.split('=')[1].split('EUR')[0]);
                totalEUR += convertedAmount;
                console.log(`Adding converted amount: ${convertedAmount} EUR (from ${amount} ${currency})`);
            } else {
                // If no conversion info yet, get the rate and calculate
                const rate = await getExchangeRate(date, currency, line);
                if (rate) {
                    const convertedAmount = amount / rate;
                    totalEUR += convertedAmount;
                    console.log(`Adding new converted amount: ${convertedAmount} EUR (from ${amount} ${currency})`);
                }
            }
        }
    }
    
    console.log(`Total EUR: ${totalEUR}`);
    document.getElementById('total-amount').textContent = `€${totalEUR.toFixed(2)}`;
}

// Handle date changes using event delegation
document.addEventListener('change', async function(e) {
    if (e.target.matches('input[type="date"]')) {
        // Only update the specific line where date changed
        const line = e.target.closest('.expense-line');
        await updateLineCalculation(line);
        await calculateTotal();
    }
});

// Function to update a single line's calculation
async function updateLineCalculation(line) {
    const amountInput = line.querySelector('.amount-input');
    const currencySelect = line.querySelector('.currency-select');
    const dateInput = line.querySelector('input[type="date"]');
    
    if (amountInput.value && currencySelect.value) {
        await getExchangeRate(
            dateInput.value || new Date().toISOString().split('T')[0],
            currencySelect.value,
            line
        );
    }
}

// Handle currency changes using event delegation
document.addEventListener('change', async function(e) {
    if (e.target.classList.contains('currency-select')) {
        // Only update the specific line where currency changed
        const line = e.target.closest('.expense-line');
        await updateLineCalculation(line);
        await calculateTotal();
    }
});

// Handle amount input changes using event delegation
document.addEventListener('input', async function(e) {
    if (e.target.classList.contains('amount-input')) {
        // Only update the specific line where amount changed
        const line = e.target.closest('.expense-line');
        await updateLineCalculation(line);
        await calculateTotal();
    }
});

// Handle file input changes
document.addEventListener('change', async function(e) {
    if (e.target.matches('input[type="file"]')) {
        console.log('File input changed');
        const line = e.target.closest('.expense-line');
        const file = e.target.files[0];
        if (!file) {
            console.log('No file selected');
            return;
        }

        console.log('Processing file:', file.name);
        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log('Sending file for OCR processing...');
            const response = await fetch('/process_receipt', {
                method: 'POST',
                body: formData
            });
            
            console.log('Response status:', response.status);
            if (!response.ok) {
                const text = await response.text();
                console.error('Server error:', text);
                return;
            }
            
            const data = await response.json();
            console.log('OCR Results:', data);
            
            if (data.success && data.results) {
                console.log('Processing OCR results:', data.results);
                
                // Update date if found
                if (data.results.date) {
                    console.log('Setting date:', data.results.date);
                    const dateInput = line.querySelector('input[type="date"]');
                    if (dateInput) {
                        dateInput.value = data.results.date; // Should be in YYYY-MM-DD format
                        console.log('Date input updated:', dateInput.value);
                    }
                }
                
                // Update amount if found
                if (data.results.total) {
                    console.log('Setting amount:', data.results.total);
                    const amountInput = line.querySelector('.amount-input');
                    amountInput.value = data.results.total;
                    amountInput.dispatchEvent(new Event('input'));
                }
                
                // Update currency if found
                if (data.results.currency) {
                    console.log('Setting currency:', data.results.currency);
                    const currencySelect = line.querySelector('.currency-select');
                    currencySelect.value = data.results.currency;
                    currencySelect.dispatchEvent(new Event('change'));
                }
                
                // Update calculations
                await updateLineCalculation(line);
                await calculateTotal();
            } else {
                console.log('No results or unsuccessful OCR:', data);
            }
        } catch (error) {
            console.error('Error processing receipt:', error);
        }
    }
});

// Helper function to format date
function formatDate(dateStr) {
    // Add date formatting logic based on your receipt date format
    // This is a simple example assuming DD/MM/YYYY format
    const parts = dateStr.split(/[/.]/);
    if (parts.length === 3) {
        const year = parts[2].length === 2 ? '20' + parts[2] : parts[2];
        return `${year}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
    }
    return '';
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
                                    <option value="EUR">€</option>
                                    <option value="USD">$</option>
                                    <option value="GBP">£</option>
                                    <option value="NOK">kr</option>
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
        setTimeout(updateAllCalculations, 0);
    });

    // Delete line button functionality using event delegation
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-line')) {
            e.target.closest('.expense-line').remove();
            calculateTotal(); // Recalculate total after removing line
        }
    });

    // Handle expense type switching
    const expenseTypes = document.querySelectorAll('input[name="expense-type"]');
    const travelDetails = document.getElementById('travel-details');

    expenseTypes.forEach(type => {
        type.addEventListener('change', function() {
            const commentField = document.getElementById('comment-field');
            
            if (this.value === 'travel') {
                travelDetails.classList.remove('d-none');
                commentField.classList.add('d-none'); // Hide comment field for travel
            } else {
                travelDetails.classList.add('d-none');
                commentField.classList.remove('d-none'); // Show comment field for other expenses
            }
            calculateTotal(); // Recalculate total after switching
        });
    });

    // Initial calculation
    updateAllCalculations();
    
    console.log('Event listeners added');
});

// Add this function back
async function updateAllCalculations() {
    const lines = document.querySelectorAll('.expense-line');
    for (const line of lines) {
        await updateLineCalculation(line);
    }
    await calculateTotal();
}