document.addEventListener('DOMContentLoaded', function() {
    // Copy notes to the reject form when submitting
    document.querySelector('form[action*="reject"]').addEventListener('submit', function() {
        const notes = document.getElementById('reviewer_notes').value;
        document.getElementById('reject_notes').value = notes;
    });
    
    // Character counter for reviewer notes with special handling for line breaks
    const textarea = document.getElementById('reviewer_notes');
    const charCount = document.getElementById('char-count');
    const MAX_CHARS = 100;
    const MAX_LINES = 2;
    
    function updateCharCount() {
        const text = textarea.value;
        const lineBreaks = (text.match(/\n/g) || []).length;
        
        // Count each line break as 5 characters to discourage excessive use
        const effectiveLength = text.length + (lineBreaks * 4); // Each \n already counts as 1, so add 4 more
        const remaining = MAX_CHARS - effectiveLength;
        
        // Check if too many line breaks
        if (lineBreaks > MAX_LINES) {
            // Remove excess line breaks
            let lines = text.split('\n');
            if (lines.length > MAX_LINES + 1) {
                lines = lines.slice(0, MAX_LINES + 1);
                textarea.value = lines.join('\n');
                alert(`Maximum ${MAX_LINES} line breaks allowed.`);
            }
        }
        
        // Update character count display
        charCount.textContent = remaining;
        if (remaining < 20) {
            charCount.style.color = 'red';
        } else {
            charCount.style.color = '';
        }
        
        // Prevent typing if max reached
        if (remaining < 0) {
            textarea.value = text.substring(0, MAX_CHARS - (lineBreaks * 4));
            updateCharCount(); // Recalculate after truncation
        }
    }
    
    // Handle paste events to prevent excessive content
    textarea.addEventListener('paste', function(e) {
        // Get pasted data
        let pastedText = (e.clipboardData || window.clipboardData).getData('text');
        
        // Count line breaks in pasted text
        const lineBreaks = (pastedText.match(/\n/g) || []).length;
        const currentBreaks = (textarea.value.match(/\n/g) || []).length;
        
        if (lineBreaks + currentBreaks > MAX_LINES) {
            if (confirm(`The pasted text contains too many line breaks. Would you like to paste without line breaks?`)) {
                e.preventDefault();
                // Replace line breaks with spaces and paste
                pastedText = pastedText.replace(/\n/g, ' ');
                
                // Insert at cursor position
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const text = textarea.value;
                textarea.value = text.substring(0, start) + pastedText + text.substring(end);
                
                // Move cursor to end of pasted text
                textarea.selectionStart = textarea.selectionEnd = start + pastedText.length;
                
                updateCharCount();
            } else {
                e.preventDefault(); // Prevent paste
            }
        }
    });
    
    textarea.addEventListener('input', updateCharCount);
    textarea.addEventListener('keydown', function(e) {
        // Check for Enter key
        if (e.key === 'Enter') {
            const lineBreaks = (textarea.value.match(/\n/g) || []).length;
            if (lineBreaks >= MAX_LINES) {
                e.preventDefault();
                alert(`Maximum ${MAX_LINES} line breaks allowed.`);
            }
        }
    });
    
    updateCharCount(); // Initialize on page load
}); 