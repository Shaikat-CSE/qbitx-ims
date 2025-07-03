// mock-data.js - Mock data for QBITX IMS Transform Suppliers when API is not available

// Mock products data
window.MOCK_PRODUCTS = [
    {
        id: 'p1',
        name: 'Smartphone X',
        sku: 'SP-001',
        description: 'Latest smartphone model with advanced features',
        buying_price: 38000,
        selling_price: 45000,
        price: 41500, // Average for backward compatibility
        quantity: 25,
        type: 'Electronics',
        min_stock: 5,
        uom: 'Unit'
    },
    {
        id: 'p2',
        name: 'Laptop Pro',
        sku: 'LP-002',
        description: 'High-performance laptop for professionals',
        buying_price: 70000,
        selling_price: 85000,
        price: 77500, // Average for backward compatibility
        quantity: 12,
        type: 'Electronics',
        min_stock: 3,
        uom: 'Unit'
    },
    {
        id: 'p3',
        name: 'Office Desk',
        sku: 'FN-003',
        description: 'Ergonomic office desk',
        buying_price: 8500,
        selling_price: 12000,
        price: 10250, // Average for backward compatibility
        quantity: 8,
        type: 'Furniture',
        min_stock: 2,
        uom: 'Piece'
    },
    {
        id: 'p4',
        name: 'Premium Coffee',
        sku: 'GR-004',
        description: 'Premium coffee beans',
        buying_price: 550,
        selling_price: 850,
        price: 700, // Average for backward compatibility
        quantity: 50,
        type: 'Grocery',
        min_stock: 10,
        uom: 'kg'
    },
    {
        id: 'p5',
        name: 'Wireless Headphones',
        sku: 'SP-005',
        description: 'Noise-cancelling wireless headphones',
        buying_price: 2200,
        selling_price: 3500,
        price: 2850, // Average for backward compatibility
        quantity: 30,
        type: 'Electronics',
        min_stock: 5,
        uom: 'Unit'
    }
];

// Mock suppliers data
window.MOCK_SUPPLIERS = [
    {
        id: 's1',
        name: 'Tech Distributors Ltd.',
        contact_person: 'Ahmed Khan',
        phone: '01712345678',
        email: 'info@techdist.com',
        address: '123 Tech Street, Dhaka'
    },
    {
        id: 's2',
        name: 'Global Imports Inc.',
        contact_person: 'Sarah Rahman',
        phone: '01812345678',
        email: 'contact@globalimports.com',
        address: '456 Import Avenue, Chattogram'
    },
    {
        id: 's3',
        name: 'Furniture World',
        contact_person: 'Kamal Hossain',
        phone: '01912345678',
        email: 'sales@furnitureworld.com',
        address: '789 Furniture Road, Sylhet'
    }
];

// Mock clients data
window.MOCK_CLIENTS = [
    {
        id: 'c1',
        name: 'ABC Corporation',
        contact_person: 'Rahim Ahmed',
        phone: '01612345678',
        email: 'info@abccorp.com',
        address: '101 Business Park, Dhaka'
    },
    {
        id: 'c2',
        name: 'XYZ Enterprises',
        contact_person: 'Fatima Begum',
        phone: '01512345678',
        email: 'contact@xyzent.com',
        address: '202 Enterprise Zone, Khulna'
    },
    {
        id: 'c3',
        name: 'Local Retail Shop',
        contact_person: 'Jamal Uddin',
        phone: '01312345678',
        email: 'shop@localretail.com',
        address: '303 Retail Street, Rajshahi'
    }
];

// Mock stock history data
window.MOCK_STOCK_HISTORY = [
    {
        id: 't1',
        product: 'p1',
        product_name: 'Smartphone X',
        quantity: 10,
        type: 'IN',
        date: '2025-06-01T10:30:00',
        notes: 'Initial stock',
        supplier: 's1',
        supplier_name: 'Tech Distributors Ltd.',
        reference_number: 'PO-2025-001',
        discount: 2000,
        wastage: 1500,
        uom: 'Unit'
    },
    {
        id: 't2',
        product: 'p2',
        product_name: 'Laptop Pro',
        quantity: 5,
        type: 'IN',
        date: '2025-06-01T11:45:00',
        notes: 'Initial stock',
        supplier: 's1',
        supplier_name: 'Tech Distributors Ltd.',
        reference_number: 'PO-2025-002',
        discount: 5000,
        wastage: 3000,
        uom: 'Unit'
    },
    {
        id: 't3',
        product: 'p3',
        product_name: 'Office Desk',
        quantity: 3,
        type: 'IN',
        date: '2025-06-02T09:15:00',
        notes: 'Initial stock',
        supplier: 's3',
        supplier_name: 'Furniture World',
        reference_number: 'PO-2025-003',
        discount: 0,
        wastage: 0,
        uom: 'Piece'
    },
    {
        id: 't4',
        product: 'p1',
        product_name: 'Smartphone X',
        quantity: 2,
        type: 'OUT',
        date: '2025-06-03T14:20:00',
        notes: 'Regular sale',
        client: 'c1',
        client_name: 'ABC Corporation',
        reference_number: 'SO-2025-001',
        discount: 1000,
        wastage: 500,
        uom: 'Unit'
    },
    {
        id: 't5',
        product: 'p2',
        product_name: 'Laptop Pro',
        quantity: 1,
        type: 'OUT',
        date: '2025-06-03T16:30:00',
        notes: 'Regular sale',
        client: 'c2',
        client_name: 'XYZ Enterprises',
        reference_number: 'SO-2025-002',
        discount: 2000,
        wastage: 1200,
        uom: 'Unit'
    },
    {
        id: 't6',
        product: 'p4',
        product_name: 'Premium Coffee',
        quantity: 20,
        type: 'IN',
        date: '2025-06-04T10:00:00',
        notes: 'Regular stock',
        supplier: 's2',
        supplier_name: 'Global Imports Inc.',
        reference_number: 'PO-2025-004',
        discount: 500,
        wastage: 250,
        uom: 'kg'
    },
    {
        id: 't7',
        product: 'p4',
        product_name: 'Premium Coffee',
        quantity: 5,
        type: 'OUT',
        date: '2025-06-05T11:15:00',
        notes: 'Regular sale',
        client: 'c3',
        client_name: 'Local Retail Shop',
        reference_number: 'SO-2025-003',
        discount: 200,
        wastage: 75,
        uom: 'kg'
    },
    {
        id: 't8',
        product: 'p5',
        product_name: 'Wireless Headphones',
        quantity: 15,
        type: 'IN',
        date: '2025-06-05T13:45:00',
        notes: 'Initial stock',
        supplier: 's1',
        supplier_name: 'Tech Distributors Ltd.',
        reference_number: 'PO-2025-005',
        discount: 1500,
        wastage: 800,
        uom: 'Unit'
    },
    {
        id: 't9',
        product: 'p5',
        product_name: 'Wireless Headphones',
        quantity: 3,
        type: 'OUT',
        date: '2025-06-06T09:30:00',
        notes: 'Regular sale',
        client: 'c1',
        client_name: 'ABC Corporation',
        reference_number: 'SO-2025-004',
        discount: 300,
        wastage: 150,
        uom: 'Unit'
    },
    {
        id: 't10',
        product: 'p3',
        product_name: 'Office Desk',
        quantity: 1,
        type: 'OUT',
        date: '2025-06-06T14:00:00',
        notes: 'Regular sale',
        client: 'c2',
        client_name: 'XYZ Enterprises',
        reference_number: 'SO-2025-005',
        discount: 500,
        wastage: 0,
        uom: 'Piece'
    }
];

// Mock inventory stats
window.MOCK_INVENTORY_STATS = {
    total_products: window.MOCK_PRODUCTS.length,
    total_value: window.MOCK_PRODUCTS.reduce((sum, product) => sum + ((product.buying_price || product.price) * product.quantity), 0),
    low_stock_count: window.MOCK_PRODUCTS.filter(product => product.quantity <= product.min_stock).length
};

// Override setupMockData function
function setupMockData() {
    console.log('Using mock data instead of API');
    
    // Store original functions if they exist
    const originalGetProducts = window.getProducts;
    
    // Override getProducts
    window.getProducts = async function() {
        // Try to use the original function first if it exists
        if (originalGetProducts) {
            try {
                const apiProducts = await originalGetProducts();
                console.log(`API returned ${apiProducts.length} products`);
                
                // If API returned products, use them
                if (apiProducts && apiProducts.length > 0) {
                    return apiProducts;
                }
                
                // Otherwise fall back to mock data
                console.log('API returned no products, using mock data');
            } catch (error) {
                console.error('Error fetching products from API:', error);
            }
        }
        
        // Return mock products
        console.log(`Returning ${window.MOCK_PRODUCTS.length} mock products`);
        return [...window.MOCK_PRODUCTS];
    };
    
    // Override getProductById
    const originalGetProductById = window.getProductById;
    window.getProductById = async function(id) {
        // Try to use the original function first if it exists
        if (originalGetProductById) {
            try {
                const product = await originalGetProductById(id);
                if (product) {
                    return product;
                }
            } catch (error) {
                console.error('Error fetching product by ID from API:', error);
            }
        }
        
        // Fall back to mock data
        const product = window.MOCK_PRODUCTS.find(p => p.id === id);
        if (!product) {
            throw new Error('Product not found');
        }
        return {...product};
    };
    
    // Override getStockHistory
    const originalGetStockHistory = window.getStockHistory;
    window.getStockHistory = async function() {
        // Try to use the original function first if it exists
        if (originalGetStockHistory) {
            try {
                const history = await originalGetStockHistory();
                if (history && history.length > 0) {
                    return history;
                }
            } catch (error) {
                console.error('Error fetching stock history from API:', error);
            }
        }
        
        // Fall back to mock data
        return [...window.MOCK_STOCK_HISTORY];
    };
    
    // Override getInventoryStats
    const originalGetInventoryStats = window.getInventoryStats;
    window.getInventoryStats = async function() {
        // Try to use the original function first if it exists
        if (originalGetInventoryStats) {
            try {
                const stats = await originalGetInventoryStats();
                if (stats) {
                    return stats;
                }
            } catch (error) {
                console.error('Error fetching inventory stats from API:', error);
            }
        }
        
        // Fall back to mock data
        return {...window.MOCK_INVENTORY_STATS};
    };
    
    // Override getSuppliers
    const originalGetSuppliers = window.getSuppliers;
    window.getSuppliers = async function() {
        // Try to use the original function first if it exists
        if (originalGetSuppliers) {
            try {
                const suppliers = await originalGetSuppliers();
                if (suppliers && suppliers.length > 0) {
                    return suppliers;
                }
            } catch (error) {
                console.error('Error fetching suppliers from API:', error);
            }
        }
        
        // Fall back to mock data
        return [...window.MOCK_SUPPLIERS];
    };
    
    // Override getClients
    const originalGetClients = window.getClients;
    window.getClients = async function() {
        // Try to use the original function first if it exists
        if (originalGetClients) {
            try {
                const clients = await originalGetClients();
                if (clients && clients.length > 0) {
                    return clients;
                }
            } catch (error) {
                console.error('Error fetching clients from API:', error);
            }
        }
        
        // Fall back to mock data
        return [...window.MOCK_CLIENTS];
    };
    
    // Override deleteProduct
    const originalDeleteProduct = window.deleteProduct;
    window.deleteProduct = async function(id) {
        // Try to use the original function first if it exists
        if (originalDeleteProduct) {
            try {
                await originalDeleteProduct(id);
                return { success: true };
            } catch (error) {
                console.error('Error deleting product from API:', error);
            }
        }
        
        // Fall back to mock data deletion
        console.log(`Mock deleting product with ID: ${id}`);
        const index = window.MOCK_PRODUCTS.findIndex(p => p.id === id || p.id === String(id));
        if (index === -1) {
            throw new Error('Product not found');
        }
        
        // Remove the product from mock data
        window.MOCK_PRODUCTS.splice(index, 1);
        return { success: true };
    };
}

// Check if API is available, otherwise use mock data
document.addEventListener('DOMContentLoaded', function() {
    // Always set up mock data initially
    setupMockData();
    
    // Check if API_CONFIG exists and is accessible
    if (typeof API_CONFIG === 'undefined' || !API_CONFIG.BASE_URL) {
        console.log('API_CONFIG not found, using mock data only');
        return;
    }
    
    console.log('Checking API availability...');
    
    // Build the full URL for the API check
    const apiUrl = window.location.origin + API_CONFIG.BASE_URL + '/products/stats/';
    console.log('Testing API at:', apiUrl);
    
    // Test API connection
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                console.error(`API responded with status ${response.status}: ${response.statusText}`);
                throw new Error('API not available');
            }
            return response.json();
        })
        .then(data => {
            console.log('API stats endpoint is available:', data);
            
            // Check if products API returns data
            console.log('Checking products endpoint...');
            return fetch(window.location.origin + API_CONFIG.BASE_URL + '/products/');
        })
        .then(response => {
            if (!response.ok) {
                console.error(`Products API responded with status ${response.status}: ${response.statusText}`);
                throw new Error('Products API not available');
            }
            return response.json();
        })
        .then(products => {
            console.log(`Received ${products.length} products from API`);
            if (products.length === 0) {
                console.warn('API returned empty products array, using mock data');
            } else {
                console.log('Using real API data');
                
                // Check stock history endpoint
                console.log('Checking stock history endpoint...');
                return fetch(window.location.origin + API_CONFIG.BASE_URL + '/stock-history/')
                    .then(response => {
                        if (!response.ok) {
                            console.error(`Stock history API responded with status ${response.status}: ${response.statusText}`);
                            throw new Error('Stock history API not available');
                        }
                        return response.json();
                    })
                    .then(history => {
                        console.log(`Received ${history.length} stock history entries from API`);
                        if (history.length === 0) {
                            console.warn('API returned empty stock history, may use mock data for transactions');
                        }
                    })
                    .catch(error => {
                        console.warn('Error checking stock history API:', error);
                    });
            }
        })
        .catch(error => {
            console.warn('API not available or returned no data, using mock data:', error);
        });
}); 