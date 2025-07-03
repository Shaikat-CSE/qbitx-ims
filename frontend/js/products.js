// products.js - Product management functionality for QBITX IMS Transform Suppliers

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Load product type filter options
        await loadProductTypes();
        
        // Load products initially
        await loadProducts();
        
        // Set up event listeners
        setupEventListeners();
    } catch (error) {
        console.error('Error initializing products page:', error);
        showNotification('Error loading products data', 'danger');
    }
});

// Load product types for filter dropdown
async function loadProductTypes() {
    try {
        const productTypes = await getProductTypes();
        const typeFilter = document.getElementById('productTypeFilter');
        
        productTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type.name;
            option.textContent = type.name;
            typeFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading product types:', error);
        throw error;
    }
}

// Load products into table with optional filters
async function loadProducts(filterType = '', searchQuery = '') {
    try {
        const products = await getProducts();
        const tableBody = document.getElementById('productsTable');
        const emptyMessage = document.getElementById('emptyMessage');
        const welcomeMessage = document.getElementById('welcomeMessage');
        const productsTable = document.querySelector('.card:not(#welcomeMessage)');
        const filterRow = document.querySelector('.row.mb-3');
        
        // Show welcome message if no products exist at all
        if (products.length === 0) {
            welcomeMessage.classList.remove('d-none');
            productsTable.classList.add('d-none');
            filterRow.classList.add('d-none');
            return;
        } else {
            welcomeMessage.classList.add('d-none');
            productsTable.classList.remove('d-none');
            filterRow.classList.remove('d-none');
        }
        
        // Filter products by type and search query
        let filteredProducts = products;
        
        if (filterType) {
            filteredProducts = filteredProducts.filter(product => product.type === filterType);
        }
        
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filteredProducts = filteredProducts.filter(product => 
                product.name.toLowerCase().includes(query) || 
                product.sku.toLowerCase().includes(query)
            );
        }
        
        // Show or hide empty message
        if (filteredProducts.length === 0) {
            tableBody.innerHTML = '';
            emptyMessage.classList.remove('d-none');
            return;
        } else {
            emptyMessage.classList.add('d-none');
        }
        
        // Generate table rows
        tableBody.innerHTML = '';
        
        filteredProducts.forEach(product => {
            const row = document.createElement('tr');
            
            // Add low-stock class if quantity is low
            if (product.quantity <= product.minimum_stock_level) {
                row.classList.add('low-stock');
            }
            
            // Format expiry date if it exists
            let expiryDisplay = '-';
            if (product.expiry_date) {
                const expiryDate = new Date(product.expiry_date);
                expiryDisplay = expiryDate.toLocaleDateString();
                
                // Add expired class if product is expired
                if (expiryDate < new Date()) {
                    expiryDisplay = `<span class="text-danger">${expiryDisplay}</span>`;
                }
            }
            
            // Calculate profit margin
            const buyingPrice = parseFloat(product.buying_price) || 0;
            const sellingPrice = parseFloat(product.selling_price) || 0;
            let profitMargin = 0;
            let profitMarginClass = '';
            
            if (buyingPrice > 0 && sellingPrice > 0) {
                profitMargin = ((sellingPrice - buyingPrice) / buyingPrice) * 100;
                
                // Add color coding based on margin
                if (profitMargin < 10) {
                    profitMarginClass = 'text-danger';
                } else if (profitMargin < 20) {
                    profitMarginClass = 'text-warning';
                } else {
                    profitMarginClass = 'text-success';
                }
            }
            
            // Create action buttons based on permissions
            const canEditProduct = hasPermission('inventory.change_product');
            const canDeleteProduct = hasPermission('inventory.delete_product');
            
            const editButton = canEditProduct 
                ? `<a href="product-form.html?id=${product.id}" class="btn btn-sm btn-warning edit-product-btn" data-action="edit-product">
                      <i class="fas fa-edit"></i>
                   </a>`
                : `<button class="btn btn-sm btn-warning disabled" disabled title="You do not have permission to edit products">
                      <i class="fas fa-edit"></i>
                   </button>`;
                   
            const deleteButton = canDeleteProduct
                ? `<button class="btn btn-sm btn-danger delete-product" data-id="${product.id}" data-name="${product.name}" data-action="delete-product">
                      <i class="fas fa-trash"></i>
                   </button>`
                : `<button class="btn btn-sm btn-danger disabled" disabled title="You do not have permission to delete products">
                      <i class="fas fa-trash"></i>
                   </button>`;
            
            row.innerHTML = `
                <td>${product.name}</td>
                <td>${product.sku}</td>
                <td>${product.type}</td>
                <td>${product.quantity}</td>
                <td>${product.unit_of_measure || 'Unit'}</td>
                <td>${formatCurrency(product.buying_price)}</td>
                <td>${formatCurrency(product.selling_price)}</td>
                <td><span class="${profitMarginClass}">${profitMargin.toFixed(2)}%</span></td>
                <td>${product.shipment_number || '-'}</td>
                <td>${product.location || '-'}</td>
                <td>${expiryDisplay}</td>
                <td>
                    ${editButton}
                    ${deleteButton}
                </td>
            `;
            
            tableBody.appendChild(row);
        });
        
        // Add event listeners to delete buttons
        attachDeleteHandlers();
    } catch (error) {
        console.error('Error loading products:', error);
        throw error;
    }
}

// Set up event listeners for product list page
function setupEventListeners() {
    // Filter by type
    document.getElementById('productTypeFilter').addEventListener('change', function() {
        const filterType = this.value;
        const searchQuery = document.getElementById('searchInput').value.trim();
        loadProducts(filterType, searchQuery);
    });
    
    // Search products
    document.getElementById('searchInput').addEventListener('input', function() {
        const searchQuery = this.value.trim();
        const filterType = document.getElementById('productTypeFilter').value;
        loadProducts(filterType, searchQuery);
    });
    
    // Confirm delete
    document.getElementById('confirmDelete').addEventListener('click', async function() {
        const productId = this.getAttribute('data-id');
        console.log(`Confirm delete clicked for product ID: ${productId}`);
        await deleteProductAndReload(productId);
        
        // Hide modal
        const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        deleteModal.hide();
    });
}

// Attach delete button handlers
function attachDeleteHandlers() {
    // Only attach handlers if user has delete permission
    if (!hasPermission('inventory.delete_product')) return;
    
    document.querySelectorAll('.delete-product:not(.disabled)').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-id');
            const productName = this.getAttribute('data-name');
            
            // Set product name in modal
            document.getElementById('deleteProductName').textContent = productName;
            
            // Set product ID on confirm button
            document.getElementById('confirmDelete').setAttribute('data-id', productId);
            
            // Show modal
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
            deleteModal.show();
        });
    });
}

// Delete a product and reload the table
async function deleteProductAndReload(productId) {
    try {
        // Double-check permissions for security
        if (!hasPermission('inventory.delete_product')) {
            showNotification('You do not have permission to delete products', 'danger');
            return;
        }
        
        console.log(`Attempting to delete product with ID: ${productId}`);
        
        // Handle both numeric and string IDs (for both API and mock data)
        await deleteProduct(productId);
        
        // Reload products table
        const filterType = document.getElementById('productTypeFilter').value;
        const searchQuery = document.getElementById('searchInput').value.trim();
        await loadProducts(filterType, searchQuery);
        
        // Show success message
        showNotification('Product deleted successfully');
    } catch (error) {
        console.error('Error deleting product:', error);
        showNotification('Error deleting product: ' + error.message, 'danger');
    }
} 