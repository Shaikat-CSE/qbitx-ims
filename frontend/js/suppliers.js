// suppliers.js - Supplier management functionality for QBITX IMS Transform Suppliers

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Initialize supplier management page
        await initSuppliersPage();
    } catch (error) {
        console.error('Error initializing suppliers page:', error);
        showNotification('Error loading supplier data', 'danger');
    }
});

// Initialize supplier management page
async function initSuppliersPage() {
    // Load suppliers
    await loadSuppliers();
    
    // Set up event listeners
    setupEventListeners();
}

// Load suppliers into the table
async function loadSuppliers() {
    try {
        const suppliers = await getSuppliers();
        const tableBody = document.querySelector('#suppliersTable tbody');
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        // Add suppliers to table
        suppliers.forEach(supplier => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${supplier.name}</td>
                <td>${supplier.contact_person || '-'}</td>
                <td>${supplier.email || '-'}</td>
                <td>${supplier.phone || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-info view-supplier" data-id="${supplier.id}">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-primary edit-supplier" data-id="${supplier.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-supplier" data-id="${supplier.id}" data-name="${supplier.name}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // Initialize DataTable
        if ($.fn.DataTable.isDataTable('#suppliersTable')) {
            $('#suppliersTable').DataTable().destroy();
        }
        
        $('#suppliersTable').DataTable({
            responsive: true,
            order: [[0, 'asc']]
        });
        
    } catch (error) {
        console.error('Error loading suppliers:', error);
        showNotification('Error loading suppliers', 'danger');
    }
}

// Set up event listeners
function setupEventListeners() {
    // Add/Edit supplier form submission
    document.getElementById('saveSupplierBtn').addEventListener('click', async function() {
        const form = document.getElementById('supplierForm');
        
        // Form validation
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        // Get form values
        const supplierId = document.getElementById('supplierId').value;
        const supplierData = {
            name: document.getElementById('supplierName').value,
            contact_person: document.getElementById('contactPerson').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            address: document.getElementById('address').value,
            notes: document.getElementById('notes').value
        };
        
        try {
            if (supplierId) {
                // Update existing supplier
                await updateSupplier(supplierId, supplierData);
                showNotification('Supplier updated successfully');
            } else {
                // Create new supplier
                await createSupplier(supplierData);
                showNotification('Supplier added successfully');
            }
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addSupplierModal'));
            modal.hide();
            
            // Reload suppliers
            await loadSuppliers();
            
        } catch (error) {
            console.error('Error saving supplier:', error);
            showNotification('Error saving supplier', 'danger');
        }
    });
    
    // View supplier details
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.view-supplier')) {
            const button = e.target.closest('.view-supplier');
            const supplierId = button.getAttribute('data-id');
            await showSupplierDetails(supplierId);
        }
    });
    
    // Close supplier details
    document.getElementById('closeSupplierDetails').addEventListener('click', function() {
        document.getElementById('supplierDetailsSection').style.display = 'none';
    });
    
    // Edit supplier
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.edit-supplier')) {
            const button = e.target.closest('.edit-supplier');
            const supplierId = button.getAttribute('data-id');
            await editSupplier(supplierId);
        }
    });
    
    // Delete supplier
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-supplier')) {
            const button = e.target.closest('.delete-supplier');
            const supplierId = button.getAttribute('data-id');
            const supplierName = button.getAttribute('data-name');
            
            // Set supplier name in confirmation modal
            document.getElementById('deleteSupplierName').textContent = supplierName;
            
            // Set supplier ID for delete confirmation
            document.getElementById('confirmDeleteBtn').setAttribute('data-id', supplierId);
            
            // Show confirmation modal
            const modal = new bootstrap.Modal(document.getElementById('deleteSupplierModal'));
            modal.show();
        }
    });
    
    // Confirm delete
    document.getElementById('confirmDeleteBtn').addEventListener('click', async function() {
        const supplierId = this.getAttribute('data-id');
        
        try {
            await deleteSupplier(supplierId);
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteSupplierModal'));
            modal.hide();
            
            // Show success message
            showNotification('Supplier deleted successfully');
            
            // Reload suppliers
            await loadSuppliers();
            
        } catch (error) {
            console.error('Error deleting supplier:', error);
            showNotification('Error deleting supplier', 'danger');
        }
    });
    
    // Reset form when modal is opened
    document.getElementById('addSupplierModal').addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        
        // Clear form
        document.getElementById('supplierForm').reset();
        document.getElementById('supplierForm').classList.remove('was-validated');
        document.getElementById('supplierId').value = '';
        
        // Set modal title for new supplier
        document.getElementById('supplierModalTitle').textContent = 'Add New Supplier';
    });
}

// Show supplier details
async function showSupplierDetails(supplierId) {
    try {
        const supplier = await getSupplierById(supplierId);
        
        // Set supplier details
        document.getElementById('supplierDetailsName').textContent = supplier.name;
        document.getElementById('supplierDetailsPerson').textContent = supplier.contact_person || '-';
        document.getElementById('supplierDetailsEmail').textContent = supplier.email || '-';
        document.getElementById('supplierDetailsPhone').textContent = supplier.phone || '-';
        document.getElementById('supplierDetailsAddress').textContent = supplier.address || '-';
        document.getElementById('supplierDetailsNotes').textContent = supplier.notes || '-';
        
        // Show supplier details section
        document.getElementById('supplierDetailsSection').style.display = 'block';
        
        // Load supplier transactions
        await loadSupplierTransactions(supplierId);
        
        // Load supplier products
        await loadSupplierProducts(supplierId);
        
    } catch (error) {
        console.error('Error loading supplier details:', error);
        showNotification('Error loading supplier details', 'danger');
    }
}

// Load supplier transactions
async function loadSupplierTransactions(supplierId) {
    try {
        const transactions = await getSupplierTransactions(supplierId);
        const tableBody = document.getElementById('supplierTransactionsTable');
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        if (transactions.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No transactions found</td></tr>';
            return;
        }
        
        // Add transactions to table
        transactions.forEach(transaction => {
            const date = new Date(transaction.date);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'});
            const total = transaction.unit_price ? transaction.unit_price * transaction.quantity : '-';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${formattedDate}</td>
                <td>${transaction.product_name}</td>
                <td>${transaction.quantity}</td>
                <td>${transaction.unit_price ? formatCurrency(transaction.unit_price) : '-'}</td>
                <td>${total !== '-' ? formatCurrency(total) : '-'}</td>
                <td>${transaction.reference_number || '-'}</td>
            `;
            tableBody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading supplier transactions:', error);
        showNotification('Error loading supplier transactions', 'danger');
    }
}

// Load supplier products
async function loadSupplierProducts(supplierId) {
    try {
        const products = await getSupplierProducts(supplierId);
        const tableBody = document.getElementById('supplierProductsTable');
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        if (products.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No products found</td></tr>';
            return;
        }
        
        // Add products to table
        products.forEach(product => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${product.name}</td>
                <td>${product.sku}</td>
                <td>${product.type}</td>
                <td>${product.quantity}</td>
                <td>${formatCurrency(product.buying_price)}</td>
                <td>${product.location || '-'}</td>
            `;
            tableBody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading supplier products:', error);
        showNotification('Error loading supplier products', 'danger');
    }
}

// Edit supplier
async function editSupplier(supplierId) {
    try {
        const supplier = await getSupplierById(supplierId);
        
        // Set form values
        document.getElementById('supplierId').value = supplier.id;
        document.getElementById('supplierName').value = supplier.name;
        document.getElementById('contactPerson').value = supplier.contact_person || '';
        document.getElementById('email').value = supplier.email || '';
        document.getElementById('phone').value = supplier.phone || '';
        document.getElementById('address').value = supplier.address || '';
        document.getElementById('notes').value = supplier.notes || '';
        
        // Set modal title
        document.getElementById('supplierModalTitle').textContent = 'Edit Supplier';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('addSupplierModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading supplier for edit:', error);
        showNotification('Error loading supplier', 'danger');
    }
} 