// stock.js - Stock management functionality for QBITX IMS Transform Suppliers

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
    
    // Load supplier dropdown
    await loadSuppliersDropdown();
    
    // Load client dropdown
    await loadClientsDropdown();
    
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

// Load suppliers dropdown
async function loadSuppliersDropdown() {
    try {
        const suppliers = await getSuppliers();
        const supplierSelect = document.getElementById('supplierSelect');
        
        if (!supplierSelect) return; // If element doesn't exist
        
        // Sort suppliers by name
        suppliers.sort((a, b) => a.name.localeCompare(b.name));
        
        // Generate options
        suppliers.forEach(supplier => {
            const option = document.createElement('option');
            option.value = supplier.id;
            option.textContent = supplier.name;
            supplierSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading suppliers dropdown:', error);
    }
}

// Load clients dropdown
async function loadClientsDropdown() {
    try {
        const clients = await getClients();
        const clientSelect = document.getElementById('clientSelect');
        
        if (!clientSelect) return; // If element doesn't exist
        
        // Sort clients by name
        clients.sort((a, b) => a.name.localeCompare(b.name));
        
        // Generate options
        clients.forEach(client => {
            const option = document.createElement('option');
            option.value = client.id;
            option.textContent = client.name;
            clientSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading clients dropdown:', error);
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
                ? transaction.supplier_name || transaction.supplier || '-' 
                : transaction.client_name || transaction.client || '-';
            
            // Get product information for UOM and pricing
            getProductById(transaction.product).then(product => {
                // Calculate financial values
                const unitPrice = transaction.unit_price || product.price || 0;
                const discount = transaction.discount || 0;
                // Use wastage from backend, fallback to 0
                const wastage = transaction.wastage || 0;
                const totalPrice = transaction.quantity * unitPrice;
                const payableAmount = totalPrice - discount;
                const uom = product.unit_of_measure || 'Unit';
                
                // Log values for debugging
                console.log(`Transaction ${transaction.id} values:`, {
                    unitPrice,
                    discount,
                    wastage,
                    totalPrice,
                    payableAmount,
                    uom,
                    product_unit_of_measure: product.unit_of_measure
                });
                
                row.innerHTML = `
                    <td>${formattedDate}</td>
                    <td>${transaction.product_name}</td>
                    <td><span class="${transactionClass}">${transactionLabel}</span></td>
                    <td>${transaction.quantity}</td>
                    <td>${uom}</td>
                    <td>${formatCurrency(unitPrice)}</td>
                    <td>${formatCurrency(discount)}</td>
                    <td>${wastage > 0 ? formatCurrency(wastage) : '-'}</td>
                    <td>${formatCurrency(totalPrice)}</td>
                    <td>${formatCurrency(payableAmount)}</td>
                    <td>${transaction.reference_number || '-'}</td>
                    <td>${contactInfo}</td>
                    <td>${transaction.notes || '-'}</td>
                    <td>
                        <a href="invoice.html?id=${transaction.id}" class="btn btn-sm btn-outline-primary" title="Generate Invoice">
                            <i class="fas fa-file-invoice"></i>
                        </a>
                    </td>
                `;
                
                tableBody.appendChild(row);
            }).catch(error => {
                console.error('Error loading product details for transaction:', error);
                
                // Fallback if product details can't be loaded
                row.innerHTML = `
                    <td>${formattedDate}</td>
                    <td>${transaction.product_name}</td>
                    <td><span class="${transactionClass}">${transactionLabel}</span></td>
                    <td>${transaction.quantity}</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>${transaction.reference_number || '-'}</td>
                    <td>${contactInfo}</td>
                    <td>${transaction.notes || '-'}</td>
                    <td>
                        <a href="invoice.html?id=${transaction.id}" class="btn btn-sm btn-outline-primary" title="Generate Invoice">
                            <i class="fas fa-file-invoice"></i>
                        </a>
                    </td>
                `;
                
                tableBody.appendChild(row);
            });
        });
        
        // Show message if no history
        if (recentHistory.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="13" class="text-center">No stock transactions found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading stock history:', error);
        throw error;
    }
}

// Format currency value
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'BDT',
        minimumFractionDigits: 2
    }).format(value);
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
            // Show appropriate supplier/client fields based on transaction type
            if (this.value === 'IN') {
                document.getElementById('supplierInfo').style.display = 'block';
                document.getElementById('clientInfo').style.display = 'none';
            } else {
                document.getElementById('supplierInfo').style.display = 'none';
                document.getElementById('clientInfo').style.display = 'block';
            }
            
            // Update unit price based on transaction type if "Use Default Price" is checked
            const useDefaultPrice = document.getElementById('useDefaultPrice').checked;
            if (useDefaultPrice) {
                const unitPriceInput = document.getElementById('unitPrice');
                const transactionType = this.value;
                
                // Set price based on transaction type using stored data attributes
                if (transactionType === 'IN' && unitPriceInput.dataset.buyingPrice) {
                    unitPriceInput.value = unitPriceInput.dataset.buyingPrice;
                } else if (unitPriceInput.dataset.sellingPrice) {
                    unitPriceInput.value = unitPriceInput.dataset.sellingPrice;
                }
                
                // Ensure the unit price input remains read-only
                unitPriceInput.readOnly = true;
                
                // Update transaction summary
                updateTransactionSummary();
            }
            
            // Reload product details to update other information
            const selectedProductId = document.getElementById('product').value;
            if (selectedProductId) {
                loadProductDetails(selectedProductId);
            }
        });
    });
    
    // Use Default Price checkbox change
    document.getElementById('useDefaultPrice').addEventListener('change', function() {
        const unitPriceInput = document.getElementById('unitPrice');
        const selectedProductId = document.getElementById('product').value;
        
        if (selectedProductId) {
            if (this.checked) {
                // Set price based on transaction type using stored data attributes
                const transactionType = document.querySelector('input[name="stockType"]:checked').value;
                
                if (transactionType === 'IN' && unitPriceInput.dataset.buyingPrice) {
                    unitPriceInput.value = unitPriceInput.dataset.buyingPrice;
                } else if (unitPriceInput.dataset.sellingPrice) {
                    unitPriceInput.value = unitPriceInput.dataset.sellingPrice;
                }
                
                // Make the unit price input read-only when using default price
                unitPriceInput.readOnly = true;
                
                // Update transaction summary
                updateTransactionSummary();
            } else {
                // Allow user to enter custom price by making the field editable
                unitPriceInput.readOnly = false;
            }
        } else {
            // No product selected, nothing to do
            if (this.checked) {
                showNotification('Please select a product first', 'warning');
                this.checked = false;
            }
        }
    });
    
    // Update transaction summary when quantity, unit price, or discount changes
    document.getElementById('quantity').addEventListener('input', updateTransactionSummary);
    document.getElementById('unitPrice').addEventListener('input', updateTransactionSummary);
    document.getElementById('discount').addEventListener('input', updateTransactionSummary);
    document.getElementById('wastage').addEventListener('input', updateTransactionSummary);
    
    // Supplier select change
    const supplierSelect = document.getElementById('supplierSelect');
    if (supplierSelect) {
        supplierSelect.addEventListener('change', function() {
            const supplierId = this.value;
            if (supplierId) {
                getSupplierById(supplierId).then(supplier => {
                    document.getElementById('supplier').value = supplier.name;
                    document.getElementById('supplierContact').value = supplier.contact_person || '';
                });
            }
        });
    }
    
    // Client select change
    const clientSelect = document.getElementById('clientSelect');
    if (clientSelect) {
        clientSelect.addEventListener('change', function() {
            const clientId = this.value;
            if (clientId) {
                getClientById(clientId).then(client => {
                    document.getElementById('client').value = client.name;
                    document.getElementById('clientContact').value = client.contact_person || '';
                });
            }
        });
    }
    
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
        const discount = document.getElementById('discount').value ?
                         parseFloat(document.getElementById('discount').value) : 0;
        const wastage = document.getElementById('wastage').value ?
                         parseFloat(document.getElementById('wastage').value) : 0;
        
        // Get supplier or client data based on transaction type
        let supplier = null;
        let supplierContact = null;
        let supplierId = null;
        let client = null;
        let clientContact = null;
        let clientId = null;
        
        if (stockType === 'IN') {
            supplier = document.getElementById('supplier').value;
            supplierContact = document.getElementById('supplierContact').value;
            
            // Get supplier ID if selected from dropdown
            const supplierSelect = document.getElementById('supplierSelect');
            if (supplierSelect && supplierSelect.value) {
                supplierId = supplierSelect.value;
            }
        } else {
            client = document.getElementById('client').value;
            clientContact = document.getElementById('clientContact').value;
            
            // Get client ID if selected from dropdown
            const clientSelect = document.getElementById('clientSelect');
            if (clientSelect && clientSelect.value) {
                clientId = clientSelect.value;
            }
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
                discount: discount,
                wastage: wastage,
                supplier: supplier,
                supplier_contact: supplierContact,
                client: client,
                client_contact: clientContact,
                supplier_id: supplierId,
                client_id: clientId
            };
            // Mark as wastage if wastage value is greater than 0
            if (wastage > 0) {
                transactionData.is_wastage = true;
            }
            
            // Update stock
            const response = await updateStockWithDetails(transactionData);
            
            // Show success message
            showNotification('Stock transaction saved successfully');
            
            // Ask if user wants to generate invoice
            if (confirm('Transaction saved. Do you want to generate an invoice?')) {
                window.location.href = `invoice.html?id=${response.transaction_id}`;
                return;
            }
            
            // Reload stock history
            await loadStockHistory();
            
            // Reload product details
            await loadProductDetails(productId);
            
            // Reset form
            document.getElementById('quantity').value = '';
            document.getElementById('notes').value = '';
            document.getElementById('unitPrice').value = '';
            document.getElementById('discount').value = '0';
            document.getElementById('wastage').value = '0';
            document.getElementById('referenceNumber').value = '';
            document.getElementById('supplier').value = '';
            document.getElementById('supplierContact').value = '';
            document.getElementById('client').value = '';
            document.getElementById('clientContact').value = '';
            document.getElementById('stockIn').checked = true;
            
            if (document.getElementById('supplierSelect')) {
                document.getElementById('supplierSelect').value = '';
            }
            
            if (document.getElementById('clientSelect')) {
                document.getElementById('clientSelect').value = '';
            }
            
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

// Load product details when a product is selected
async function loadProductDetails(productId) {
    if (!productId) {
        // Hide product details and show placeholder
        document.getElementById('productDetails').classList.add('d-none');
        document.getElementById('noProductSelected').classList.remove('d-none');
        return;
    }
    
    try {
        const product = await getProductById(productId);
        
        // Show product details
        document.getElementById('productDetails').classList.remove('d-none');
        document.getElementById('noProductSelected').classList.add('d-none');
        
        // Fill in product details
        document.getElementById('productName').textContent = product.name;
        document.getElementById('productSKU').textContent = product.sku;
        document.getElementById('productType').textContent = product.type;
        document.getElementById('productLocation').textContent = product.location || 'Not specified';
        document.getElementById('productStock').textContent = `${product.quantity} ${product.unit_of_measure || 'units'}`;
        document.getElementById('productBatch').textContent = product.batch_number || 'Not specified';
        document.getElementById('productBarcode').textContent = product.barcode || 'Not specified';
        
        // Set expiry date
        if (product.expiry_date) {
            const expiryDate = new Date(product.expiry_date);
            document.getElementById('productExpiry').textContent = expiryDate.toLocaleDateString();
        } else {
            document.getElementById('productExpiry').textContent = 'Not specified';
        }
        
        // Get buying and selling prices
        const buyingPrice = product.buying_price || product.price || 0;
        const sellingPrice = product.selling_price || product.price || 0;
        
        // Calculate profit margin
        let profitMargin = 0;
        let profitPercentage = 0;
        
        if (buyingPrice > 0) {
            profitMargin = sellingPrice - buyingPrice;
            profitPercentage = (profitMargin / buyingPrice) * 100;
        }
        
        // Display prices and profit margin
        document.getElementById('productBuyingPrice').textContent = formatCurrency(buyingPrice);
        document.getElementById('productSellingPrice').textContent = formatCurrency(sellingPrice);
        document.getElementById('productProfitMargin').textContent = `${formatCurrency(profitMargin)} (${profitPercentage.toFixed(2)}%)`;
        
        // Set text color for profit margin based on value
        const profitMarginElement = document.getElementById('productProfitMargin');
        if (profitMargin > 0) {
            profitMarginElement.classList.add('text-success');
            profitMarginElement.classList.remove('text-danger', 'text-warning');
        } else if (profitMargin < 0) {
            profitMarginElement.classList.add('text-danger');
            profitMarginElement.classList.remove('text-success', 'text-warning');
        } else {
            profitMarginElement.classList.add('text-warning');
            profitMarginElement.classList.remove('text-success', 'text-danger');
        }
        
        // Store default prices as data attributes on the unit price input
        const unitPriceInput = document.getElementById('unitPrice');
        unitPriceInput.dataset.buyingPrice = buyingPrice;
        unitPriceInput.dataset.sellingPrice = sellingPrice;
        
        // Check if the "Use Default Price" checkbox is checked
        const useDefaultPrice = document.getElementById('useDefaultPrice').checked;
        
        if (useDefaultPrice) {
            // Determine which price to show in the unit price field based on transaction type
            const transactionType = document.querySelector('input[name="stockType"]:checked').value;
            
            // Set unit price based on transaction type
            if (transactionType === 'IN') {
                // For stock in (purchase), use buying price
                unitPriceInput.value = buyingPrice;
            } else {
                // For stock out (sale), use selling price
                unitPriceInput.value = sellingPrice;
            }
            
            // Make the unit price input read-only when using default price
            unitPriceInput.readOnly = true;
        } else {
            // If not using default price, ensure the field is editable
            unitPriceInput.readOnly = false;
        }
        
        // Update transaction summary
        updateTransactionSummary();
        
        return product;
    } catch (error) {
        console.error('Error loading product details:', error);
        showNotification('Error loading product details', 'danger');
        
        // Hide product details and show placeholder with error
        document.getElementById('productDetails').classList.add('d-none');
        document.getElementById('noProductSelected').classList.remove('d-none');
        document.getElementById('noProductSelected').innerHTML = `
            <p class="text-danger">Error loading product details. Please try again.</p>
        `;
        
        return null;
    }
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

// Update transaction summary when quantity, unit price, or discount changes
function updateTransactionSummary() {
    const quantity = parseFloat(document.getElementById('quantity').value) || 0;
    const unitPrice = parseFloat(document.getElementById('unitPrice').value) || 0;
    const discount = parseFloat(document.getElementById('discount').value) || 0;
    const wastage = parseFloat(document.getElementById('wastage').value) || 0;
    
    // Calculate values
    const totalPrice = quantity * unitPrice;
    const payableAmount = totalPrice - discount;
    
    // Update display
    document.getElementById('totalPriceDisplay').textContent = formatCurrency(totalPrice);
    document.getElementById('discountDisplay').textContent = formatCurrency(discount);
    document.getElementById('wastageLossDisplay').textContent = formatCurrency(wastage);
    document.getElementById('payableAmountDisplay').textContent = formatCurrency(payableAmount);
}