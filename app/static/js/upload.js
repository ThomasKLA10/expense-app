// Amount formatting
document.addEventListener('DOMContentLoaded', function() {
    const amountInput = document.getElementById('amount');
    if (amountInput) {
        amountInput.addEventListener('input', function(e) {
            let value = this.value.replace(/[^\d.]/g, '');
            let parts = value.split('.');
            if (parts.length > 2) {
                parts = [parts[0], parts.slice(1).join('')];
            }
            if (parts[0].length > 3) {
                parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            }
            if (parts[1]) {
                parts[1] = parts[1].slice(0, 2);
            }
            this.value = parts.join('.');
        });
    }
});

// Form submission
const uploadForm = document.querySelector('form');
if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
        const amountInput = document.getElementById('amount');
        const formattedValue = amountInput.value;
        const plainNumber = formattedValue.replace(/,/g, '');
        amountInput.value = plainNumber;
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('receipt');
    const previewSection = document.getElementById('preview-section');
    const imagePreview = document.getElementById('image-preview');
    const pdfPreview = document.getElementById('pdf-preview');
    const pdfFilename = pdfPreview.querySelector('.pdf-filename');
    const deleteButton = document.getElementById('delete-preview');
    const travelFields = document.getElementById('travel-fields');
    const categoryInputs = document.querySelectorAll('input[name="category"]');

    // Handle file selection
    fileInput.addEventListener('change', function(e) {
        const file = this.files[0];
        if (file) {
            previewSection.classList.remove('d-none');
            
            if (file.type.startsWith('image/')) {
                imagePreview.classList.remove('d-none');
                pdfPreview.classList.add('d-none');
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.querySelector('img').src = e.target.result;
                };
                reader.readAsDataURL(file);
            } else if (file.type === 'application/pdf') {
                pdfPreview.classList.remove('d-none');
                imagePreview.classList.add('d-none');
                pdfFilename.textContent = file.name;
            }
        } else {
            previewSection.classList.add('d-none');
        }
    });

    // Handle delete button
    deleteButton.addEventListener('click', function() {
        fileInput.value = '';
        previewSection.classList.add('d-none');
        imagePreview.querySelector('img').src = '';
        pdfFilename.textContent = '';
    });

    // Handle category changes
    function toggleTravelFields() {
        const selectedCategory = document.querySelector('input[name="category"]:checked').value;
        travelFields.style.display = selectedCategory === 'travel' ? 'block' : 'none';
    }

    categoryInputs.forEach(input => {
        input.addEventListener('change', toggleTravelFields);
    });

    // Initial state
    toggleTravelFields();

    // Add zoom functionality
    const zoomContainer = document.querySelector('.receipt-zoom-container');
    const magnifierView = document.querySelector('.magnifier-view');
    let isZoomFrozen = false;
    
    function updateMagnifier(e) {
        if (isZoomFrozen) return; // Don't update if frozen
        
        const img = zoomContainer.querySelector('.receipt-image');
        const rect = img.getBoundingClientRect();
        
        // Get relative mouse position
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Calculate relative position (0 to 1)
        const relativeX = x / rect.width;
        const relativeY = y / rect.height;
        
        updateZoomView(relativeX, relativeY);
    }
    
    function updateZoomView(relativeX, relativeY) {
        const img = zoomContainer.querySelector('.receipt-image');
        const zoomFactor = 2;
        
        // Center the zoom by adjusting the background position
        const magnifierWidth = 300;
        const magnifierHeight = 300;
        
        const bgX = -((relativeX * img.width * zoomFactor) - (magnifierWidth / 2));
        const bgY = -((relativeY * img.height * zoomFactor) - (magnifierHeight / 2));
        
        magnifierView.style.backgroundImage = `url(${img.src})`;
        magnifierView.style.backgroundSize = `${img.width * zoomFactor}px ${img.height * zoomFactor}px`;
        magnifierView.style.backgroundPosition = `${bgX}px ${bgY}px`;
        
        // Show magnifier panel
        magnifierView.classList.add('active');
    }
    
    // Add event listeners for zoom
    if (zoomContainer) {
        const img = zoomContainer.querySelector('.receipt-image');
        
        img.addEventListener('mousemove', updateMagnifier);
        img.addEventListener('mouseleave', () => {
            if (!isZoomFrozen) {
                magnifierView.classList.remove('active');
            }
        });
        
        // Click to freeze/unfreeze
        img.addEventListener('click', (e) => {
            isZoomFrozen = !isZoomFrozen;
            if (isZoomFrozen) {
                // Update one last time at click position
                updateMagnifier(e);
                magnifierView.classList.add('frozen');
            } else {
                magnifierView.classList.remove('frozen');
            }
        });
        
        // Handle image load
        img.addEventListener('load', function() {
            // Initialize magnifier view
            magnifierView.style.backgroundImage = `url(${this.src})`;
            magnifierView.style.backgroundSize = `${this.width * 2}px ${this.height * 2}px`;
        });
    }
});