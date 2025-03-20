import { calculateTotal, updateAllCalculations, handleInputChange } from './calculations.js';
import { handleFileInputChange, handleViewReceipt } from './fileHandling.js';
import { 
    addExpenseLine, 
    deleteExpenseLine, 
    handleExpenseTypeChange, 
    createDropZone, 
    handleFormSubmission,
    handleFileDrop
} from './uiHandlers.js';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DOM Content Loaded ===');
    
    // Initialize global uploadedFiles map
    window.uploadedFiles = new Map();
    
    // Debug: Log all currency selects
    const selects = document.querySelectorAll('select');
    console.log('Found currency selects:', selects.length);
    
    // Listen for changes on any input or select using event delegation
    document.addEventListener('change', async function(e) {
        console.log('Change event fired on:', e.target.tagName);
        
        // Handle different types of changes
        if (e.target.matches('input[type="date"]')) {
            // Only update the specific line where date changed
            const line = e.target.closest('.expense-line');
            await updateLineCalculation(line);
            await calculateTotal();
        } else if (e.target.classList.contains('currency-select')) {
            const line = e.target.closest('.expense-line');
            await updateLineCalculation(line);
            await calculateTotal();
        } else if (e.target.matches('input[type="file"]')) {
            await handleFileInputChange(e);
        } else if (e.target.matches('input[name="expense-type"]')) {
            handleExpenseTypeChange(e);
        } else {
            await handleInputChange(e.target);
        }
    });
    
    // Listen for input on number fields (for real-time updates)
    document.addEventListener('input', async function(e) {
        console.log('Input event fired on:', e.target.tagName);
        
        if (e.target.classList.contains('amount-input')) {
            // Only update the specific line where amount changed
            const line = e.target.closest('.expense-line');
            await updateLineCalculation(line);
            await calculateTotal();
        } else {
            await handleInputChange(e.target);
        }
    });

    // Add line button functionality
    document.querySelector('.add-line').addEventListener('click', addExpenseLine);

    // Delete line button functionality using event delegation
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-line')) {
            deleteExpenseLine(e);
        } else if (e.target.closest('.view-receipt')) {
            handleViewReceipt(e);
        }
    });

    // Handle expense type switching
    const expenseTypes = document.querySelectorAll('input[name="expense-type"]');
    expenseTypes.forEach(type => {
        type.addEventListener('change', handleExpenseTypeChange);
    });

    // Prevent default drag behaviors on the entire document
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    // Create and set up drop zone
    const dropZone = createDropZone();
    if (dropZone) {
        // Handle drag and drop events specifically for the drop zone
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('drop-zone-active');
                console.log('Drag event:', eventName);
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('drop-zone-active');
                console.log('Drag event:', eventName);
            });
        });

        // Handle dropped files
        dropZone.addEventListener('drop', async function(e) {
            await handleFileDrop(e, dropZone);
        });
    }

    // Set up form submission
    const submitButton = document.getElementById('submit-form');
    if (submitButton) {
        submitButton.addEventListener('click', handleFormSubmission);
    } else {
        console.error('Submit button not found!');
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

    // Initial calculation
    updateAllCalculations();
    
    console.log('Event listeners added');
}); 