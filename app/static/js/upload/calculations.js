import { getExchangeRate } from './api.js';

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
        
        const amount = sanitizeAmount(amountInput.value);
        const currency = currencySelect.value;
        const date = dateInput.value || new Date().toISOString().split('T')[0];
        
        if (amount) {  // Only process if there's an amount
            if (currency === 'EUR') {
                totalEUR += amount;
                console.log(`Adding EUR amount: ${amount}`);
            } else {
                const rate = await getExchangeRate(currency, 'EUR', date);
                const convertedAmount = amount * rate;
                totalEUR += convertedAmount;
                console.log(`Adding converted amount: ${convertedAmount} EUR (from ${amount} ${currency})`);
            }
        }
    }
    
    console.log(`Total EUR: ${totalEUR}`);
    document.getElementById('total-amount').textContent = `€${totalEUR.toFixed(2)}`;
}

// Function to update a single line's calculation
async function updateLineCalculation(line) {
    const amountInput = line.querySelector('.amount-input');
    const currencySelect = line.querySelector('.currency-select');
    const dateInput = line.querySelector('input[type="date"]');
    const calculator = line.querySelector('.calculator');
    
    // Sanitize the input value to ensure it's positive
    if (amountInput.value) {
        const sanitizedValue = sanitizeAmount(amountInput.value);
        if (sanitizedValue.toString() !== amountInput.value) {
            amountInput.value = sanitizedValue.toString();
        }
    }
    
    if (amountInput.value && currencySelect.value !== 'EUR') {
        const date = dateInput.value || new Date().toISOString().split('T')[0];
        const rate = await getExchangeRate(currencySelect.value, 'EUR', date);
        const amount = sanitizeAmount(amountInput.value);
        const convertedAmount = (amount * rate).toFixed(2);
        const conversionText = line.querySelector('.conversion-text');
        if (conversionText) {
            conversionText.innerHTML = `
                <span>Historic rate: 1 ${currencySelect.value} = ${rate.toFixed(4)} EUR</span>
                <span class="calculation">${amount} × ${rate.toFixed(4)} = ${convertedAmount} EUR</span>
            `;
        }
        calculator.style.display = 'block';
    } else {
        calculator.style.display = 'none';
    }
}

// Update all calculations
async function updateAllCalculations() {
    const lines = document.querySelectorAll('.expense-line');
    for (const line of lines) {
        await updateLineCalculation(line);
    }
    await calculateTotal();
}

// Handle input change
async function handleInputChange(target) {
    if (!target) return;
    
    const line = target.closest('.expense-line');
    if (line) {
        await updateLineCalculation(line);
        await calculateTotal();
    }
}

// Add this function to sanitize input values
function sanitizeAmount(value) {
    // Convert to number and ensure it's positive
    const num = Math.abs(parseFloat(value) || 0);
    return isNaN(num) ? 0 : num;
}

export { calculateTotal, updateLineCalculation, updateAllCalculations, handleInputChange, sanitizeAmount }; 