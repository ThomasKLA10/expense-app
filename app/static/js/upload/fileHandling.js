import { updateLineCalculation, calculateTotal } from './calculations.js';

// Helper function to check allowed file types
function allowedFile(filename) {
    const allowedExtensions = ['pdf', 'png', 'jpg', 'jpeg', 'gif'];
    const extension = filename.split('.').pop().toLowerCase();
    return allowedExtensions.includes(extension);
}

// Process receipt with OCR
async function processReceiptOCR(file, line) {
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
            
            // Update amount if found - format to 2 decimal places
            if (results.total) {
                // Format to exactly 2 decimal places
                const formattedTotal = parseFloat(results.total).toFixed(2);
                console.log('Setting amount:', formattedTotal);
                const amountInput = line.querySelector('.amount-input');
                if (amountInput) {
                    amountInput.value = formattedTotal;
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

// Handle file input changes
async function handleFileInputChange(e) {
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
        
        // Process with OCR
        await processReceiptOCR(file, line);
    }
}

// Handle view receipt button
function handleViewReceipt(e) {
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

export { allowedFile, processReceiptOCR, handleFileInputChange, handleViewReceipt }; 