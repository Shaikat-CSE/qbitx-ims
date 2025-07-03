// clients.js - Client management functionality for QBITX IMS Transform Suppliers

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Initialize client management page
        await initClientsPage();
    } catch (error) {
        console.error('Error initializing clients page:', error);
        showNotification('Error loading client data', 'danger');
    }
});

// Initialize client management page
async function initClientsPage() {
    // Load clients
    await loadClients();
    
    // Set up event listeners
    setupEventListeners();
}

// Load clients into the table
async function loadClients() {
    try {
        const clients = await getClients();
        const tableBody = document.querySelector('#clientsTable tbody');
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        // Add clients to table
        clients.forEach(client => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${client.name}</td>
                <td>${client.contact_person || '-'}</td>
                <td>${client.email || '-'}</td>
                <td>${client.phone || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-info view-client" data-id="${client.id}">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-primary edit-client" data-id="${client.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-client" data-id="${client.id}" data-name="${client.name}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // Initialize DataTable
        if ($.fn.DataTable.isDataTable('#clientsTable')) {
            $('#clientsTable').DataTable().destroy();
        }
        
        $('#clientsTable').DataTable({
            responsive: true,
            order: [[0, 'asc']]
        });
        
    } catch (error) {
        console.error('Error loading clients:', error);
        showNotification('Error loading clients', 'danger');
    }
}

// Set up event listeners
function setupEventListeners() {
    // Add/Edit client form submission
    document.getElementById('saveClientBtn').addEventListener('click', async function() {
        const form = document.getElementById('clientForm');
        
        // Form validation
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        // Get form values
        const clientId = document.getElementById('clientId').value;
        const clientData = {
            name: document.getElementById('clientName').value,
            contact_person: document.getElementById('contactPerson').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            address: document.getElementById('address').value,
            notes: document.getElementById('notes').value
        };
        
        try {
            if (clientId) {
                // Update existing client
                await updateClient(clientId, clientData);
                showNotification('Client updated successfully');
            } else {
                // Create new client
                await createClient(clientData);
                showNotification('Client added successfully');
            }
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addClientModal'));
            modal.hide();
            
            // Reload clients
            await loadClients();
            
        } catch (error) {
            console.error('Error saving client:', error);
            showNotification('Error saving client', 'danger');
        }
    });
    
    // View client details
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.view-client')) {
            const button = e.target.closest('.view-client');
            const clientId = button.getAttribute('data-id');
            await showClientDetails(clientId);
        }
    });
    
    // Close client details
    document.getElementById('closeClientDetails').addEventListener('click', function() {
        document.getElementById('clientDetailsSection').style.display = 'none';
    });
    
    // Edit client
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.edit-client')) {
            const button = e.target.closest('.edit-client');
            const clientId = button.getAttribute('data-id');
            await editClient(clientId);
        }
    });
    
    // Delete client
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-client')) {
            const button = e.target.closest('.delete-client');
            const clientId = button.getAttribute('data-id');
            const clientName = button.getAttribute('data-name');
            
            // Set client name in confirmation modal
            document.getElementById('deleteClientName').textContent = clientName;
            
            // Set client ID for delete confirmation
            document.getElementById('confirmDeleteBtn').setAttribute('data-id', clientId);
            
            // Show confirmation modal
            const modal = new bootstrap.Modal(document.getElementById('deleteClientModal'));
            modal.show();
        }
    });
    
    // Confirm delete
    document.getElementById('confirmDeleteBtn').addEventListener('click', async function() {
        const clientId = this.getAttribute('data-id');
        
        try {
            await deleteClient(clientId);
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteClientModal'));
            modal.hide();
            
            // Show success message
            showNotification('Client deleted successfully');
            
            // Reload clients
            await loadClients();
            
        } catch (error) {
            console.error('Error deleting client:', error);
            showNotification('Error deleting client', 'danger');
        }
    });
    
    // Reset form when modal is opened
    document.getElementById('addClientModal').addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        
        // Clear form
        document.getElementById('clientForm').reset();
        document.getElementById('clientForm').classList.remove('was-validated');
        document.getElementById('clientId').value = '';
        
        // Set modal title for new client
        document.getElementById('clientModalTitle').textContent = 'Add New Client';
    });
}

// Show client details
async function showClientDetails(clientId) {
    try {
        const client = await getClientById(clientId);
        
        // Set client details
        document.getElementById('clientDetailsName').textContent = client.name;
        document.getElementById('clientDetailsPerson').textContent = client.contact_person || '-';
        document.getElementById('clientDetailsEmail').textContent = client.email || '-';
        document.getElementById('clientDetailsPhone').textContent = client.phone || '-';
        document.getElementById('clientDetailsAddress').textContent = client.address || '-';
        document.getElementById('clientDetailsNotes').textContent = client.notes || '-';
        
        // Show client details section
        document.getElementById('clientDetailsSection').style.display = 'block';
        
        // Load client transactions
        await loadClientTransactions(clientId);
        
        // Load client products
        await loadClientProducts(clientId);
        
    } catch (error) {
        console.error('Error loading client details:', error);
        showNotification('Error loading client details', 'danger');
    }
}

// Load client transactions
async function loadClientTransactions(clientId) {
    try {
        const transactions = await getClientTransactions(clientId);
        const tableBody = document.getElementById('clientTransactionsTable');
        
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
        console.error('Error loading client transactions:', error);
        showNotification('Error loading client transactions', 'danger');
    }
}

// Load client products
async function loadClientProducts(clientId) {
    try {
        const products = await getClientProducts(clientId);
        const tableBody = document.getElementById('clientProductsTable');
        
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
                <td>${formatCurrency(product.selling_price)}</td>
                <td>${product.location || '-'}</td>
            `;
            tableBody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading client products:', error);
        showNotification('Error loading client products', 'danger');
    }
}

// Edit client
async function editClient(clientId) {
    try {
        const client = await getClientById(clientId);
        
        // Set form values
        document.getElementById('clientId').value = client.id;
        document.getElementById('clientName').value = client.name;
        document.getElementById('contactPerson').value = client.contact_person || '';
        document.getElementById('email').value = client.email || '';
        document.getElementById('phone').value = client.phone || '';
        document.getElementById('address').value = client.address || '';
        document.getElementById('notes').value = client.notes || '';
        
        // Set modal title
        document.getElementById('clientModalTitle').textContent = 'Edit Client';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('addClientModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading client for edit:', error);
        showNotification('Error loading client', 'danger');
    }
} 