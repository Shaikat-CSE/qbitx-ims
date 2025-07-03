// dashboard.js - Dashboard functionality for Golden Niche IMS

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Initialize dashboard
        await initDashboard();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showNotification('Error loading dashboard data', 'danger');
    }
});

// Initialize dashboard
async function initDashboard() {
    try {
        // Load inventory stats
        const stats = await getInventoryStats();
        
        // Update stats display
        document.getElementById('totalProducts').textContent = stats.total_products || 0;
        document.getElementById('inventoryValue').textContent = formatCurrency(stats.total_value || 0);
        document.getElementById('lowStockCount').textContent = stats.low_stock_count || 0;
        
        // Load low stock products
        await loadLowStockProducts();
        
        // Load recent transactions
        await loadRecentTransactions();
        
        // Load charts
        await loadCharts();
        
        // Set up event listeners
        setupEventListeners();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        throw error;
    }
}

// Load low stock products
async function loadLowStockProducts() {
    try {
        const lowStockProducts = await getLowStockProducts();
        const tableBody = document.getElementById('lowStockTable');
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        if (lowStockProducts.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No low stock products found.</td></tr>';
            return;
        }
        
        // Sort by quantity (lowest first)
        lowStockProducts.sort((a, b) => a.quantity - b.quantity);
        
        // Generate table rows
        lowStockProducts.forEach(product => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${product.name}</td>
                <td>${product.sku}</td>
                <td class="text-danger fw-bold">${product.quantity}</td>
                <td>${product.minimum_stock_level}</td>
                <td>${formatCurrency(product.price)}</td>
                <td>
                    <a href="stock.html?product=${product.id}" class="btn btn-warning btn-sm">
                        <i class="fas fa-plus-circle"></i> Restock
                    </a>
                </td>
            `;
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading low stock products:', error);
        throw error;
    }
}

// Load recent transactions
async function loadRecentTransactions() {
    try {
        const stockHistory = await getStockHistory();
        const tableBody = document.getElementById('recentTransactionsTable');
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        // Show only the 5 most recent transactions
        const recentTransactions = stockHistory.slice(0, 5);
        
        if (recentTransactions.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No recent transactions found.</td></tr>';
            return;
        }
        
        // Generate table rows
        recentTransactions.forEach(transaction => {
            const row = document.createElement('tr');
            
            // Format date
            const date = new Date(transaction.date);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'});
            
            // Determine transaction class and label
            const transactionClass = transaction.type === 'IN' ? 'text-success' : 'text-danger';
            const transactionLabel = transaction.type === 'IN' ? 'Stock In' : 'Stock Out';
            
            // Determine contact information
            const contactInfo = transaction.type === 'IN' 
                ? transaction.supplier || '-' 
                : transaction.client || '-';
            
            row.innerHTML = `
                <td>${formattedDate}</td>
                <td>${transaction.product_name}</td>
                <td><span class="${transactionClass}">${transactionLabel}</span></td>
                <td>${transaction.quantity}</td>
                <td>${contactInfo}</td>
                <td>${transaction.reference_number || '-'}</td>
            `;
            
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading recent transactions:', error);
        throw error;
    }
}

// Load charts
async function loadCharts() {
    try {
        const [products, stockHistory] = await Promise.all([
            getProducts(),
            getStockHistory()
        ]);
        
        // Create transactions chart
        createTransactionsChart(stockHistory);
        
        // Create category chart
        createCategoryChart(products);
    } catch (error) {
        console.error('Error loading chart data:', error);
        throw error;
    }
}

// Create stock transactions chart
function createTransactionsChart(stockHistory) {
    // Get dates for the last 7 days
    const dates = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
    }
    
    // Count stock in and stock out for each day
    const stockInData = Array(7).fill(0);
    const stockOutData = Array(7).fill(0);
    
    stockHistory.forEach(transaction => {
        const transactionDate = new Date(transaction.date).toISOString().split('T')[0];
        const dateIndex = dates.indexOf(transactionDate);
        
        if (dateIndex !== -1) {
            if (transaction.type === 'IN') {
                stockInData[dateIndex] += transaction.quantity;
            } else {
                stockOutData[dateIndex] += transaction.quantity;
            }
        }
    });
    
    // Format dates for display
    const formattedDates = dates.map(date => {
        const [year, month, day] = date.split('-');
        return `${day}/${month}`;
    });
    
    // Create chart
    const ctx = document.getElementById('stockTransactionsChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: formattedDates,
            datasets: [
                {
                    label: 'Stock In',
                    data: stockInData,
                    backgroundColor: 'rgba(40, 167, 69, 0.2)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 2,
                    tension: 0.1
                },
                {
                    label: 'Stock Out',
                    data: stockOutData,
                    backgroundColor: 'rgba(220, 53, 69, 0.2)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 2,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Quantity'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Stock Transactions (Last 7 Days)'
                }
            }
        }
    });
}

// Create category chart
function createCategoryChart(products) {
    // Group products by category
    const categories = {};
    const categoryColors = {
        'Fruits': '#FF6384',
        'Spice': '#36A2EB',
        'Home Decor': '#FFCE56',
        'Cookware': '#4BC0C0',
        'Bakery Ingredients': '#9966FF'
    };
    
    // Calculate total inventory value by category
    products.forEach(product => {
        const type = product.type;
        const value = product.quantity * product.price;
        
        if (!categories[type]) {
            categories[type] = 0;
        }
        
        categories[type] += value;
    });
    
    const categoryLabels = Object.keys(categories);
    const categoryValues = Object.values(categories);
    const backgroundColors = categoryLabels.map(label => categoryColors[label] || '#777777');
    
    // Create chart
    const ctx = document.getElementById('inventoryCategoryChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categoryLabels,
            datasets: [{
                data: categoryValues,
                backgroundColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return `${context.label}: ${formatCurrency(value)}`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Inventory Value by Category'
                }
            }
        }
    });
}

// Set up event listeners
function setupEventListeners() {
    // Show low stock products
    document.getElementById('showLowStockBtn').addEventListener('click', function() {
        const lowStockCard = document.getElementById('lowStockCard');
        
        if (lowStockCard.style.display === 'none') {
            lowStockCard.style.display = 'block';
            this.innerHTML = 'Hide low stock products <i class="fas fa-arrow-up"></i>';
        } else {
            lowStockCard.style.display = 'none';
            this.innerHTML = 'View low stock products <i class="fas fa-arrow-right"></i>';
        }
    });
    
    // Refresh dashboard
    document.getElementById('refreshDashboardBtn').addEventListener('click', async function() {
        try {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            
            // Re-initialize dashboard
            await initDashboard();
            
            showNotification('Dashboard refreshed successfully');
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            showNotification('Error refreshing dashboard', 'danger');
        } finally {
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        }
    });
} 