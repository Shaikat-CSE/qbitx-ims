// product-form.js - Product form functionality for QBITX IMS Transform Suppliers

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Initialize the product form
        await initProductForm();
    } catch (error) {
        console.error('Error initializing product form:', error);
        showNotification('Error loading product form data', 'danger');
    }
});

// Initialize product form
async function initProductForm() {
    // Initialize date picker for expiry date
    initDatePicker();
    
    // Load product types for dropdown
    await loadProductTypeOptions();
    
    // Check if editing existing product
    const urlParams = new URLSearchParams(window.location.search);
    const productId = urlParams.get('id');
    
    if (productId) {
        // Editing existing product
        document.getElementById('formTitle').textContent = 'Edit Product';
        await fillProductForm(parseInt(productId));
    } else {
        // Adding new product
        document.getElementById('formTitle').textContent = 'Add New Product';
        // Initialize quantity to 0
        document.getElementById('productQuantity').value = 0;
        // Initialize minimum stock level to 5
        document.getElementById('productMinStockLevel').value = 5;
        
        // Generate a unique SKU
        generateSKU();
        
        // Show helper message for new product
        const formCard = document.querySelector('.card-body');
        const helperMessage = document.createElement('div');
        helperMessage.className = 'alert alert-info mb-4';
        helperMessage.innerHTML = `
            <h5><i class="fas fa-info-circle"></i> Getting Started</h5>
            <p>Add products to any of the following categories:</p>
            <ul>
                <li>Fruits</li>
                <li>Spice</li>
                <li>Home Decor</li>
                <li>Cookware</li>
                <li>Bakery Ingredients</li>
            </ul>
            <p class="mt-2 mb-0"><strong>Tip:</strong> Use the barcode scanner to easily input product barcodes.</p>
        `;
        formCard.insertBefore(helperMessage, document.getElementById('productForm'));
    }
    
    // Set up event listeners
    setupEventListeners();
}

// Initialize date picker
function initDatePicker() {
    flatpickr("#productExpiryDate", {
        dateFormat: "Y-m-d",
        allowInput: true,
        altInput: true,
        altFormat: "F j, Y"
    });
}

// Generate a unique SKU based on product type and timestamp
function generateSKU() {
    const timestamp = new Date().getTime().toString().slice(-6);
    document.getElementById('productSKU').value = `GN${timestamp}`;
}

// Handle barcode scanning
function handleBarcodeScan() {
    // Show a modal dialog for scanning
    const modalHTML = `
        <div class="modal fade" id="barcodeScanModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Scan Barcode</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center">
                        <p>Please scan the barcode using your scanner device.</p>
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
            // We have a barcode, process it
            document.getElementById('productBarcode').value = this.value;
            modal.hide();
            
            // Remove the modal from the DOM after hiding
            document.getElementById('barcodeScanModal').addEventListener('hidden.bs.modal', function() {
                this.remove();
            });
        }
    });
}

// Load product types for form dropdown
async function loadProductTypeOptions() {
    try {
        const productTypes = await getProductTypes();
        const typeSelect = document.getElementById('productType');
        
        // Clear existing options except the first one
        const firstOption = typeSelect.firstElementChild;
        typeSelect.innerHTML = '';
        if (firstOption) {
            typeSelect.appendChild(firstOption);
        }
        
        // Add product type options
        productTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type.name;
            option.textContent = type.name;
            typeSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading product types:', error);
        throw error;
    }
}

// Fill product form with existing product data
async function fillProductForm(productId) {
    try {
        const product = await getProductById(productId);
        
        // Set form values for basic fields
        document.getElementById('productId').value = product.id;
        document.getElementById('productName').value = product.name;
        document.getElementById('productSKU').value = product.sku;
        document.getElementById('productType').value = product.type;
        document.getElementById('productQuantity').value = product.quantity;
        
        // Set UOM
        if (product.unit_of_measure) {
            document.getElementById('productUOM').value = product.unit_of_measure;
        }
        
        // Set buying and selling prices
        document.getElementById('productBuyingPrice').value = product.buying_price || product.price;
        document.getElementById('productSellingPrice').value = product.selling_price || product.price;
        
        // Set wastage if available and the field exists
        const productWastageElement = document.getElementById('productWastage');
        if (product.wastage !== undefined && productWastageElement) {
            productWastageElement.value = product.wastage;
        }
        
        // Calculate and display profit margin
        calculateProfitMargin();
        
        // Set tracking information
        document.getElementById('productLocation').value = product.location || '';
        document.getElementById('productBarcode').value = product.barcode || '';
        document.getElementById('productBatchNumber').value = product.batch_number || '';
        document.getElementById('productMinStockLevel').value = product.minimum_stock_level || 5;
        
        // Set expiry date if it exists
        if (product.expiry_date) {
            const datePicker = document.getElementById('productExpiryDate')._flatpickr;
            datePicker.setDate(product.expiry_date);
        }
    } catch (error) {
        console.error('Error loading product:', error);
        showNotification('Error loading product data', 'danger');
        
        // Redirect to products page
        setTimeout(() => {
            window.location.href = 'products.html';
        }, 2000);
    }
}

// Set up form submission and other event listeners
function setupEventListeners() {
    // Barcode scanner button
    document.getElementById('scanBarcodeBtn').addEventListener('click', handleBarcodeScan);
    
    // Auto-generate SKU when product name changes (only for new products)
    if (!document.getElementById('productId').value) {
        document.getElementById('productName').addEventListener('blur', function() {
            if (this.value && document.getElementById('productSKU').value === '') {
                generateSKU();
            }
        });
    }
    
    // Add event listeners for price fields to calculate profit margin
    document.getElementById('productBuyingPrice').addEventListener('input', calculateProfitMargin);
    document.getElementById('productSellingPrice').addEventListener('input', calculateProfitMargin);
    
    // Form submission
    document.getElementById('productForm').addEventListener('submit', saveProductForm);
}

// Calculate profit margin based on buying and selling prices
function calculateProfitMargin() {
    const buyingPrice = parseFloat(document.getElementById('productBuyingPrice').value) || 0;
    const sellingPrice = parseFloat(document.getElementById('productSellingPrice').value) || 0;
    
    if (buyingPrice > 0 && sellingPrice > 0) {
        const profit = sellingPrice - buyingPrice;
        const marginPercentage = (profit / buyingPrice) * 100;
        document.getElementById('profitMargin').value = marginPercentage.toFixed(2);
        
        // Add visual feedback based on margin value
        const profitMarginInput = document.getElementById('profitMargin');
        if (marginPercentage < 10) {
            profitMarginInput.className = 'form-control bg-danger text-white';
        } else if (marginPercentage < 20) {
            profitMarginInput.className = 'form-control bg-warning';
        } else {
            profitMarginInput.className = 'form-control bg-success text-white';
        }
    } else {
        document.getElementById('profitMargin').value = '0.00';
        document.getElementById('profitMargin').className = 'form-control';
    }
}

// Save product form
async function saveProductForm(event) {
    event.preventDefault();
    
    // Validate form
    const form = document.getElementById('productForm');
    if (!form.checkValidity()) {
        event.stopPropagation();
        form.classList.add('was-validated');
        return;
    }
    
    // Get form values
    const productId = document.getElementById('productId').value;
    const name = document.getElementById('productName').value;
    const sku = document.getElementById('productSKU').value;
    const type = document.getElementById('productType').value;
    const quantity = parseInt(document.getElementById('productQuantity').value) || 0;
    const buyingPrice = parseFloat(document.getElementById('productBuyingPrice').value) || 0;
    const sellingPrice = parseFloat(document.getElementById('productSellingPrice').value) || 0;
    const location = document.getElementById('productLocation').value;
    const barcode = document.getElementById('productBarcode').value;
    const batchNumber = document.getElementById('productBatchNumber').value;
    const expiryDate = document.getElementById('productExpiryDate').value;
    const minStockLevel = parseInt(document.getElementById('productMinStockLevel').value) || 5;
    const unitOfMeasure = document.getElementById('productUOM').value;
    
    // Safely get wastage value if the element exists
    const wastageElement = document.getElementById('productWastage');
    const wastage = wastageElement ? (parseFloat(wastageElement.value) || 0) : 0;
    
    // Create product object
    const productData = {
        name,
        sku,
        type,
        quantity,
        buying_price: buyingPrice,
        selling_price: sellingPrice,
        location,
        barcode,
        shipment_number: batchNumber,
        expiry_date: expiryDate || null,
        minimum_stock_level: minStockLevel,
        unit_of_measure: unitOfMeasure,
        wastage
    };
    
    try {
        let result;
        
        if (productId) {
            // Update existing product
            productData.id = parseInt(productId);
            result = await updateProduct(productData);
            showNotification('Product updated successfully', 'success');
        } else {
            // Create new product
            result = await createProduct(productData);
            showNotification('Product created successfully', 'success');
        }
        
        console.log('Product saved:', result);
        
        // Redirect to products page
        setTimeout(() => {
            window.location.href = 'products.html';
        }, 1000);
    } catch (error) {
        console.error('Error saving product:', error);
        showNotification('Error saving product. Please try again.', 'danger');
    }
} 