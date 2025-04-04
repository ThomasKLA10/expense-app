document.addEventListener('DOMContentLoaded', function() {
    // Accordion functionality
    document.querySelectorAll('.accordion-collapse').forEach(collapse => {
        collapse.addEventListener('shown.bs.collapse', event => {
            localStorage.setItem(event.target.id + '_expanded', 'true');
        });
        collapse.addEventListener('hidden.bs.collapse', event => {
            localStorage.setItem(event.target.id + '_expanded', 'false');
        });
        
        const expanded = localStorage.getItem(collapse.id + '_expanded') === 'true';
        if (expanded) {
            new bootstrap.Collapse(collapse, { toggle: true });
        }
    });

    // Auto-hide toasts after 6 seconds with fade out animation
    let toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.classList.add('animate__fadeOutRight');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 1000);
        }, 6000);
    });

    // Receipt viewing functionality
    // Get viewed receipts from localStorage
    let viewedReceipts = JSON.parse(localStorage.getItem('viewedReceipts') || '[]');
    
    // Mark already viewed receipts
    document.querySelectorAll('tr[data-receipt-id]').forEach(row => {
        const receiptId = row.dataset.receiptId;
        if (viewedReceipts.includes(receiptId)) {
            row.dataset.viewed = "true";
        }
    });

    // Handle new interactions
    const recentUpdates = document.querySelectorAll('.recent-update');
    recentUpdates.forEach(row => {
        row.addEventListener('mouseover', function() {
            const receiptId = this.dataset.receiptId;
            if (!viewedReceipts.includes(receiptId)) {
                viewedReceipts.push(receiptId);
                localStorage.setItem('viewedReceipts', JSON.stringify(viewedReceipts));
                
                setTimeout(() => {
                    row.dataset.viewed = "true";
                }, 300);
            }
        });
    });
}); 