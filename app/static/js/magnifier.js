document.addEventListener('DOMContentLoaded', function() {
    const zoomContainer = document.querySelector('.receipt-zoom-container');
    const magnifierView = document.querySelector('.magnifier-view');
    let isZoomFrozen = false;
    
    function updateMagnifier(e) {
        if (isZoomFrozen) return;
        
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
                updateMagnifier(e);
                magnifierView.classList.add('frozen');
            } else {
                magnifierView.classList.remove('frozen');
            }
        });
        
        // Handle image load
        img.addEventListener('load', function() {
            magnifierView.style.backgroundImage = `url(${this.src})`;
            magnifierView.style.backgroundSize = `${this.width * 2}px ${this.height * 2}px`;
        });
    }
}); 