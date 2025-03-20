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

// Export functions
export { getExchangeRate, formatDate }; 