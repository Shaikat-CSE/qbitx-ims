// app.js - Common functionality for QBITX IMS Transform Suppliers with Django backend

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
            <strong class="me-auto">QBITX IMS Transform Suppliers</strong>
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
        // Build the full URL
        const baseUrl = API_CONFIG.BASE_URL.startsWith('http') 
            ? API_CONFIG.BASE_URL 
            : window.location.origin + API_CONFIG.BASE_URL;
        
        const url = `${baseUrl}${endpoint}`;
        console.log(`API Request: ${url}`, options);
        
        // Get auth token from localStorage - check both possible token names
        const authToken = localStorage.getItem('auth_token') || localStorage.getItem('authToken');
        
        // Create headers with authentication if token exists
        let headers = {
            'Content-Type': 'application/json'
        };
        
        if (authToken) {
            headers['Authorization'] = `Token ${authToken}`;
        }
        
        // Merge provided options with headers
        const finalOptions = {
            ...options,
            headers: {
                ...headers,
                ...(options.headers || {})
            }
        };
        
        const response = await fetch(url, finalOptions);
        
        // Handle unauthorized responses
        if (response.status === 401) {
            console.error('Authentication failed. Redirecting to login page.');
            localStorage.removeItem('authToken');
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('currentUser');
            window.location.href = 'login.html';
            return null;
        }
        
        if (!response.ok) {
            console.error(`API Error: ${response.status} ${response.statusText} for ${endpoint}`);
            
            // Try to get error details from response
            let errorMessage = `${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData.error) {
                    errorMessage = errorData.error;
                } else if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
                console.error('API error details:', errorData);
            } catch (e) {
                console.error('Could not parse error response:', e);
            }
            
            // If API fails, check if we have mock data available
            if (window.MOCK_PRODUCTS && endpoint.includes('/products')) {
                console.log('Falling back to mock data for products');
                if (options.method === 'DELETE') {
                    return { success: true };
                }
                return [...window.MOCK_PRODUCTS];
            }
            
            if (window.MOCK_STOCK_HISTORY && endpoint.includes('/stock-history')) {
                console.log('Falling back to mock data for stock history');
                return [...window.MOCK_STOCK_HISTORY];
            }
            
            if (window.MOCK_SUPPLIERS && endpoint.includes('/suppliers')) {
                console.log('Falling back to mock data for suppliers');
                return [...window.MOCK_SUPPLIERS];
            }
            
            if (window.MOCK_CLIENTS && endpoint.includes('/clients')) {
                console.log('Falling back to mock data for clients');
                return [...window.MOCK_CLIENTS];
            }
            
            if (window.MOCK_INVENTORY_STATS && endpoint.includes('/stats')) {
                console.log('Falling back to mock data for inventory stats');
                return {...window.MOCK_INVENTORY_STATS};
            }
            
            throw new Error(errorMessage || 'API request failed');
        }
        
        // For DELETE requests, we might not have a response body
        if (options.method === 'DELETE') {
            return { success: true };
        }
        
        const data = await response.json();
        console.log(`API Response for ${endpoint}: ${Array.isArray(data) ? data.length + ' items' : 'object'}`);
        return data;
    } catch (error) {
        console.error('API error:', error);
        
        // Try to use mock data as fallback if available
        if (window.MOCK_PRODUCTS && endpoint.includes('/products')) {
            console.log('Error occurred, using mock data for products');
            if (options.method === 'DELETE') {
                return { success: true };
            }
            return [...window.MOCK_PRODUCTS];
        }
        
        if (window.MOCK_STOCK_HISTORY && endpoint.includes('/stock-history')) {
            console.log('Error occurred, using mock data for stock history');
            return [...window.MOCK_STOCK_HISTORY];
        }
        
        if (window.MOCK_SUPPLIERS && endpoint.includes('/suppliers')) {
            console.log('Error occurred, using mock data for suppliers');
            return [...window.MOCK_SUPPLIERS];
        }
        
        if (window.MOCK_CLIENTS && endpoint.includes('/clients')) {
            console.log('Error occurred, using mock data for clients');
            return [...window.MOCK_CLIENTS];
        }
        
        if (window.MOCK_INVENTORY_STATS && endpoint.includes('/stats')) {
            console.log('Error occurred, using mock data for inventory stats');
            return {...window.MOCK_INVENTORY_STATS};
        }
        
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
async function updateProduct(productData) {
    const id = productData.id;
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
    console.log('Getting stock history with token:', localStorage.getItem('auth_token') || localStorage.getItem('authToken'));
    try {
        const data = await fetchAPI(API_CONFIG.ENDPOINTS.STOCK_HISTORY);
        console.log('Stock history data fetched successfully:', data ? `${data.length} items` : 'No data');
        return data;
    } catch (error) {
        console.error('Error fetching stock history:', error);
        // Fall back to mock data if available
        if (window.MOCK_STOCK_HISTORY) {
            console.log('Using mock stock history data instead');
            return [...window.MOCK_STOCK_HISTORY];
        }
        throw error;
    }
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

// Helper function to get inventory stats
async function getInventoryStats() {
    return await fetchAPI(API_CONFIG.ENDPOINTS.STATS);
}

// Helper function to get wastage stats
async function getWastageStats() {
    return await fetchAPI(API_CONFIG.ENDPOINTS.WASTAGE_STATS);
}

// Helper function to get low stock products
async function getLowStockProducts(threshold = 5) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.LOW_STOCK}?threshold=${threshold}`);
}

// Update stock with detailed information
async function updateStockWithDetails(transactionData) {
    return await fetchAPI('/stock/update/', {
        method: 'POST',
        body: JSON.stringify(transactionData)
    });
}

// Helper functions for suppliers
async function getSuppliers() {
    return await fetchAPI(API_CONFIG.ENDPOINTS.SUPPLIERS);
}

async function getSupplierById(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.SUPPLIERS}${id}/`);
}

async function createSupplier(supplierData) {
    return await fetchAPI(API_CONFIG.ENDPOINTS.SUPPLIERS, {
        method: 'POST',
        body: JSON.stringify(supplierData)
    });
}

async function updateSupplier(id, supplierData) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.SUPPLIERS}${id}/`, {
        method: 'PUT',
        body: JSON.stringify(supplierData)
    });
}

async function deleteSupplier(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.SUPPLIERS}${id}/`, {
        method: 'DELETE'
    });
}

async function getSupplierTransactions(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.SUPPLIERS}${id}/transactions/`);
}

async function getSupplierProducts(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.SUPPLIERS}${id}/products/`);
}

// Helper functions for clients
async function getClients() {
    return await fetchAPI(API_CONFIG.ENDPOINTS.CLIENTS);
}

async function getClientById(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.CLIENTS}${id}/`);
}

async function createClient(clientData) {
    return await fetchAPI(API_CONFIG.ENDPOINTS.CLIENTS, {
        method: 'POST',
        body: JSON.stringify(clientData)
    });
}

async function updateClient(id, clientData) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.CLIENTS}${id}/`, {
        method: 'PUT',
        body: JSON.stringify(clientData)
    });
}

async function deleteClient(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.CLIENTS}${id}/`, {
        method: 'DELETE'
    });
}

async function getClientTransactions(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.CLIENTS}${id}/transactions/`);
}

async function getClientProducts(id) {
    return await fetchAPI(`${API_CONFIG.ENDPOINTS.CLIENTS}${id}/products/`);
} 