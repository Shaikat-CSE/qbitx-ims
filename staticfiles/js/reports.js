// reports.js - Reports functionality for Golden Niche IMS

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Initialize reports page
        await initReportsPage();
    } catch (error) {
        console.error('Error initializing reports page:', error);
        showNotification('Error loading reports data', 'danger');
    }
});

// Initialize reports page
async function initReportsPage() {
    try {
        // Load summary stats
        await loadSummaryStats();
        
        // Load products and stock history data
        const [products, stockHistory] = await Promise.all([
            getProducts(),
            getStockHistory()
        ]);
        
        // Load charts
        createTransactionsChart(stockHistory);
        createCategoryChart(products);
        
        // Load stock history table
        loadStockHistoryTable(stockHistory, products);
        
        // Set up event listeners for export and print
        setupEventListeners();
    } catch (error) {
        console.error('Error loading reports data:', error);
        throw error;
    }
}

// Load summary stats
async function loadSummaryStats() {
    try {
        const stats = await getInventoryStats();
        
        // Update UI with stats
        document.getElementById('totalProducts').textContent = stats.total_products || 0;
        document.getElementById('inventoryValue').textContent = formatCurrency(stats.total_value || 0);
        document.getElementById('lowStock').textContent = stats.low_stock_count || 0;
    } catch (error) {
        console.error('Error loading summary stats:', error);
        throw error;
    }
}

// Create transactions chart (last 30 days)
function createTransactionsChart(stockHistory) {
    // Get dates for the last 30 days
    const dates = [];
    const today = new Date();
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
    }
    
    // Count stock in and stock out for each day
    const stockInData = Array(30).fill(0);
    const stockOutData = Array(30).fill(0);
    
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
        return `${month}/${day}`;
    });
    
    // Create chart
    const ctx = document.getElementById('transactionsChart').getContext('2d');
    
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
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date (MM/DD)'
                    }
                }
            }
        }
    });
}

// Create category chart
function createCategoryChart(products) {
    // Group products by category and calculate total value
    const categories = {};
    
    products.forEach(product => {
        const type = product.type;
        const value = product.quantity * product.price;
        
        if (!categories[type]) {
            categories[type] = 0;
        }
        
        categories[type] += value;
    });
    
    // Prepare data for chart
    const categoryLabels = Object.keys(categories);
    const categoryValues = Object.values(categories);
    
    // Create chart
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categoryLabels,
            datasets: [{
                data: categoryValues,
                backgroundColor: [
                    '#FFC107',
                    '#FF9800',
                    '#FF5722',
                    '#E91E63',
                    '#9C27B0',
                    '#673AB7'
                ],
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
                }
            }
        }
    });
}

// Load stock history table
function loadStockHistoryTable(stockHistory, products) {
    const tableBody = document.getElementById('stockHistoryTable');
    
    // Create a map of product IDs to products for quick lookup
    const productsMap = {};
    products.forEach(product => {
        productsMap[product.id] = product;
    });
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Sort transactions by date (newest first)
    const sortedHistory = [...stockHistory].sort((a, b) => 
        new Date(b.date) - new Date(a.date)
    );
    
    // Generate table rows
    sortedHistory.forEach(transaction => {
        const row = document.createElement('tr');
        
        // Format date
        const date = new Date(transaction.date);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'});
        
        // Get product info
        const product = productsMap[transaction.product];
        const sku = product ? product.sku : 'N/A';
        
        // Determine transaction class and label
        const transactionClass = transaction.type === 'IN' ? 'text-success' : 'text-danger';
        const transactionLabel = transaction.type === 'IN' ? 'Stock In' : 'Stock Out';
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td>${transaction.product_name}</td>
            <td>${sku}</td>
            <td><span class="${transactionClass}">${transactionLabel}</span></td>
            <td>${transaction.quantity}</td>
            <td>${transaction.notes || '-'}</td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Show message if no history
    if (sortedHistory.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No stock transactions found</td></tr>';
    }
}

// Set up event listeners
function setupEventListeners() {
    // Print report
    document.getElementById('printReportBtn').addEventListener('click', function() {
        window.print();
    });
    
    // Export as CSV
    document.getElementById('exportReportBtn').addEventListener('click', function() {
        exportTableToCSV('transactions.csv');
    });
}

// Export table to CSV
function exportTableToCSV(filename) {
    const table = document.getElementById('transactionsTable');
    let csv = [];
    
    // Get all rows
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Get text content and clean it
            let text = cols[j].textContent.trim();
            
            // If it contains a comma, quote it
            if (text.includes(',')) {
                text = '"' + text + '"';
            }
            
            row.push(text);
        }
        
        csv.push(row.join(','));
    }
    
    // Create CSV file
    const csvContent = 'data:text/csv;charset=utf-8,' + csv.join('\n');
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    
    // Trigger download
    link.click();
    
    // Clean up
    document.body.removeChild(link);
} 