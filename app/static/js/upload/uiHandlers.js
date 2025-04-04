import { updateLineCalculation, calculateTotal, updateAllCalculations, handleInputChange } from './calculations.js';
import { handleFileInputChange, handleViewReceipt, allowedFile } from './fileHandling.js';

// Add line button functionality
function addExpenseLine() {
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
                            <select class="form-select border-0 currency-select" style="width: 100px">
                                <option value="EUR">€ EUR</option>
                                <option value="USD">$ USD</option>
                                <option value="GBP">£ GBP</option>
                                <option value="NOK">kr NOK</option>
                                <option value="CHF">Fr. CHF</option>
                                <option value="DKK">kr DKK</option>
                                <option value="SEK">kr SEK</option>
                                <option value="HUF">Ft HUF</option>
                                <option value="AED">د.إ AED</option>
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
}

// Delete line functionality
function deleteExpenseLine(e) {
    const line = e.target.closest('.expense-line');
    const viewButton = line.querySelector('.view-receipt');
    if (viewButton && viewButton.dataset.fileIndex) {
        window.uploadedFiles.delete(viewButton.dataset.fileIndex);
    }
    line.remove();
    calculateTotal();
}

// Handle expense type switching
function handleExpenseTypeChange(e) {
    const travelDetails = document.getElementById('travel-details');
    const commentField = document.getElementById('comment-field');
    
    if (e.target.value === 'travel') {
        travelDetails.classList.remove('d-none');
        commentField.classList.add('d-none'); // Hide comment field for travel
    } else {
        travelDetails.classList.add('d-none');
        commentField.classList.remove('d-none'); // Show comment field for other expenses
    }
    calculateTotal(); // Recalculate total after switching
}

// Create drop zone
function createDropZone() {
    const dropZone = document.createElement('div');
    dropZone.id = 'drop-zone';
    dropZone.className = 'drop-zone mb-4';
    dropZone.innerHTML = `
        <div class="drop-zone-content">
            <i class="bi bi-cloud-upload"></i>
            <p>Drag and drop receipt files here</p>
            <p class="text-muted small">or click the "Add Line" button to add manually</p>
        </div>
    `;

    // Insert drop zone before the expense lines container
    const expenseLinesContainer = document.querySelector('.expense-lines');
    if (expenseLinesContainer) {
        expenseLinesContainer.parentNode.insertBefore(dropZone, expenseLinesContainer);
        console.log('Drop zone created and inserted');
        return dropZone;
    }
    
    console.log('Expense lines container not found');
    return null;
}

// Handle form submission
function handleFormSubmission(e) {
    e.preventDefault();
    console.log('Submit button clicked');
    
    // Get the submit button
    const submitButton = document.getElementById('submit-form');
    
    // Prevent multiple submissions
    if (submitButton.disabled) {
        console.log('Form already being submitted');
        return;
    }
    
    // Disable the button and show loading state
    submitButton.disabled = true;
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';
    
    // Validate required fields
    const expenseLines = document.querySelectorAll('.expense-line');
    let isValid = true;
    let errorMessage = '';

    // Check if there's at least one expense line
    if (expenseLines.length === 0) {
        errorMessage = 'Please add at least one expense line';
        isValid = false;
    }

    // Check each expense line
    expenseLines.forEach((line, index) => {
        const dateInput = line.querySelector('input[type="date"]');
        const descriptionInput = line.querySelector('input[type="text"]');
        const amountInput = line.querySelector('.amount-input');
        
        if (!dateInput?.value || !descriptionInput?.value || !amountInput?.value) {
            errorMessage = `Please fill all required fields in expense line ${index + 1}`;
            isValid = false;
        }
    });

    // Check comment field for "other" expenses
    const expenseType = document.querySelector('input[name="expense-type"]:checked')?.value || 'other';
    if (expenseType === 'other') {
        const commentInput = document.getElementById('comment');
        if (!commentInput || !commentInput.value.trim()) {
            errorMessage = 'Please add a comment for other expenses';
            isValid = false;
        }
    }

    if (!isValid) {
        alert(errorMessage);
        // Re-enable the button if validation fails
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
        return;
    }

    // Create FormData object
    const formData = new FormData();
    formData.append('expense-type', expenseType);
    
    // Add comment if it's "other" expense type
    if (expenseType === 'other') {
        formData.append('comment', document.getElementById('comment').value);
    }
    
    // Add travel details if it's "travel" expense type
    if (expenseType === 'travel') {
        formData.append('purpose', document.querySelector('input[name="purpose"]').value);
        formData.append('from', document.querySelector('input[name="from"]').value);
        formData.append('to', document.querySelector('input[name="to"]').value);
        formData.append('departure', document.querySelector('input[name="departure"]').value);
        formData.append('return', document.querySelector('input[name="return"]').value);
    }
    
    // Add expense lines with both original and converted amounts
    expenseLines.forEach((line, index) => {
        const dateInput = line.querySelector('input[type="date"]').value;
        const descriptionInput = line.querySelector('input[type="text"]').value;
        const originalAmount = line.querySelector('.amount-input').value;
        const originalCurrency = line.querySelector('.currency-select').value;
        
        // Get the converted EUR amount from the calculator display
        let eurAmount = originalAmount;
        if (originalCurrency !== 'EUR') {
            const calculatorText = line.querySelector('.calculation');
            if (calculatorText) {
                const match = calculatorText.textContent.match(/= ([\d.]+) EUR$/);
                if (match) {
                    eurAmount = Number(match[1]).toFixed(2);
                }
            }
        } else {
            eurAmount = Number(originalAmount).toFixed(2);
        }
        
        formData.append(`date[]`, dateInput);
        formData.append(`description[]`, descriptionInput);
        formData.append(`amount[]`, eurAmount);  // EUR amount
        formData.append(`currency[]`, originalCurrency);  // Original currency
        formData.append(`original_amount[]`, originalAmount);  // Original amount
        
        // Add receipt file if present
        const fileInput = line.querySelector('input[type="file"]');
        if (fileInput.files[0]) {
            formData.append(`receipt[]`, fileInput.files[0]);
        }
    });
    
    // Submit the form
    fetch('/submit_expense', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            // Re-enable the button on error
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Re-enable the button on error
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
        
        const errorMessage = document.createElement('div');
        errorMessage.className = 'alert alert-danger mt-3';
        errorMessage.textContent = 'Unable to submit the form. Please check your inputs and try again.';
        document.getElementById('expense-form').prepend(errorMessage);
    });
}

// Handle file drop
async function handleFileDrop(e, dropZone) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drop-zone-active');
    
    const files = Array.from(e.dataTransfer.files);
    console.log('Files dropped:', files);
    
    // Process files sequentially
    for (const file of files) {
        if (allowedFile(file.name)) {
            console.log('Processing file:', file.name);
            
            // Create new line and wait for it to be processed before moving to next file
            await new Promise(resolve => {
                const addLineBtn = document.querySelector('.add-line');
                if (addLineBtn) {
                    console.log('Clicking add line button');
                    addLineBtn.click();
                    
                    setTimeout(async () => {
                        const newLine = document.querySelector('.expense-line:last-child');
                        if (newLine) {
                            const fileInput = newLine.querySelector('input[type="file"]');
                            if (fileInput) {
                                console.log('Setting file in input');
                                const dataTransfer = new DataTransfer();
                                dataTransfer.items.add(file);
                                fileInput.files = dataTransfer.files;
                                
                                // Trigger change event and wait for it to complete
                                const event = new Event('change', { bubbles: true });
                                fileInput.dispatchEvent(event);
                                
                                // Wait for the OCR processing to complete
                                await new Promise(r => setTimeout(r, 1000));
                                resolve();
                            } else {
                                console.log('No file input found in new line');
                                resolve();
                            }
                        } else {
                            console.log('No new line created');
                            resolve();
                        }
                    }, 100);
                } else {
                    console.log('Add line button not found');
                    resolve();
                }
            });
        } else {
            console.warn('Invalid file type:', file.name);
        }
    }
}

export { 
    addExpenseLine, 
    deleteExpenseLine, 
    handleExpenseTypeChange, 
    createDropZone, 
    handleFormSubmission,
    handleFileDrop
}; 