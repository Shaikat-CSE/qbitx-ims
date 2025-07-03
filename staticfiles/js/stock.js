// stock.js - Stock management functionality for Golden Niche IMS

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Initialize stock management page
        await initStockPage();
    } catch (error) {
        console.error('Error initializing stock page:', error);
        showNotification('Error loading stock data', 'danger');
    }
});

// Initialize stock management page
async function initStockPage() {
    // Load product dropdown
    await loadProductsDropdown();
    
    // Load recent stock history
    await loadStockHistory();
    
    // Set up event listeners
    setupEventListeners();
    
    // Check if product ID was passed in URL (for restocking from dashboard)
    const urlParams = new URLSearchParams(window.location.search);
    const productIdParam = urlParams.get('product');
    
    if (productIdParam) {
        document.getElementById('product').value = productIdParam;
        // Trigger change event to load product details
        document.getElementById('product').dispatchEvent(new Event('change'));
        // Set stock type to IN for restocking
        document.getElementById('stockIn').checked = true;
        // Focus on quantity field
        document.getElementById('quantity').focus();
    }
}

// Load products dropdown
async function loadProductsDropdown() {
    try {
        const products = await getProducts();
        const productSelect = document.getElementById('product');
        
        // Sort products by name
        products.sort((a, b) => a.name.localeCompare(b.name));
        
        // Generate options
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = product.name;
            productSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading products dropdown:', error);
        throw error;
    }
}

// Load recent stock history
async function loadStockHistory(limit = 10) {
    try {
        const stockHistory = await getStockHistory();
        const tableBody = document.getElementById('stockHistoryTable');
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        // Get most recent transactions (up to limit)
        const recentHistory = stockHistory.slice(0, limit);
        
        // Generate table rows
        recentHistory.forEach(transaction => {
            const row = document.createElement('tr');
            
            // Format date
            const date = new Date(transaction.date);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'});
            
            // Determine transaction class and label
            const transactionClass = transaction.type === 'IN' ? 'text-success' : 'text-danger';
            const transactionLabel = transaction.type === 'IN' ? 'Stock In' : 'Stock Out';
            
            // Determine supplier/client info
            const contactInfo = transaction.type === 'IN' 
                ? transaction.supplier || '-' 
                : transaction.client || '-';
            
            row.innerHTML = `
                <td>${formattedDate}</td>
                <td>${transaction.product_name}</td>
                <td><span class="${transactionClass}">${transactionLabel}</span></td>
                <td>${transaction.quantity}</td>
                <td>${transaction.reference_number || '-'}</td>
                <td>${contactInfo}</td>
                <td>${transaction.notes || '-'}</td>
            `;
            
            tableBody.appendChild(row);
        });
        
        // Show message if no history
        if (recentHistory.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center">No stock transactions found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading stock history:', error);
        throw error;
    }
}

// Set up event listeners
function setupEventListeners() {
    // Product selection change
    document.getElementById('product').addEventListener('change', async function() {
        const productId = this.value;
        
        if (productId) {
            await loadProductDetails(productId);
        } else {
            // Hide product details if no product selected
            document.getElementById('productDetails').classList.add('d-none');
            document.getElementById('noProductSelected').classList.remove('d-none');
        }
    });
    
    // Barcode scanner button
    document.getElementById('scanProductBarcodeBtn').addEventListener('click', handleBarcodeScan);
    
    // Transaction type change
    document.querySelectorAll('input[name="stockType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            // Show/hide supplier and client forms based on transaction type
            if (this.value === 'IN') {
                document.getElementById('supplierInfo').style.display = 'block';
                document.getElementById('clientInfo').style.display = 'none';
            } else {
                document.getElementById('supplierInfo').style.display = 'none';
                document.getElementById('clientInfo').style.display = 'block';
            }
        });
    });
    
    // Pre-fill unit price when product is selected
    document.getElementById('product').addEventListener('change', function() {
        const productId = this.value;
        if (productId) {
            getProductById(productId).then(product => {
                document.getElementById('unitPrice').value = product.price;
            });
        }
    });
    
    // Stock form submission
    document.getElementById('stockForm').addEventListener('submit', async function(event) {
        event.preventDefault();
        
        // Form validation
        if (!this.checkValidity()) {
            event.stopPropagation();
            this.classList.add('was-validated');
            return;
        }
        
        // Get form values
        const productId = document.getElementById('product').value;
        const quantity = parseInt(document.getElementById('quantity').value);
        const stockType = document.querySelector('input[name="stockType"]:checked').value;
        const notes = document.getElementById('notes').value;
        const referenceNumber = document.getElementById('referenceNumber').value;
        const unitPrice = document.getElementById('unitPrice').value ? 
                          parseFloat(document.getElementById('unitPrice').value) : null;
        
        // Get supplier or client data based on transaction type
        let supplier = null;
        let supplierContact = null;
        let client = null;
        let clientContact = null;
        
        if (stockType === 'IN') {
            supplier = document.getElementById('supplier').value;
            supplierContact = document.getElementById('supplierContact').value;
        } else {
            client = document.getElementById('client').value;
            clientContact = document.getElementById('clientContact').value;
        }
        
        try {
            // Create transaction data object
            const transactionData = {
                product: productId,
                quantity: quantity,
                type: stockType,
                notes: notes,
                reference_number: referenceNumber,
                unit_price: unitPrice,
                supplier: supplier,
                supplier_contact: supplierContact,
                client: client,
                client_contact: clientContact
            };
            
            // Update stock
            await updateStockWithDetails(transactionData);
            
            // Show success message
            showNotification('Stock transaction saved successfully');
            
            // Reload stock history
            await loadStockHistory();
            
            // Reload product details
            await loadProductDetails(productId);
            
            // Reset form
            document.getElementById('quantity').value = '';
            document.getElementById('notes').value = '';
            document.getElementById('unitPrice').value = '';
            document.getElementById('referenceNumber').value = '';
            document.getElementById('supplier').value = '';
            document.getElementById('supplierContact').value = '';
            document.getElementById('client').value = '';
            document.getElementById('clientContact').value = '';
            document.getElementById('stockIn').checked = true;
            
            // Trigger change event to show supplier info
            document.getElementById('stockIn').dispatchEvent(new Event('change'));
            
            // Focus on quantity field
            document.getElementById('quantity').focus();
        } catch (error) {
            console.error('Error saving stock transaction:', error);
            showNotification('Error saving stock transaction', 'danger');
        }
    });
}

// Handle barcode scanning for product selection
function handleBarcodeScan() {
    // Show a modal dialog for scanning
    const modalHTML = `
        <div class="modal fade" id="barcodeScanModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Scan Product Barcode</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center">
                        <p>Please scan the product barcode using your scanner device.</p>
                        <div class="mb-3">
                            <input type="text" class="form-control form-control-lg" id="barcodeInput" 
                                   placeholder="Barcode will appear here" autofocus>
                        </div>
                        <div class="d-flex justify-content-center">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Waiting for scan...</span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to the DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Initialize and show the modal
    const modal = new bootstrap.Modal(document.getElementById('barcodeScanModal'));
    modal.show();
    
    // Set focus on the input field
    setTimeout(() => {
        document.getElementById('barcodeInput').focus();
    }, 500);
    
    // Listen for input in the barcode field
    document.getElementById('barcodeInput').addEventListener('input', function(e) {
        if (this.value.length > 5) {
            const barcode = this.value;
            // Find product by barcode
            findProductByBarcode(barcode, modal);
        }
    });
}

// Find product by barcode and select it in the dropdown
async function findProductByBarcode(barcode, modal) {
    try {
        const products = await getProducts();
        
        // Find product with matching barcode
        const product = products.find(p => p.barcode === barcode);
        
        if (product) {
            // Select the product in the dropdown
            document.getElementById('product').value = product.id;
            
            // Trigger change event to load product details
            document.getElementById('product').dispatchEvent(new Event('change'));
            
            // Hide modal
            modal.hide();
            
            // Show success message
            showNotification(`Product found: ${product.name}`);
        } else {
            // Show error message
            showNotification('No product found with this barcode', 'danger');
            
            // Hide modal
            modal.hide();
        }
        
        // Remove the modal from the DOM after hiding
        document.getElementById('barcodeScanModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    } catch (error) {
        console.error('Error finding product by barcode:', error);
        showNotification('Error scanning barcode', 'danger');
        modal.hide();
    }
}

// Load product details
async function loadProductDetails(productId) {
    try {
        const product = await getProductById(productId);
        
        // Update product details
        document.getElementById('productName').textContent = product.name;
        document.getElementById('productSKU').textContent = product.sku;
        document.getElementById('productType').textContent = product.type;
        document.getElementById('productStock').textContent = product.quantity;
        document.getElementById('productPrice').textContent = formatCurrency(product.price);
        document.getElementById('productLocation').textContent = product.location || 'Not specified';
        document.getElementById('productBatch').textContent = product.batch_number || 'Not specified';
        
        // Set default unit price
        document.getElementById('unitPrice').value = product.price;
        
        // Format expiry date if it exists
        let expiryDisplay = 'Not specified';
        if (product.expiry_date) {
            const expiryDate = new Date(product.expiry_date);
            expiryDisplay = expiryDate.toLocaleDateString();
            
            // Highlight if expired
            if (expiryDate < new Date()) {
                expiryDisplay = `<span class="text-danger">${expiryDisplay} (EXPIRED)</span>`;
            }
        }
        document.getElementById('productExpiry').innerHTML = expiryDisplay;
        document.getElementById('productBarcode').textContent = product.barcode || 'Not specified';
        
        // Show product details, hide placeholder
        document.getElementById('productDetails').classList.remove('d-none');
        document.getElementById('noProductSelected').classList.add('d-none');
    } catch (error) {
        console.error('Error loading product details:', error);
        showNotification('Error loading product details', 'danger');
    }
}

// Update stock with detailed information
async function updateStockWithDetails(transactionData) {
    try {
        const response = await fetch(`${apiUrl}/stock/update/`, {
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