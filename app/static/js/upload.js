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