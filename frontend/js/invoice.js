// invoice.js - Invoice generation functionality for QBITX IMS Transform Suppliers

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Get transaction ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const transactionId = urlParams.get('id');
        
        if (!transactionId) {
            showNotification('No transaction ID provided', 'danger');
            setTimeout(() => {
                window.location.href = 'stock.html';
            }, 2000);
            return;
        }
        
        // Load transaction data
        await loadTransactionData(transactionId);
        
        // Set up event listeners
        setupEventListeners();
    } catch (error) {
        console.error('Error initializing invoice page:', error);
        showNotification('Error loading invoice data', 'danger');
    }
});

// Set up event listeners
function setupEventListeners() {
    // Print invoice button
    document.getElementById('printInvoiceBtn').addEventListener('click', function() {
        window.print();
    });
}

// Load transaction data
async function loadTransactionData(transactionId) {
    try {
        // Get transaction details
        const transaction = await getTransactionById(transactionId);
        
        if (!transaction) {
            showNotification('Transaction not found', 'danger');
            return;
        }
        
        // Get product details
        const product = await getProductById(transaction.product);
        
        if (!product) {
            showNotification('Product details not found', 'danger');
            return;
        }
        
        // Log data for debugging
        console.log('Transaction data:', transaction);
        console.log('Product data:', product);
        
        // Validate required fields
        const validatedTransaction = validateTransactionData(transaction, product);
        
        // Set invoice number (using transaction ID)
        document.getElementById('invoiceNumber').textContent = `INV-${validatedTransaction.id.toString().padStart(5, '0')}`;
        
        // Set invoice date in a compact format
        const invoiceDate = new Date();
        const invoiceDateOptions = { year: 'numeric', month: 'short', day: 'numeric' };
        document.getElementById('invoiceDate').textContent = invoiceDate.toLocaleDateString(undefined, invoiceDateOptions);
        
        // Set reference number
        document.getElementById('referenceNumber').textContent = validatedTransaction.reference_number || '-';
        
        // Set transaction date - use more compact format for printing
        const transactionDate = new Date(validatedTransaction.date);
        const dateOptions = { year: 'numeric', month: 'short', day: 'numeric' };
        const timeOptions = { hour: '2-digit', minute:'2-digit' };
        document.getElementById('transactionDate').textContent = 
            transactionDate.toLocaleDateString(undefined, dateOptions) + ' ' + 
            transactionDate.toLocaleTimeString('en-US', timeOptions);
        
        // Set transaction type
        const transactionType = validatedTransaction.type === 'IN' ? 'Purchase (Stock In)' : 'Sale (Stock Out)';
        document.getElementById('transactionType').textContent = transactionType;
        
        // Set client or supplier information
        if (validatedTransaction.type === 'OUT') {
            // Show client section, hide supplier section
            document.getElementById('clientSection').style.display = 'block';
            document.getElementById('supplierSection').style.display = 'none';
            
            // Set client details
            document.getElementById('clientName').textContent = validatedTransaction.client || 'Walk-in Customer';
            document.getElementById('clientContact').textContent = validatedTransaction.client_contact || '';
            
            // If client_ref exists, get more details
            if (validatedTransaction.client_ref) {
                try {
                    const client = await getClientById(validatedTransaction.client_ref);
                    if (client) {
                        document.getElementById('clientAddress').textContent = client.address || '';
                        document.getElementById('clientEmail').textContent = client.email || '';
                    }
                } catch (error) {
                    console.error('Error loading client details:', error);
                }
            }
        } else {
            // Show supplier section, hide client section
            document.getElementById('clientSection').style.display = 'none';
            document.getElementById('supplierSection').style.display = 'block';
            
            // Set supplier details
            document.getElementById('supplierName').textContent = validatedTransaction.supplier || 'Unknown Supplier';
            document.getElementById('supplierContact').textContent = validatedTransaction.supplier_contact || '';
            
            // If supplier_ref exists, get more details
            if (validatedTransaction.supplier_ref) {
                try {
                    const supplier = await getSupplierById(validatedTransaction.supplier_ref);
                    if (supplier) {
                        document.getElementById('supplierAddress').textContent = supplier.address || '';
                        document.getElementById('supplierEmail').textContent = supplier.email || '';
                    }
                } catch (error) {
                    console.error('Error loading supplier details:', error);
                }
            }
        }
        
        // Set invoice items
        const invoiceItems = document.getElementById('invoiceItems');
        
        // Clear existing items
        invoiceItems.innerHTML = '';
        
        // Add product row
        const row = document.createElement('tr');
        
        // Calculate total
        const unitPrice = validatedTransaction.unit_price || validatedTransaction.product_details.price;
        const discount = validatedTransaction.discount || 0;
        const totalPrice = unitPrice * validatedTransaction.quantity;
        const payableAmount = totalPrice - discount;
        
        // Debug the values
        console.log('Values to display:');
        console.log('- Product name:', validatedTransaction.product_details.name);
        console.log('- SKU:', validatedTransaction.product_details.sku);
        console.log('- Quantity:', validatedTransaction.quantity);
        console.log('- UOM:', validatedTransaction.product_details.unit_of_measure);
        console.log('- Unit Price:', unitPrice);
        console.log('- Discount:', discount);
        console.log('- Total Price:', totalPrice);
        console.log('- Payable Amount:', payableAmount);
        
        row.innerHTML = `
            <td>1</td>
            <td>${validatedTransaction.product_details.name}</td>
            <td>${validatedTransaction.product_details.sku}</td>
            <td>${validatedTransaction.quantity}</td>
            <td>${validatedTransaction.product_details.unit_of_measure}</td>
            <td>${formatCurrency(unitPrice)}</td>
            <td>${formatCurrency(discount)}</td>
            <td>${formatCurrency(totalPrice)}</td>
            <td>${formatCurrency(payableAmount)}</td>
        `;
        
        invoiceItems.appendChild(row);
        
        // Set totals
        document.getElementById('subtotal').textContent = formatCurrency(totalPrice);
        document.getElementById('discountTotal').textContent = formatCurrency(discount);
        document.getElementById('total').textContent = formatCurrency(payableAmount);
        
        // Set notes
        document.getElementById('invoiceNotes').textContent = validatedTransaction.notes || 'Thank you for your business!';
        
    } catch (error) {
        console.error('Error loading transaction data:', error);
        showNotification('Error loading transaction data', 'danger');
    }
}

// Validate transaction data and ensure all required fields are present
function validateTransactionData(transaction, product) {
    // Determine which price to use based on transaction type
    let price = transaction.unit_price;
    if (!price) {
        if (transaction.type === 'IN') {
            price = product.buying_price || product.price || 0;
        } else {
            price = product.selling_price || product.price || 0;
        }
    }
    
    const validatedTransaction = {
        ...transaction,
        id: transaction.id || 0,
        product: transaction.product || 0,
        quantity: transaction.quantity || 0,
        type: transaction.type || 'OUT',
        notes: transaction.notes || '',
        date: transaction.date || new Date().toISOString(),
        reference_number: transaction.reference_number || '',
        unit_price: price,
        discount: transaction.discount || 0,
        supplier: transaction.supplier || '',
        supplier_contact: transaction.supplier_contact || '',
        client: transaction.client || '',
        client_contact: transaction.client_contact || '',
        supplier_ref: transaction.supplier_ref || null,
        client_ref: transaction.client_ref || null,
        product_name: transaction.product_name || product.name || 'Unknown Product',
        
        // Add product details directly to the validated transaction
        product_details: {
            name: product.name || 'Unknown Product',
            sku: product.sku || 'N/A',
            buying_price: product.buying_price || product.price || 0,
            selling_price: product.selling_price || product.price || 0,
            price: price, // Use the appropriate price based on transaction type
            unit_of_measure: product.unit_of_measure || 'Unit'
        }
    };
    
    return validatedTransaction;
}

// Get transaction by ID
async function getTransactionById(id) {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/stock-history/${id}/`, {
            method: 'GET',
            headers: {
                'Authorization': `Token ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Raw transaction API response:', data);
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
} 