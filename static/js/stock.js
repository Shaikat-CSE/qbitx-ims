// stock.js - JavaScript for stock transaction form

document.addEventListener('DOMContentLoaded', function() {
    // Initial setup when page loads
    updateFormFields();
    updatePaymentFields();
    updateTransactionPreview();
    
    // Add event listener to transaction type dropdown
    const transactionTypeSelect = document.getElementById('id_transaction_type');
    if (transactionTypeSelect) {
        transactionTypeSelect.addEventListener('change', function() {
            updateFormFields();
            updatePaymentFields();
            updateTransactionPreview();
        });
    }
    
    // Add event listener to payment status dropdown
    const paymentStatusSelect = document.getElementById('id_payment_status');
    if (paymentStatusSelect) {
        paymentStatusSelect.addEventListener('change', function() {
            updatePaymentFields();
            updateTransactionPreview();
        });
    }
    
    // Add event listener to product dropdown for price updates and info
    const productSelect = document.getElementById('id_product');
    if (productSelect) {
        productSelect.addEventListener('change', function() {
            updateProductPrices();
            showProductInfo();
            updateTransactionPreview();
        });
        // On page load, if a product is selected, show info and populate fields
        if (productSelect.value) {
            updateProductPrices();
            showProductInfo();
            updateTransactionPreview();
        }
    }
    
    // Add event listeners to quantity and price fields
    const quantityInput = document.getElementById('id_quantity');
    const buyingPriceInput = document.getElementById('id_buying_price');
    const sellingPriceInput = document.getElementById('id_selling_price');
    const sourceWarehouseSelect = document.getElementById('id_source_warehouse');
    
    if (quantityInput) {
        quantityInput.addEventListener('input', updateTransactionPreview);
    }
    
    if (buyingPriceInput) {
        buyingPriceInput.addEventListener('input', updateTransactionPreview);
    }
    
    if (sellingPriceInput) {
        sellingPriceInput.addEventListener('input', function() {
            calculateTaxes();
            updateTransactionPreview();
        });
    }
    
    if (sourceWarehouseSelect) {
        sourceWarehouseSelect.addEventListener('change', updateTransactionPreview);
    }
    
    // Always show tax options section
    const taxOptionsSection = document.getElementById('taxOptionsSection');
    if (taxOptionsSection) {
        taxOptionsSection.style.display = 'block';
    }
    
    // Handle apply taxes checkbox
    const applyTaxesCheckbox = document.getElementById('applyTaxes');
    const taxDetails = document.getElementById('taxDetails');
    
    if (applyTaxesCheckbox) {
        applyTaxesCheckbox.addEventListener('change', function() {
            if (this.checked) {
                taxDetails.style.display = 'block';
                document.getElementById('id_apply_taxes').value = 'True';
                calculateTaxes();
                updateTransactionPreview();
            } else {
                taxDetails.style.display = 'none';
                document.getElementById('id_apply_taxes').value = 'False';
                updateTransactionPreview();
            }
        });
    }
    
    // Handle tax rate changes
    const vatRateInput = document.getElementById('vatRate');
    const aitRateInput = document.getElementById('aitRate');
    
    if (vatRateInput && aitRateInput && sellingPriceInput) {
        vatRateInput.addEventListener('input', function() {
            document.getElementById('vatRateDisplay').textContent = this.value;
            calculateTaxes();
            updateTransactionPreview();
        });
        
        aitRateInput.addEventListener('input', function() {
            document.getElementById('aitRateDisplay').textContent = this.value;
            calculateTaxes();
            updateTransactionPreview();
        });
    }
});

// Function to update form fields based on transaction type
function updateFormFields() {
    const transactionType = document.getElementById('id_transaction_type').value;
    const supplierField = document.getElementById('id_supplier').closest('.mb-3');
    const clientField = document.getElementById('id_client').closest('.mb-3');
    const sourceWarehouseField = document.getElementById('id_source_warehouse').closest('.mb-3');
    const destinationWarehouseField = document.getElementById('id_destination_warehouse').closest('.mb-3');
    const wastageField = document.getElementById('id_wastage_amount').closest('.mb-3');
    const paymentOptionsSection = document.getElementById('paymentOptionsSection');
    
    // Hide all conditional fields first
    supplierField.style.display = 'none';
    clientField.style.display = 'none';
    sourceWarehouseField.style.display = 'none';
    destinationWarehouseField.style.display = 'none';
    wastageField.style.display = 'none';
    
    // Show relevant fields based on transaction type
    switch (transactionType) {
        case 'in':
            supplierField.style.display = 'block';
            destinationWarehouseField.style.display = 'block';
            paymentOptionsSection.style.display = 'block'; // Show payment options for stock in
            break;
        case 'out':
            clientField.style.display = 'block';
            sourceWarehouseField.style.display = 'block';
            paymentOptionsSection.style.display = 'block'; // Show payment options for stock out
            break;
        case 'wastage':
            sourceWarehouseField.style.display = 'block';
            wastageField.style.display = 'block';
            paymentOptionsSection.style.display = 'none'; // Hide payment options for wastage
            // Set payment status to 'na' for wastage
            const paymentStatusSelect = document.getElementById('id_payment_status');
            if (paymentStatusSelect) {
                paymentStatusSelect.value = 'na';
            }
            break;
        case 'return':
            supplierField.style.display = 'block';
            clientField.style.display = 'block';
            destinationWarehouseField.style.display = 'block';
            paymentOptionsSection.style.display = 'block'; // Show payment options for returns
            break;
        case 'transfer':
            sourceWarehouseField.style.display = 'block';
            destinationWarehouseField.style.display = 'block';
            paymentOptionsSection.style.display = 'none'; // Hide payment options for transfers
            // Set payment status to 'na' for transfers
            const paymentStatusTransfer = document.getElementById('id_payment_status');
            if (paymentStatusTransfer) {
                paymentStatusTransfer.value = 'na';
            }
            break;
    }
    
    // Reset category and product selections when transaction type changes
    const productCategorySelect = document.getElementById('product_category');
    const productSelect = document.getElementById('id_product');
    
    if (productCategorySelect) {
        productCategorySelect.innerHTML = '<option value="">Select Warehouse First</option>';
    }
    
    if (productSelect) {
        productSelect.innerHTML = '<option value="">Select Category First</option>';
        
        // Clear product info displays
        const productInfoCard = document.getElementById('productInfoCard');
        const transactionDetailsCard = document.getElementById('transactionDetailsCard');
        
        if (productInfoCard) {
            productInfoCard.style.display = 'none';
        }
        
        if (transactionDetailsCard) {
            transactionDetailsCard.style.display = 'none';
        }
    }
}

// Function to update payment fields based on payment status
function updatePaymentFields() {
    const paymentStatus = document.getElementById('id_payment_status').value;
    const dueDateField = document.getElementById('paymentDueDateField');
    const amountPaidField = document.getElementById('amountPaidField');
    
    // Hide all payment detail fields first
    dueDateField.style.display = 'none';
    amountPaidField.style.display = 'none';
    
    // Show relevant fields based on payment status
    switch (paymentStatus) {
        case 'paid':
            // No additional fields needed for paid
            break;
        case 'due':
            dueDateField.style.display = 'block';
            // Clear amount paid for due payments
            document.getElementById('id_amount_paid').value = '0';
            break;
        case 'partial':
            dueDateField.style.display = 'block';
            amountPaidField.style.display = 'block';
            break;
        case 'credit':
            dueDateField.style.display = 'block';
            // Clear amount paid for credit payments
            document.getElementById('id_amount_paid').value = '0';
            break;
        case 'na':
            // No additional fields needed for not applicable
            break;
    }
    
    // For transactions that don't use payment statuses
    const transactionType = document.getElementById('id_transaction_type').value;
    if (transactionType === 'wastage' || transactionType === 'transfer') {
        document.getElementById('id_payment_status').value = 'na';
    }
}

// Function to fetch product prices and update form
function updateProductPrices() {
    const productId = document.getElementById('id_product').value;
    if (!productId) return;
    
    // Fetch product data using AJAX with exact ID match
    fetch(`/imstransform/products/?format=json&search=${productId}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                // Find the exact product by ID
                const product = data.find(p => p.id === parseInt(productId)) || data[0];
                
                // Update buying and selling price fields
                document.getElementById('id_buying_price').value = product.buying_price;
                document.getElementById('id_selling_price').value = product.selling_price;
                // If product has a warehouse, set source warehouse field
                if (product.warehouse_id) {
                    const sourceWarehouseSelect = document.getElementById('id_source_warehouse');
                    if (sourceWarehouseSelect) {
                        sourceWarehouseSelect.value = product.warehouse_id;
                    }
                }
                // Update tax calculations if applicable
                const applyTaxesCheckbox = document.getElementById('applyTaxes');
                if (applyTaxesCheckbox && applyTaxesCheckbox.checked) {
                    calculateTaxes();
                }
                // Always update product info card after updating prices
                showProductInfo(product);
            }
        })
        .catch(error => console.error('Error fetching product data:', error));
}

// Function to show product info card and update info
function showProductInfo(productData) {
    const productId = document.getElementById('id_product').value;
    const productInfoCard = document.getElementById('productInfoCard');
    if (!productId) {
        productInfoCard.style.display = 'none';
        return;
    }
    
    // If product data is already provided, use it
    if (productData) {
        updateProductInfoCard(productData);
        return;
    }
    
    // Otherwise fetch the product data
    fetch(`/imstransform/products/?format=json&search=${productId}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                // Find the exact product by ID
                const product = data.find(p => p.id === parseInt(productId)) || data[0];
                updateProductInfoCard(product);
            }
        })
        .catch(error => {
            console.error('Error fetching product details:', error);
            productInfoCard.style.display = 'none';
        });
}

// Helper function to update the product info card with product data
function updateProductInfoCard(product) {
    const productInfoCard = document.getElementById('productInfoCard');
    
    document.getElementById('productName').textContent = product.name;
    document.getElementById('productSku').textContent = product.sku;
    document.getElementById('productCategory').textContent = product.category_name || '-';
    document.getElementById('productQuantity').textContent = product.quantity;
    document.getElementById('productUom').textContent = product.unit_of_measure;
    document.getElementById('productBuyingPrice').textContent = product.buying_price;
    document.getElementById('productSellingPrice').textContent = product.selling_price;
    
    // Calculate profit margin
    const buyingPrice = parseFloat(product.buying_price);
    const sellingPrice = parseFloat(product.selling_price);
    let profitMargin = 0;
    if (buyingPrice > 0) {
        profitMargin = ((sellingPrice - buyingPrice) / buyingPrice) * 100;
    }
    
    document.getElementById('productProfitMargin').textContent = profitMargin.toFixed(2);
    document.getElementById('productWarehouse').textContent = product.warehouse_name || '-';
    productInfoCard.style.display = 'block';
    
    // After showing product info, fetch and show transaction details
    fetchTransactionDetails(product.id);
}

// Function to fetch and display transaction details for the selected product
function fetchTransactionDetails(productId) {
    if (!productId) {
        const productSelect = document.getElementById('id_product');
        if (productSelect) {
            productId = productSelect.value;
        }
        if (!productId) return;
    }
    
    const transactionDetailsCard = document.getElementById('transactionDetailsCard');
    const transactionsList = document.getElementById('transactionsList');
    
    // Show loading indicator
    transactionsList.innerHTML = '<tr><td colspan="5" class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading transactions...</td></tr>';
    transactionDetailsCard.style.display = 'block';
    
    // Fetch transaction data using AJAX
    fetch(`/imstransform/stock/?format=json&product_id=${productId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Clear the transactions list
            transactionsList.innerHTML = '';
            
            if (data && data.length > 0) {
                // Sort transactions by date (newest first)
                data.sort((a, b) => new Date(b.transaction_date) - new Date(a.transaction_date));
                
                // Take only the 5 most recent transactions
                const recentTransactions = data.slice(0, 5);
                
                // Add each transaction to the list
                recentTransactions.forEach(transaction => {
                    const row = document.createElement('tr');
                    
                    // Format the date
                    const transactionDate = new Date(transaction.transaction_date);
                    const formattedDate = transactionDate.toLocaleDateString() + ' ' + 
                                         transactionDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                    
                    // Determine the badge class based on transaction type
                    let typeClass = 'bg-secondary';
                    if (transaction.transaction_type === 'in') typeClass = 'bg-primary';
                    if (transaction.transaction_type === 'out') typeClass = 'bg-info';
                    if (transaction.transaction_type === 'wastage') typeClass = 'bg-danger';
                    if (transaction.transaction_type === 'return') typeClass = 'bg-warning';
                    if (transaction.transaction_type === 'transfer') typeClass = 'bg-success';
                    
                    // Determine the payment status badge class
                    let statusClass = 'bg-secondary';
                    if (transaction.payment_status === 'paid') statusClass = 'bg-success';
                    if (transaction.payment_status === 'due') statusClass = 'bg-danger';
                    if (transaction.payment_status === 'partial') statusClass = 'bg-warning';
                    if (transaction.payment_status === 'credit') statusClass = 'bg-info';
                    
                    // Get transaction type display name
                    let typeDisplay = transaction.transaction_type.charAt(0).toUpperCase() + transaction.transaction_type.slice(1);
                    
                    // Get payment status display name
                    let statusDisplay = 'N/A';
                    if (transaction.payment_status === 'paid') statusDisplay = 'Paid';
                    if (transaction.payment_status === 'due') statusDisplay = 'Due';
                    if (transaction.payment_status === 'partial') statusDisplay = 'Partial';
                    if (transaction.payment_status === 'credit') statusDisplay = 'Credit';
                    
                    // Create the row content
                    row.innerHTML = `
                        <td>${transaction.id}</td>
                        <td>${formattedDate}</td>
                        <td><span class="badge ${typeClass}">${typeDisplay}</span></td>
                        <td>${transaction.quantity}</td>
                        <td><span class="badge ${statusClass}">${statusDisplay}</span></td>
                    `;
                    
                    transactionsList.appendChild(row);
                });
            } else {
                // No transactions found
                transactionsList.innerHTML = '<tr><td colspan="5" class="text-center">No transactions found for this product</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error fetching transaction data:', error);
            transactionsList.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading transactions</td></tr>';
        });
}

// Function to calculate taxes based on rates and selling price
function calculateTaxes() {
    const applyTaxesCheckbox = document.getElementById('applyTaxes');
    if (!applyTaxesCheckbox || !applyTaxesCheckbox.checked) return;
    
    const sellingPriceInput = document.getElementById('id_selling_price');
    const vatRateInput = document.getElementById('vatRate');
    const aitRateInput = document.getElementById('aitRate');
    
    const sellingPrice = parseFloat(sellingPriceInput.value) || 0;
    const vatRate = parseFloat(vatRateInput.value) || 0;
    const aitRate = parseFloat(aitRateInput.value) || 0;
    
    // Calculate after VAT deduction
    const vatAmount = sellingPrice * (vatRate / 100);
    const afterVat = sellingPrice - vatAmount;
    
    // Calculate after AIT deduction
    const aitAmount = afterVat * (aitRate / 100);
    const finalPrice = afterVat - aitAmount;
    
    // Update displays
    document.getElementById('originalPriceDisplay').textContent = sellingPrice.toFixed(2);
    document.getElementById('afterVatDisplay').textContent = afterVat.toFixed(2);
    document.getElementById('afterAitDisplay').textContent = finalPrice.toFixed(2);
    document.getElementById('finalPriceDisplay').textContent = finalPrice.toFixed(2);
    
    // Update hidden form fields
    document.getElementById('id_apply_taxes').value = applyTaxesCheckbox.checked;
    document.getElementById('id_vat_rate').value = vatRate;
    document.getElementById('id_ait_rate').value = aitRate;
    document.getElementById('id_final_price').value = finalPrice.toFixed(2);
} 

// Function to update the transaction preview card
function updateTransactionPreview() {
    // Get all the necessary form values
    const quantity = parseFloat(document.getElementById('id_quantity').value) || 0;
    const buyingPrice = parseFloat(document.getElementById('id_buying_price').value) || 0;
    const sellingPrice = parseFloat(document.getElementById('id_selling_price').value) || 0;
    const transactionTypeSelect = document.getElementById('id_transaction_type');
    const paymentStatusSelect = document.getElementById('id_payment_status');
    const sourceWarehouseSelect = document.getElementById('id_source_warehouse');
    const applyTaxesCheckbox = document.getElementById('applyTaxes');
    
    // Get the selected values
    const transactionType = transactionTypeSelect ? transactionTypeSelect.value : '';
    const paymentStatus = paymentStatusSelect ? paymentStatusSelect.value : '';
    const sourceWarehouse = sourceWarehouseSelect ? sourceWarehouseSelect.options[sourceWarehouseSelect.selectedIndex]?.text : '-';
    
    // Calculate unit price based on transaction type
    let unitPrice = 0;
    if (transactionType === 'out') {
        // For stock out, use selling price or final price if taxes are applied
        if (applyTaxesCheckbox && applyTaxesCheckbox.checked) {
            const finalPriceInput = document.getElementById('id_final_price');
            unitPrice = parseFloat(finalPriceInput.value) || sellingPrice;
        } else {
            unitPrice = sellingPrice;
        }
    } else {
        // For other transaction types, use buying price
        unitPrice = buyingPrice;
    }
    
    // Calculate total price
    const totalPrice = quantity * unitPrice;
    
    // Get transaction type display name
    let typeDisplay = '';
    switch (transactionType) {
        case 'in':
            typeDisplay = 'Stock In';
            break;
        case 'out':
            typeDisplay = 'Stock Out';
            break;
        case 'wastage':
            typeDisplay = 'Wastage';
            break;
        case 'return':
            typeDisplay = 'Return';
            break;
        case 'transfer':
            typeDisplay = 'Transfer';
            break;
        default:
            typeDisplay = '-';
    }
    
    // Get payment status display name
    let paymentStatusDisplay = '';
    switch (paymentStatus) {
        case 'paid':
            paymentStatusDisplay = 'Paid';
            break;
        case 'due':
            paymentStatusDisplay = 'Due';
            break;
        case 'partial':
            paymentStatusDisplay = 'Partially Paid';
            break;
        case 'credit':
            paymentStatusDisplay = 'Credit';
            break;
        case 'na':
            paymentStatusDisplay = 'N/A';
            break;
        default:
            paymentStatusDisplay = '-';
    }
    
    // Update the preview card
    document.getElementById('previewQuantity').textContent = quantity;
    document.getElementById('previewUnitPrice').textContent = unitPrice.toFixed(2);
    document.getElementById('previewTotalPrice').textContent = totalPrice.toFixed(2);
    document.getElementById('previewType').textContent = typeDisplay;
    document.getElementById('previewPaymentStatus').textContent = paymentStatusDisplay;
    
    // Update warehouse display based on transaction type
    const destinationWarehouseSelect = document.getElementById('id_destination_warehouse');
    const destinationWarehouse = destinationWarehouseSelect ? 
        destinationWarehouseSelect.options[destinationWarehouseSelect.selectedIndex]?.text : '-';
        
    if (transactionType === 'in' || transactionType === 'return') {
        document.getElementById('previewWarehouse').textContent = `To: ${destinationWarehouse}`;
    } else if (transactionType === 'out' || transactionType === 'wastage') {
        document.getElementById('previewWarehouse').textContent = `From: ${sourceWarehouse}`;
    } else if (transactionType === 'transfer') {
        document.getElementById('previewWarehouse').textContent = 
            `From: ${sourceWarehouse} → To: ${destinationWarehouse}`;
    } else {
        document.getElementById('previewWarehouse').textContent = sourceWarehouse;
    }
    
    // Handle tax preview section
    const taxPreviewSection = document.getElementById('taxPreviewSection');
    if (transactionType === 'out' && applyTaxesCheckbox && applyTaxesCheckbox.checked) {
        // Show tax preview section
        taxPreviewSection.style.display = 'block';
        
        // Get tax rates
        const vatRate = parseFloat(document.getElementById('vatRate').value) || 0;
        const aitRate = parseFloat(document.getElementById('aitRate').value) || 0;
        
        // Calculate tax deductions
        const vatDeduction = sellingPrice * (vatRate / 100);
        const afterVat = sellingPrice - vatDeduction;
        const aitDeduction = afterVat * (aitRate / 100);
        const afterTaxes = afterVat - aitDeduction;
        
        // Calculate profit
        const profit = afterTaxes - buyingPrice;
        const profitPercentage = buyingPrice > 0 ? (profit / buyingPrice) * 100 : 0;
        
        // Update tax preview values
        document.getElementById('previewVatDeduction').textContent = vatDeduction.toFixed(2);
        document.getElementById('previewAitDeduction').textContent = aitDeduction.toFixed(2);
        document.getElementById('previewAfterTaxes').textContent = afterTaxes.toFixed(2);
        
        // Display profit with color based on positive or negative
        const previewProfit = document.getElementById('previewProfit');
        previewProfit.textContent = `${profit.toFixed(2)} (${profitPercentage.toFixed(2)}%)`;
        if (profit > 0) {
            previewProfit.className = 'text-success';
        } else if (profit < 0) {
            previewProfit.className = 'text-danger';
        } else {
            previewProfit.className = '';
        }
    } else {
        // Hide tax preview section
        taxPreviewSection.style.display = 'none';
    }
} 