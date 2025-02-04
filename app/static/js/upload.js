// Exchange rate API integration
async function getExchangeRate(from, to, date) {
    try {
        // If same currency, return 1
        if (from === to) {
            return 1;
        }
        
        const url = `https://api.frankfurter.app/${date}?from=${from}&to=${to}`;
        console.log('Fetching from URL:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.rates && data.rates[to]) {
            return data.rates[to];
        } else {
            throw new Error('Invalid API response');
        }
    } catch (error) {
        console.error('Error fetching rate:', error);
        return 1; // Fallback to 1:1 rate
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
        
        if (amount) {  // Only process if there's an amount
            if (currency === 'EUR') {
                totalEUR += amount;
                console.log(`Adding EUR amount: ${amount}`);
            } else {
                const rate = await getExchangeRate(currency, 'EUR', date);
                const convertedAmount = amount * (1/rate);  // Fixed conversion calculation
                totalEUR += convertedAmount;
                console.log(`Adding converted amount: ${convertedAmount} EUR (from ${amount} ${currency})`);
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
    const calculator = line.querySelector('.calculator');
    
    if (amountInput.value && currencySelect.value !== 'EUR') {
        const date = dateInput.value || new Date().toISOString().split('T')[0];
        const rate = await getExchangeRate(currencySelect.value, 'EUR', date);
        const amount = parseFloat(amountInput.value);
        const convertedAmount = (amount / rate).toFixed(2);
        const conversionText = line.querySelector('.conversion-text');
        if (conversionText) {
            conversionText.innerHTML = `
                <span>Historic rate: 1 ${currencySelect.value} = ${(1/rate).toFixed(4)} EUR</span>
                <span class="calculation">${amount} × ${(1/rate).toFixed(4)} = ${convertedAmount} EUR</span>
            `;
        }
        calculator.style.display = 'block';
    } else {
        calculator.style.display = 'none';
    }
}

// Handle currency changes using event delegation
document.addEventListener('change', async function(e) {
    if (e.target.classList.contains('currency-select')) {
        const line = e.target.closest('.expense-line');
        const calculator = line.querySelector('.calculator');
        const amountInput = line.querySelector('.amount-input');
        const dateInput = line.querySelector('input[type="date"]');
        
        // Show/hide calculator based on currency
        if (calculator) {
            calculator.style.display = e.target.value !== 'EUR' ? 'block' : 'none';
            
            // Update conversion display if amount exists
            if (amountInput.value && e.target.value !== 'EUR') {
                const date = dateInput.value || new Date().toISOString().split('T')[0];
                const rate = await getExchangeRate(e.target.value, 'EUR', date);
                const amount = parseFloat(amountInput.value);
                const convertedAmount = (amount / rate).toFixed(2);
                const conversionText = line.querySelector('.conversion-text');
                if (conversionText) {
                    conversionText.textContent = `${amount} ${e.target.value} = ${convertedAmount} EUR`;
                }
            }
        }
        
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
        const line = e.target.closest('.expense-line');
        const viewButton = line.querySelector('.view-receipt');
        const file = e.target.files[0];
        
        // Enable/disable view button based on file selection
        viewButton.disabled = !file;
        
        // Store the file itself instead of the URL
        viewButton.dataset.fileIndex = line.dataset.fileIndex || Date.now().toString();
        if (file) {
            // Store the file in a map using the index
            if (!window.uploadedFiles) window.uploadedFiles = new Map();
            window.uploadedFiles.set(viewButton.dataset.fileIndex, file);
        }
        
        console.log('Sending file for OCR processing...');
        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log('Sending file for OCR processing...');
            const response = await fetch('/process_receipt', {
                method: 'POST',
                body: formData
            });
            
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('OCR Results:', data);
            
            // Check if we have results directly (no success wrapper)
            const results = data.results || data;
            console.log('Processing results:', results);
            
            if (results) {
                // Update date if found
                if (results.date) {
                    console.log('Setting date:', results.date);
                    const dateInput = line.querySelector('input[type="date"]');
                    if (dateInput) {
                        dateInput.value = results.date;
                        dateInput.dispatchEvent(new Event('change'));
                    }
                }
                
                // Update amount if found
                if (results.total) {
                    console.log('Setting amount:', results.total);
                    const amountInput = line.querySelector('.amount-input');
                    if (amountInput) {
                        amountInput.value = results.total;
                        amountInput.dispatchEvent(new Event('input'));
                    }
                }
                
                // Update currency if found
                if (results.currency) {
                    console.log('Setting currency:', results.currency);
                    const currencySelect = line.querySelector('.currency-select');
                    if (currencySelect) {
                        currencySelect.value = results.currency;
                        currencySelect.dispatchEvent(new Event('change'));
                        
                        // Show calculator for non-EUR currencies
                        const calculator = line.querySelector('.calculator');
                        if (calculator) {
                            calculator.style.display = results.currency !== 'EUR' ? 'block' : 'none';
                            
                            // Update conversion display
                            if (results.total && results.currency !== 'EUR') {
                                const rate = await getExchangeRate(results.currency, 'EUR', results.date || new Date().toISOString().split('T')[0]);
                                const convertedAmount = (results.total / rate).toFixed(2);
                                const conversionText = calculator.querySelector('.text-primary');
                                if (conversionText) {
                                    conversionText.textContent = `${results.total} ${results.currency} = ${convertedAmount} EUR`;
                                }
                            }
                        }
                    }
                }
                
                // Update calculations
                await updateLineCalculation(line);
                await calculateTotal();
            } else {
                console.log('No OCR results found');
            }
        } catch (error) {
            console.error('Error processing receipt:', error);
        }
    }
});

// Add click handler for view receipt button
document.addEventListener('click', function(e) {
    if (e.target.closest('.view-receipt')) {
        const button = e.target.closest('.view-receipt');
        const fileIndex = button.dataset.fileIndex;
        const file = window.uploadedFiles.get(fileIndex);
        
        if (!file) return;
        
        const fileUrl = URL.createObjectURL(file);
        const fileType = file.type;
        const preview = document.getElementById('receipt-preview');
        
        // Clear previous content
        preview.innerHTML = '';
        
        if (fileType.startsWith('image/')) {
            // Handle image files
            const img = document.createElement('img');
            img.src = fileUrl;
            img.classList.add('img-fluid');
            preview.appendChild(img);
        } else if (fileType === 'application/pdf') {
            // Handle PDF files
            const iframe = document.createElement('iframe');
            iframe.src = fileUrl;
            preview.appendChild(iframe);
        }
        
        // Store the current URL to revoke it later
        preview.dataset.currentUrl = fileUrl;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('receiptModal'));
        modal.show();
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
                        <div class="calculator">
                            <div class="line-conversion">
                                <small class="text-primary conversion-text"></small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="input-group">
                            <input type="file" class="form-control" accept="image/*,.pdf">
                            <button type="button" class="btn btn-outline-secondary view-receipt" disabled>
                                <i class="bi bi-eye"></i>
                            </button>
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
            const line = e.target.closest('.expense-line');
            const viewButton = line.querySelector('.view-receipt');
            if (viewButton && viewButton.dataset.fileIndex) {
                window.uploadedFiles.delete(viewButton.dataset.fileIndex);
            }
            line.remove();
            calculateTotal();
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

// Make sure to call calculateTotal whenever values change
async function handleInputChange(target) {
    if (!target) return;
    
    const line = target.closest('.expense-line');
    if (line) {
        await updateLineCalculation(line);
        await calculateTotal();
    }
}

// Clean up object URLs when modal is hidden
document.getElementById('receiptModal').addEventListener('hidden.bs.modal', function () {
    const preview = document.getElementById('receipt-preview');
    const currentUrl = preview.dataset.currentUrl;
    
    if (currentUrl) {
        URL.revokeObjectURL(currentUrl);
    }
    
    preview.innerHTML = '';
    preview.dataset.currentUrl = '';
});