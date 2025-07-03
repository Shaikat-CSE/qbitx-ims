// app.js - Common functionality for Golden Niche IMS with Django backend

document.addEventListener('DOMContentLoaded', function() {
    // Set up the sidebar active link based on current page
    setActiveSidebarLink();
    
    // Display the current date on the dashboard
    const currentDateElement = document.getElementById('currentDate');
    if (currentDateElement) {
        currentDateElement.textContent = new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
});

// Function to set the active sidebar link
function setActiveSidebarLink() {
    const currentPage = window.location.pathname.split('/').pop();
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    
    sidebarLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Function to format currency in BDT (Bangladeshi Taka)
function formatCurrency(amount) {
    return '৳' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Function to display a notification/toast message
function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast show bg-${type} text-white position-fixed top-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">Golden Niche IMS</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Remove the toast after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// API helper functions
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json'
            },
            ...options
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'API request failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API error:', error);
        showNotification(error.message, 'danger');
        throw error;
    }
}

// Helper function to get all products
async function getProducts() {
    return await fetchAPI(API_CONFIG.ENDPOINTS.PRODUCTS);
}

// Helper function to get product types
async function getProductTypes() {
    return await fetchAPI(API_CONFIG.ENDPOINTS.PRODUCT_TYPES);
}

// Helper function to get a product by ID
async function getProductById(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.PRODUCTS}${id}/`);
}

// Helper function to create a new product
async function createProduct(productData) {
    return await fetchAPI(API_CONFIG.ENDPOINTS.PRODUCTS, {
        method: 'POST',
        body: JSON.stringify(productData)
    });
}

// Helper function to update a product
async function updateProduct(id, productData) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.PRODUCTS}${id}/`, {
        method: 'PUT',
        body: JSON.stringify(productData)
    });
}

// Helper function to delete a product
async function deleteProduct(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.PRODUCTS}${id}/`, {
        method: 'DELETE'
    });
}

// Helper function to get stock history
async function getStockHistory() {
    return await fetchAPI(API_CONFIG.ENDPOINTS.STOCK_HISTORY);
}

// Helper function to update stock levels
async function updateStock(productId, quantity, type, notes = '') {
    return await fetchAPI(API_CONFIG.ENDPOINTS.STOCK_HISTORY, {
        method: 'POST',
        body: JSON.stringify({
            product: productId,
            quantity: parseInt(quantity),
            type: type,
            notes: notes
        })
    });
}

// Helper function to get low stock products
async function getLowStockProducts(threshold = 5) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.LOW_STOCK}?threshold=${threshold}`);
}

// Helper function to get inventory stats
async function getInventoryStats() {
    return await fetchAPI(API_CONFIG.ENDPOINTS.STATS);
}

// Update stock with detailed information
async function updateStockWithDetails(transactionData) {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/stock/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${getAuthToken()}`
            },
            body: JSON.stringify(transactionData)
        });
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
} 