// auth.js - Authentication functionality for QBITX IMS Transform Suppliers

document.addEventListener('DOMContentLoaded', function() {
    // For demo purposes, we'll use a simple localStorage-based auth
    // In a real implementation, this would use JWT tokens or session auth with Django
    
    // Initialize authentication state
    if (!localStorage.getItem('isAuthenticated')) {
        localStorage.setItem('isAuthenticated', 'false');
    } else {
        // Redirect to dashboard if already authenticated
        if (localStorage.getItem('isAuthenticated') === 'true' && window.location.pathname.includes('index.html')) {
            window.location.href = 'dashboard.html';
        }
    }

    // Login form validation and submission
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Get form values
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();
            
            // Reset error messages
            document.getElementById('emailError').textContent = '';
            document.getElementById('passwordError').textContent = '';
            
            // Validate form
            let isValid = true;
            
            if (!email) {
                document.getElementById('emailError').textContent = 'Email or username is required';
                isValid = false;
            } else if (email.includes('@')) {
                if (!isValidEmail(email)) {
                    document.getElementById('emailError').textContent = 'Please enter a valid email address';
                    isValid = false;
                }
            } // No username length check for username-only login
            
            if (!password) {
                document.getElementById('passwordError').textContent = 'Password is required';
                isValid = false;
            }
            
            if (isValid) {
                // Show loading indicator
                const submitBtn = loginForm.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
                submitBtn.disabled = true;
                
                // Authenticate with Django DRF token endpoint
                fetch(`${API_CONFIG.BASE_URL.replace(/\/$/, '')}/../api-token-auth/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username: email, password: password })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.token) {
                        // Store token and user info
                        localStorage.setItem('authToken', data.token);
                        localStorage.setItem('auth_token', data.token); // Also save as auth_token for compatibility
                        localStorage.setItem('isAuthenticated', 'true');
                        localStorage.setItem('currentUser', JSON.stringify({
                            email: email,
                            name: email // You can update this if your API returns user info
                        }));
                        
                        // Fetch user permissions after login
                        return fetchUserPermissions(data.token).then(() => {
                        window.location.href = 'dashboard.html';
                        });
                    } else {
                        // Reset button
                        submitBtn.innerHTML = originalBtnText;
                        submitBtn.disabled = false;
                        
                        // Show login error
                        alert('Invalid email or password. Please try again.');
                    }
                })
                .catch(() => {
                    // Reset button
                    submitBtn.innerHTML = originalBtnText;
                    submitBtn.disabled = false;
                    
                    alert('Login failed. Please try again.');
                });
            }
        });
    }
    
    // Apply permission-based UI adjustments when page loads
    if (localStorage.getItem('isAuthenticated') === 'true') {
        applyPermissionBasedUI();
    }

    // Set user name in header if authenticated
    if (localStorage.getItem('isAuthenticated') === 'true') {
        const userString = localStorage.getItem('currentUser');
        if (userString) {
            try {
                const user = JSON.parse(userString);
                const name = user.name || user.email || '';
                const nameSpan = document.getElementById('currentUserName');
                if (nameSpan) {
                    nameSpan.textContent = name;
                }
            } catch (e) {
                // Ignore JSON parse errors
            }
        }
    }
});

// Check if user is authenticated, redirect to login if not
function checkAuth() {
    if (localStorage.getItem('isAuthenticated') !== 'true' && 
        !window.location.pathname.includes('index.html')) {
        window.location.href = 'index.html';
        return false;
    }
    
    // Check page-specific permissions
    checkPagePermissions();
    return true;
}

// Check if user has permission to access the current page
function checkPagePermissions() {
    const currentPath = window.location.pathname;
    
    // Skip permission check for dashboard and login page
    if (currentPath.includes('dashboard.html') || currentPath.includes('index.html')) {
        return true;
    }
    
    let hasAccess = true;
    let requiredPermission = null;
    
    // Determine required permission based on page
    if (currentPath.includes('products.html') || currentPath.includes('product-form.html')) {
        requiredPermission = 'inventory.view_product';
        hasAccess = canViewProduct();
    } else if (currentPath.includes('stock.html')) {
        requiredPermission = 'inventory.view_stocktransaction';
        hasAccess = canViewStock();
    } else if (currentPath.includes('suppliers.html')) {
        requiredPermission = 'inventory.view_supplier';
        hasAccess = canViewSupplier();
    } else if (currentPath.includes('clients.html')) {
        requiredPermission = 'inventory.view_client';
        hasAccess = canViewClient();
    } else if (currentPath.includes('reports.html')) {
        // Use our custom report permission
        requiredPermission = 'inventory.view_reports';
        hasAccess = canViewReports();
    }
    
    // Check permission and redirect if necessary
    if (requiredPermission && !hasAccess) {
        // Redirect to dashboard with unauthorized message
        sessionStorage.setItem('permissionDenied', 'You do not have permission to access that page.');
        window.location.href = 'dashboard.html';
        return false;
    }
    
    return true;
}

// Handle logout
function logout() {
    localStorage.setItem('isAuthenticated', 'false');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('authToken');
    localStorage.removeItem('auth_token'); // Also remove auth_token
    localStorage.removeItem('userPermissions');
    window.location.href = 'index.html';
}

// Email validation helper
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}

// Returns the user's DRF token from localStorage, or an empty string if not set
function getAuthToken() {
    return localStorage.getItem('authToken') || '';
}

// Add logout event listener to any logout button
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Check authentication for pages other than login
    if (!window.location.pathname.includes('index.html')) {
        checkAuth();
        
        // Check for permission denied message
        const permissionDenied = sessionStorage.getItem('permissionDenied');
        if (permissionDenied) {
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger mt-3';
            errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${permissionDenied}`;
            
            // Insert after header or at the top of main content
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.insertBefore(errorDiv, mainContent.firstChild);
            }
            
            // Clear the message
            sessionStorage.removeItem('permissionDenied');
        }
    }
});

// Fetch user permissions from the server
async function fetchUserPermissions(token) {
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/user-permissions/`, {
            headers: {
                'Authorization': `Token ${token}`
            }
        });
        
        if (response.ok) {
            const permissions = await response.json();
            localStorage.setItem('userPermissions', JSON.stringify(permissions));
            return permissions;
        } else {
            console.error('Failed to fetch user permissions');
            return [];
        }
    } catch (error) {
        console.error('Error fetching user permissions:', error);
        return [];
    }
}

// Check if user has a specific permission
function hasPermission(permissionCode) {
    try {
        const permissionsString = localStorage.getItem('userPermissions');
        if (!permissionsString) {
            console.log(`No permissions found in localStorage`);
            return false;
        }
        
        const permissions = JSON.parse(permissionsString);
        const hasPermission = permissions.includes(permissionCode);
        console.log(`Checking permission: ${permissionCode}, Result: ${hasPermission}`);
        return hasPermission;
    } catch (error) {
        console.error('Error checking permission:', error);
        return false;
    }
}

// Convenience permission check functions
const canAddProduct = () => hasPermission('inventory.add_product');
const canChangeProduct = () => hasPermission('inventory.change_product');
const canDeleteProduct = () => hasPermission('inventory.delete_product');
const canViewProduct = () => hasPermission('inventory.view_product');

const canAddStock = () => hasPermission('inventory.add_stocktransaction');
const canChangeStock = () => hasPermission('inventory.change_stocktransaction');
const canDeleteStock = () => hasPermission('inventory.delete_stocktransaction');
const canViewStock = () => hasPermission('inventory.view_stocktransaction');

const canAddSupplier = () => hasPermission('inventory.add_supplier');
const canChangeSupplier = () => hasPermission('inventory.change_supplier');
const canDeleteSupplier = () => hasPermission('inventory.delete_supplier');
const canViewSupplier = () => hasPermission('inventory.view_supplier');

const canAddClient = () => hasPermission('inventory.add_client');
const canChangeClient = () => hasPermission('inventory.change_client');
const canDeleteClient = () => hasPermission('inventory.delete_client');
const canViewClient = () => hasPermission('inventory.view_client');

// Report-specific permission checks
const canViewReports = () => {
    const result = hasPermission('inventory.view_reports') || hasPermission('inventory.view_stocktransaction');
    console.log(`canViewReports check result: ${result}`);
    return result;
};
const canExportReports = () => hasPermission('inventory.export_reports');
const canPrintReports = () => hasPermission('inventory.print_reports');

// Apply UI adjustments based on permissions
function applyPermissionBasedUI() {
    // Set permissions CSS classes on body
    document.body.classList.toggle('can-add-product', canAddProduct());
    document.body.classList.toggle('can-change-product', canChangeProduct());
    document.body.classList.toggle('can-delete-product', canDeleteProduct());
    document.body.classList.toggle('can-view-product', canViewProduct());
    
    document.body.classList.toggle('can-add-stock', canAddStock());
    document.body.classList.toggle('can-change-stock', canChangeStock());
    document.body.classList.toggle('can-delete-stock', canDeleteStock());
    document.body.classList.toggle('can-view-stock', canViewStock());
    
    document.body.classList.toggle('can-add-supplier', canAddSupplier());
    document.body.classList.toggle('can-change-supplier', canChangeSupplier());
    document.body.classList.toggle('can-delete-supplier', canDeleteSupplier());
    document.body.classList.toggle('can-view-supplier', canViewSupplier());
    
    document.body.classList.toggle('can-add-client', canAddClient());
    document.body.classList.toggle('can-change-client', canChangeClient());
    document.body.classList.toggle('can-delete-client', canDeleteClient());
    document.body.classList.toggle('can-view-client', canViewClient());
    
    // Report permissions
    document.body.classList.toggle('can-view-reports', canViewReports());
    document.body.classList.toggle('can-export-reports', canExportReports());
    document.body.classList.toggle('can-print-reports', canPrintReports());
    
    // Apply permission checks to navigation links
    applyNavigationPermissions();
    
    // Apply to specific UI elements
    applyProductPermissionsUI();
    applyStockPermissionsUI();
    applySupplierPermissionsUI();
    applyClientPermissionsUI();
    applyReportPermissionsUI();
}

// Check and apply permissions to navigation links
function applyNavigationPermissions() {
    console.log('Applying navigation permissions...');
    
    // Find all navigation links with data-requires-permission attribute
    const navLinks = document.querySelectorAll('a[data-requires-permission]');
    console.log(`Found ${navLinks.length} navigation links with data-requires-permission attribute`);
    
    navLinks.forEach(link => {
        const requiredPermission = link.getAttribute('data-requires-permission');
        const href = link.getAttribute('href');
        console.log(`Processing link: ${href}, requires permission: ${requiredPermission}`);
        
        let hasAccess = false;
        
        // Special handling for reports link
        if (requiredPermission === 'inventory.view_reports') {
            hasAccess = canViewReports();
            console.log(`Reports link access: ${hasAccess}`);
        } else {
            hasAccess = hasPermission(requiredPermission);
        }
        
        // Get the lock icon element
        const lockIcon = link.querySelector('.permission-lock-icon');
        
        if (!hasAccess) {
            console.log(`Access denied for ${href}, adding disabled class`);
            
            // Add disabled class to the link
            link.classList.add('disabled');
            
            // Show the lock icon
            if (lockIcon) {
                lockIcon.style.display = 'inline-block';
                console.log('Lock icon is displayed');
            } else {
                console.log('Lock icon element not found');
            }
            
            // Set appropriate title based on the permission
            if (requiredPermission === 'inventory.view_reports') {
                link.setAttribute('title', 'You do not have permission to access reports');
            } else {
                link.setAttribute('title', 'You do not have permission to access this section');
            }
            
            // Prevent default navigation
            link.addEventListener('click', function(e) {
                e.preventDefault();
                return false;
            });
        } else {
            console.log(`Access granted for ${href}, removing disabled class`);
            
            // Remove disabled class from the link
            link.classList.remove('disabled');
            
            // Hide the lock icon
            if (lockIcon) {
                lockIcon.style.display = 'none';
                console.log('Lock icon is hidden');
            }
            
            link.removeAttribute('title');
        }
    });
}

// Apply permissions to product-related UI elements
function applyProductPermissionsUI() {
    // Add product buttons
    const addProductBtns = document.querySelectorAll('.add-product-btn, [data-action="add-product"]');
    addProductBtns.forEach(btn => {
        if (!canAddProduct()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to add products');
        }
    });
    
    // Edit product buttons
    const editProductBtns = document.querySelectorAll('.edit-product-btn, [data-action="edit-product"]');
    editProductBtns.forEach(btn => {
        if (!canChangeProduct()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to edit products');
        }
    });
    
    // Delete product buttons
    const deleteProductBtns = document.querySelectorAll('.delete-product-btn, [data-action="delete-product"]');
    deleteProductBtns.forEach(btn => {
        if (!canDeleteProduct()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to delete products');
        }
    });
}

// Apply permissions to stock-related UI elements
function applyStockPermissionsUI() {
    // Stock form
    const stockForm = document.getElementById('stockForm');
    if (stockForm && !canAddStock()) {
        const inputs = stockForm.querySelectorAll('input, select, textarea, button[type="submit"]');
        inputs.forEach(input => {
            input.classList.add('disabled');
            input.setAttribute('disabled', 'disabled');
        });
        
        // Add a message about permissions
        const formMessage = document.createElement('div');
        formMessage.className = 'alert alert-warning mt-3';
        formMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> You do not have permission to add stock transactions.';
        stockForm.prepend(formMessage);
    }
}

// Apply permissions to supplier-related UI elements
function applySupplierPermissionsUI() {
    // Add supplier buttons
    const addSupplierBtns = document.querySelectorAll('.add-supplier-btn, [data-action="add-supplier"]');
    addSupplierBtns.forEach(btn => {
        if (!canAddSupplier()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to add suppliers');
        }
    });
    
    // Edit supplier buttons
    const editSupplierBtns = document.querySelectorAll('.edit-supplier-btn, [data-action="edit-supplier"]');
    editSupplierBtns.forEach(btn => {
        if (!canChangeSupplier()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to edit suppliers');
        }
    });
    
    // Delete supplier buttons
    const deleteSupplierBtns = document.querySelectorAll('.delete-supplier-btn, [data-action="delete-supplier"]');
    deleteSupplierBtns.forEach(btn => {
        if (!canDeleteSupplier()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to delete suppliers');
        }
    });
}

// Apply permissions to client-related UI elements
function applyClientPermissionsUI() {
    // Add client buttons
    const addClientBtns = document.querySelectorAll('.add-client-btn, [data-action="add-client"]');
    addClientBtns.forEach(btn => {
        if (!canAddClient()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to add clients');
        }
    });
    
    // Edit client buttons
    const editClientBtns = document.querySelectorAll('.edit-client-btn, [data-action="edit-client"]');
    editClientBtns.forEach(btn => {
        if (!canChangeClient()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to edit clients');
        }
    });
    
    // Delete client buttons
    const deleteClientBtns = document.querySelectorAll('.delete-client-btn, [data-action="delete-client"]');
    deleteClientBtns.forEach(btn => {
        if (!canDeleteClient()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to delete clients');
        }
    });
}

// Apply permissions to report-related UI elements
function applyReportPermissionsUI() {
    // Add report buttons
    const reportBtns = document.querySelectorAll('.report-btn, [data-action="view-report"]');
    reportBtns.forEach(btn => {
        if (!canViewReports()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to view reports');
        }
    });
    
    // Export report buttons
    const exportReportBtns = document.querySelectorAll('.export-report-btn, [data-requires-permission="inventory.export_reports"]');
    exportReportBtns.forEach(btn => {
        const lockIcon = btn.querySelector('.permission-lock-icon');
        if (!canExportReports()) {
            btn.classList.add('disabled');
            btn.setAttribute('disabled', 'disabled');
            btn.setAttribute('title', 'You do not have permission to export reports');
            if (lockIcon) {
                lockIcon.style.display = 'inline-block';
            }
        } else {
            btn.classList.remove('disabled');
            btn.removeAttribute('disabled');
            btn.removeAttribute('title');
            if (lockIcon) {
                lockIcon.style.display = 'none';
            }
        }
    });
}