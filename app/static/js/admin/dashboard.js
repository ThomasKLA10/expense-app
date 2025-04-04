// Save accordion state
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.accordion-collapse').forEach(collapse => {
        collapse.addEventListener('shown.bs.collapse', event => {
            localStorage.setItem(event.target.id + '_expanded', 'true');
        });
        collapse.addEventListener('hidden.bs.collapse', event => {
            localStorage.setItem(event.target.id + '_expanded', 'false');
        });
        
        // Restore accordion state
        const expanded = localStorage.getItem(collapse.id + '_expanded') === 'true';
        if (expanded) {
            new bootstrap.Collapse(collapse, { toggle: true });
        }
    });
}); 