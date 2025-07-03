// dashboard.js - Dashboard functionality for QBITX IMS Transform Suppliers

// Register Chart.js DataLabels plugin
Chart.register(ChartDataLabels);

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
        // Format current date
        const today = new Date();
        document.getElementById('currentDate').textContent = today.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        // Format short date for cards
        const shortDate = today.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        // Set the short date on all cards
        document.querySelectorAll('[id^="currentDateShort"]').forEach(el => {
            el.textContent = shortDate;
        });
        
        // Load inventory stats from the database
        try {
            const stats = await getInventoryStats();
            console.log('Fetched inventory stats:', stats);
            
            // Update stats display with actual data
            document.getElementById('totalProducts').textContent = stats.total_products || 0;
            
            // Format and display inventory value (BDT)
            const inventoryValue = stats.total_value || 0;
            document.getElementById('inventoryValue').textContent = formatCurrency(inventoryValue);
            
            // Display low stock items count
            document.getElementById('lowStockCount').textContent = stats.low_stock_count || 0;
            
            // Fetch all transactions and sum wastage for the last tile
            let totalWastage = 0;
            try {
                const transactions = await getStockHistory();
                totalWastage = transactions.reduce((sum, t) => {
                    let w = 0;
                    if (typeof t.wastage === 'number' && !isNaN(t.wastage)) {
                        w = t.wastage;
                    } else if (typeof t.wastage === 'string' && t.wastage.trim() !== '' && !isNaN(parseFloat(t.wastage))) {
                        w = parseFloat(t.wastage);
                    } else if (typeof t.wastage_amount === 'number' && !isNaN(t.wastage_amount)) {
                        w = t.wastage_amount;
                    } else if (typeof t.wastage_amount === 'string' && t.wastage_amount.trim() !== '' && !isNaN(parseFloat(t.wastage_amount))) {
                        w = parseFloat(t.wastage_amount);
                    }
                    return sum + w;
                }, 0);
            } catch (err) {
                console.error('Error fetching transactions for wastage:', err);
            }
            document.getElementById('totalWastage').textContent = formatCurrency(totalWastage);
            
            // Add event listener for wastage details button
            const wastageBtn = document.getElementById('viewWastageBtn');
            if (wastageBtn) {
                wastageBtn.addEventListener('click', () => {
                    window.location.href = 'reports.html?filter=wastage';
                });
            }
        } catch (error) {
            console.error('Error fetching inventory stats:', error);
            showNotification('Failed to load inventory statistics from the database', 'danger');
            
            // Fallback to default values if API fails
            document.getElementById('totalProducts').textContent = "N/A";
            document.getElementById('inventoryValue').textContent = "N/A";
            document.getElementById('lowStockCount').textContent = "N/A";
            document.getElementById('totalWastage').textContent = "N/A";
        }
        
        // Load top products
        await loadTopProducts();
        
        // Load charts
        await loadCharts();
        
        // Set up event listeners
        setupEventListeners();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        throw error;
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-BD', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Load top products
async function loadTopProducts() {
    try {
        const products = await getProducts();
        const tableBody = document.getElementById('topProductsTable');
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        if (products.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center">No products found.</td></tr>';
            return;
        }
        
        // Sort by quantity (highest first)
        const sortedProducts = [...products].sort((a, b) => b.quantity - a.quantity);
        
        // Take top 10 by default
        const topProducts = sortedProducts.slice(0, 10);
        
        // Generate table rows
        topProducts.forEach(product => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${product.name}</td>
                <td>${product.unit_of_measure || 'KG'}</td>
                <td>${product.quantity}</td>
            `;
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading top products:', error);
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
        
        // Create top products by value chart
        createTopProductsValueChart(products);
        
        // Create category pie chart
        createCategoryPieChart(products);
        
        // Create sales trend chart
        createSalesTrendChart(stockHistory);
    } catch (error) {
        console.error('Error loading chart data:', error);
        throw error;
    }
}

// Create top products by value chart
function createTopProductsValueChart(products) {
    const ctx = document.getElementById('topProductsValueChart').getContext('2d');
    
    // Calculate value of each product (quantity * buying_price)
    const productsWithValue = products.map(product => ({
        name: product.name,
        value: (product.quantity || 0) * (product.buying_price || 0),
        buyingPrice: product.buying_price || 0,
        sellingPrice: product.selling_price || 0,
        quantity: product.quantity || 0
    }));
    
    // Sort by value and get top 5
    const topProducts = productsWithValue
        .sort((a, b) => b.value - a.value)
        .slice(0, 5);
    
    // Prepare data for chart
    const labels = topProducts.map(product => {
        // Truncate long names
        return product.name.length > 20 ? product.name.substring(0, 20) + '...' : product.name;
    });
    const data = topProducts.map(product => product.value);
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(78, 115, 223, 0.8)');
    gradient.addColorStop(1, 'rgba(78, 115, 223, 0.2)');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Inventory Value',
                data: data,
                backgroundColor: gradient,
                borderColor: '#4e73df',
                borderWidth: 1,
                borderRadius: 5,
                maxBarThickness: 50
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1.6,  // Adjust the aspect ratio
            indexAxis: 'y',  // Horizontal bar chart
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    padding: 10,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        title: function(context) {
                            return topProducts[context[0].dataIndex].name; // Use full product name
                        },
                        label: function(context) {
                            const index = context.dataIndex;
                            const product = topProducts[index];
                            return [
                                `Value: ${formatCurrency(product.value)}`,
                                `Buying Price: ${formatCurrency(product.buyingPrice)}`,
                                `Selling Price: ${formatCurrency(product.sellingPrice)}`,
                                `Quantity: ${product.quantity}`
                            ];
                        }
                    }
                },
                datalabels: {
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 11
                    },
                    formatter: function(value, context) {
                        return formatCurrency(value);
                    },
                    anchor: 'end',
                    align: 'end',
                    offset: -5
                }
            },
            scales: {
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 1000) {
                                return (value / 1000).toFixed(0) + 'K';
                            }
                            return value;
                        },
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

// Create category pie chart
function createCategoryPieChart(products) {
    const ctx = document.getElementById('categoryPieChart').getContext('2d');
    
    // Group products by category
    const categories = {};
    let totalValue = 0;
    
    products.forEach(product => {
        const type = product.type;
        const value = (product.quantity || 0) * (product.buying_price || 0);
        totalValue += value;
        
        if (!categories[type]) {
            categories[type] = {
                value: 0,
                count: 0
            };
        }
        
        categories[type].value += value;
        categories[type].count += 1;
    });
    
    // Prepare data for chart
    const labels = Object.keys(categories);
    const data = labels.map(label => categories[label].value);
    
    // Create color palette
    const colorPalette = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#6f42c1',
        '#5a5c69', '#858796', '#f8f9fc', '#d1d3e2', '#2e59d9', '#17a673'
    ];
    
    // Create chart
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colorPalette.slice(0, labels.length),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1.2,
            layout: {
                padding: 20
            },
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 15,
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const percentage = ((value / totalValue) * 100).toFixed(1);
                            const count = categories[label].count;
                            
                            return [
                                `${label}: ${formatCurrency(value)}`,
                                `${percentage}% of inventory value`,
                                `${count} product${count !== 1 ? 's' : ''}`
                            ];
                        }
                    }
                },
                datalabels: {
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 11
                    },
                    formatter: function(value, context) {
                        const percentage = Math.round((value / totalValue) * 100);
                        return percentage >= 5 ? `${percentage}%` : '';
                    }
                }
            }
        }
    });
}

// Create sales trend chart for last 30 days
function createSalesTrendChart(stockHistory) {
    // Get dates for the last 30 days
    const dates = [];
    const today = new Date();
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
    }
    
    // Generate random sales data for demonstration
    const salesData = [];
    for (let i = 0; i < 30; i++) {
        // Random value between 50000 and 300000
        salesData.push(Math.floor(Math.random() * 250000) + 50000);
    }
    
    // Format dates for display
    const formattedDates = dates.map(date => {
        const d = new Date(date);
        return `${d.getDate().toString().padStart(2, '0')}-${(d.getMonth() + 1).toString().padStart(2, '0')}`;
    });
    
    // Create chart
    const ctx = document.getElementById('salesTrendChart').getContext('2d');
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(78, 115, 223, 0.8)');
    gradient.addColorStop(1, 'rgba(78, 115, 223, 0.1)');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: formattedDates,
            datasets: [
                {
                    label: 'Sales Trend',
                    data: salesData,
                    backgroundColor: gradient,
                    borderColor: '#4e73df',
                    borderWidth: 2,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: '#4e73df',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointHoverBorderWidth: 3,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    padding: 10,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            return `${context.raw.toLocaleString()} BDT`;
                        }
                    }
                },
                datalabels: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Net Amount (BDT)',
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 100000) {
                                return (value / 1000).toFixed(0) + 'K';
                            }
                            return value.toLocaleString();
                        },
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        font: {
                            size: 10
                        },
                        autoSkip: true,
                        maxTicksLimit: 15
                    }
                }
            }
        }
    });
}

// Set up event listeners
function setupEventListeners() {
    // Refresh dashboard button
    document.getElementById('refreshDashboardBtn').addEventListener('click', async function() {
        try {
            await initDashboard();
            showNotification('Dashboard refreshed successfully', 'success');
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            showNotification('Error refreshing dashboard', 'danger');
        }
    });
    
    // Entries select for top products table
    document.getElementById('entriesSelect').addEventListener('change', async function() {
        try {
            const products = await getProducts();
            const tableBody = document.getElementById('topProductsTable');
            const limit = parseInt(this.value);
            
            // Clear existing rows
            tableBody.innerHTML = '';
            
            // Sort by quantity (highest first)
            const sortedProducts = [...products].sort((a, b) => b.quantity - a.quantity);
            
            // Take top N based on selection
            const topProducts = sortedProducts.slice(0, limit);
            
            // Generate table rows
            topProducts.forEach(product => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${product.name}</td>
                    <td>${product.unit_of_measure || 'KG'}</td>
                    <td>${product.quantity}</td>
                `;
                tableBody.appendChild(row);
            });
        } catch (error) {
            console.error('Error updating top products:', error);
            showNotification('Error updating top products', 'danger');
        }
    });
    
    // Product search
    document.getElementById('productSearch').addEventListener('input', async function() {
        try {
            const products = await getProducts();
            const tableBody = document.getElementById('topProductsTable');
            const searchTerm = this.value.toLowerCase();
            
            // Clear existing rows
            tableBody.innerHTML = '';
            
            // Filter products by search term
            const filteredProducts = products.filter(product => 
                product.name.toLowerCase().includes(searchTerm) ||
                product.sku.toLowerCase().includes(searchTerm)
            );
            
            // Sort by quantity (highest first)
            const sortedProducts = [...filteredProducts].sort((a, b) => b.quantity - a.quantity);
            
            // Take top 50 or less
            const topProducts = sortedProducts.slice(0, 50);
            
            // Generate table rows
            topProducts.forEach(product => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${product.name}</td>
                    <td>${product.unit_of_measure || 'KG'}</td>
                    <td>${product.quantity}</td>
                `;
                tableBody.appendChild(row);
            });
            
            if (topProducts.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="3" class="text-center">No matching products found.</td></tr>';
            }
        } catch (error) {
            console.error('Error searching products:', error);
            showNotification('Error searching products', 'danger');
        }
    });
} 