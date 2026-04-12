// Members List Filters Toggle
console.log('=== Members Filters Script Loaded ===');

function toggleFilters() {
    const form = document.getElementById('filter-form');
    const icon = document.getElementById('filter-icon');
    const text = document.getElementById('filter-text');
    
    if (form.style.display === 'none' || form.style.display === '') {
        form.style.display = 'block';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        text.textContent = 'Ocultar Filtros';
    } else {
        form.style.display = 'none';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        text.textContent = 'Mostrar Filtros';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add click event listener to toggle button
    const toggleBtn = document.getElementById('toggle-filters-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleFilters);
    }
    
    // Auto-expand if filters are active
    const filterForm = document.getElementById('filter-form');
    if (filterForm && filterForm.dataset.hasFilters === 'true') {
        toggleFilters();
    }
});
