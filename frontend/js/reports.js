// reports.js - Reports functionality for QBITX IMS Transform Suppliers

document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!checkAuth()) return;
    
    try {
        // Check if jsPDF is properly loaded
        checkPdfLibraries();
        
        // Initialize reports page
        await initReportsPage();
    } catch (error) {
        console.error('Error initializing reports page:', error);
        showNotification('Error loading reports page', 'danger');
    }
});

// Check if PDF libraries are properly loaded
function checkPdfLibraries() {
    if (!window.jspdf || typeof window.jspdf.jsPDF !== 'function') {
        console.warn('jsPDF library not detected. PDF export may not work.');
        
        // Create a basic object to prevent errors when attempting to use PDF export
        window.jspdf = window.jspdf || {};
        window.jspdf.jsPDF = window.jspdf.jsPDF || function() {
            console.error('jsPDF not available');
            return {
                setProperties: function() {},
                text: function() {},
                setFontSize: function() {},
                setTextColor: function() {},
                setFont: function() {},
                setDrawColor: function() {},
                setLineWidth: function() {},
                line: function() {},
                autoTable: function() { 
                    throw new Error('jsPDF autoTable plugin not available');
                },
                save: function() {
                    alert('PDF generation is not available. Please check your internet connection and refresh the page.');
                }
            };
        };
    }
}

// Initialize reports page
async function initReportsPage() {
    try {
        // Load summary stats
        await loadSummaryStats();
        
        // Load products, stock history, suppliers, and clients data
        let products, stockHistory, suppliers, clients;
        
        try {
            products = await getProducts();
        } catch (error) {
            console.error('Error loading products:', error);
            showNotification('Error loading products. Using empty products list.', 'warning');
            products = [];
        }
        
        try {
            stockHistory = await getStockHistory();
            
            // Store stock history globally for reference
            window.stockHistoryData = stockHistory;
            
        } catch (error) {
            console.error('Error loading stock history:', error);
            showNotification('Error loading stock history. Using empty history list.', 'warning');
            stockHistory = [];
        }
        
        try {
            suppliers = await getSuppliers();
        } catch (error) {
            console.error('Error loading suppliers:', error);
            showNotification('Error loading suppliers. Using empty suppliers list.', 'warning');
            suppliers = [];
        }
        
        try {
            clients = await getClients();
        } catch (error) {
            console.error('Error loading clients:', error);
            showNotification('Error loading clients. Using empty clients list.', 'warning');
            clients = [];
        }
        
        // Initialize report filters
        initializeReportFilters(products, suppliers, clients);
        
        // Load charts
        createTransactionsChart(stockHistory);
        createCategoryChart(products);
        
        // Load stock history table
        loadStockHistoryTable(stockHistory, products);
        
        // Set up event listeners for export, print, and report generation
        setupEventListeners(products, stockHistory, suppliers, clients);
    } catch (error) {
        console.error('Error loading reports data:', error);
        showNotification('Error initializing reports page. Please refresh to try again.', 'danger');
    }
}

// Initialize report filters
function initializeReportFilters(products, suppliers, clients) {
    // Set default dates (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    // Format dates as YYYY-MM-DD for the input fields
    const formatDateForInput = (date) => {
        return date.toISOString().split('T')[0];
    };
    
    document.getElementById('startDate').value = formatDateForInput(thirtyDaysAgo);
    document.getElementById('endDate').value = formatDateForInput(today);
    
    // Populate product filter
    const productFilter = document.getElementById('productFilter');
    
    // Clear existing options except the default "All Products" option
    while (productFilter.options.length > 1) {
        productFilter.remove(1);
    }
    
    // Sort products by name for better usability
    const sortedProducts = [...products].sort((a, b) => a.name.localeCompare(b.name));
    
    // Add all products to the dropdown
    sortedProducts.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = product.name;
        productFilter.appendChild(option);
    });
    
    // Store stock history data for reference
    if (window.stockHistoryData === undefined && window.getStockHistory) {
        getStockHistory().then(data => {
            window.stockHistoryData = data;
        }).catch(error => {
            console.error('Failed to store stock history data:', error);
        });
    }
    
    // Populate product type filter
    const productTypes = [...new Set(products.map(product => product.type))].sort();
    const productTypeFilter = document.getElementById('productTypeFilter');
    // Clear existing options except the default "All Types" option
    while (productTypeFilter.options.length > 1) {
        productTypeFilter.remove(1);
    }
    
    productTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        productTypeFilter.appendChild(option);
    });
    
    // Populate supplier filter
    const supplierFilter = document.getElementById('supplierFilter');
    // Clear existing options except the default "All Suppliers" option
    while (supplierFilter.options.length > 1) {
        supplierFilter.remove(1);
    }
    
    // Sort suppliers by name
    const sortedSuppliers = [...suppliers].sort((a, b) => a.name.localeCompare(b.name));
    sortedSuppliers.forEach(supplier => {
        const option = document.createElement('option');
        option.value = supplier.id;
        option.textContent = supplier.name;
        supplierFilter.appendChild(option);
    });
    
    // Populate client filter
    const clientFilter = document.getElementById('clientFilter');
    // Clear existing options except the default "All Clients" option
    while (clientFilter.options.length > 1) {
        clientFilter.remove(1);
    }
    
    // Sort clients by name
    const sortedClients = [...clients].sort((a, b) => a.name.localeCompare(b.name));
    sortedClients.forEach(client => {
        const option = document.createElement('option');
        option.value = client.id;
        option.textContent = client.name;
        clientFilter.appendChild(option);
    });
    
    // Set up report type change handler
    document.getElementById('reportType').addEventListener('change', function() {
        const reportType = this.value;
        const supplierContainer = document.getElementById('supplierFilterContainer');
        const clientContainer = document.getElementById('clientFilterContainer');
        
        if (reportType === 'purchases') {
            supplierContainer.style.display = 'block';
            clientContainer.style.display = 'none';
        } else if (reportType === 'sales') {
            supplierContainer.style.display = 'none';
            clientContainer.style.display = 'block';
        } else {
            supplierContainer.style.display = 'block';
            clientContainer.style.display = 'block';
        }
    });
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
            maintainAspectRatio: true,
            aspectRatio: 2.5,
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

// Create custom report chart based on filtered data
function createCustomReportChart(filteredData, startDate, endDate) {
    // Get all dates between start and end date
    const dates = [];
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    for (let date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
        dates.push(date.toISOString().split('T')[0]);
    }
    
    // Count stock in and stock out for each day
    const stockInData = Array(dates.length).fill(0);
    const stockOutData = Array(dates.length).fill(0);
    
    filteredData.forEach(transaction => {
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
    const ctx = document.getElementById('customReportChart').getContext('2d');
    
    // Remove existing chart if it exists
    if (window.customReportChart && typeof window.customReportChart.destroy === 'function') {
        window.customReportChart.destroy();
    }
    
    window.customReportChart = new Chart(ctx, {
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
            maintainAspectRatio: true,
            aspectRatio: 2.5, // Make the chart shorter
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
        const value = product.quantity * product.buying_price;
        
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
            maintainAspectRatio: true,
            aspectRatio: 2.5,
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
        
        // Only use explicit wastage value, never calculate
        let wastage = 0;
        if (typeof transaction.wastage === 'number' && !isNaN(transaction.wastage)) {
            wastage = transaction.wastage;
        } else if (typeof transaction.wastage === 'string' && transaction.wastage.trim() !== '' && !isNaN(parseFloat(transaction.wastage))) {
            wastage = parseFloat(transaction.wastage);
        } else if (typeof transaction.wastage_amount === 'number' && !isNaN(transaction.wastage_amount)) {
            wastage = transaction.wastage_amount;
        } else if (typeof transaction.wastage_amount === 'string' && transaction.wastage_amount.trim() !== '' && !isNaN(parseFloat(transaction.wastage_amount))) {
            wastage = parseFloat(transaction.wastage_amount);
        } else {
            wastage = 0;
        }
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td>${transaction.product_name}</td>
            <td>${sku}</td>
            <td><span class="${transactionClass}">${transactionLabel}</span></td>
            <td>${transaction.quantity}</td>
            <td>${transaction.uom || 'Unit'}</td>
            <td>${transaction.type === 'IN' ? formatCurrency(parseFloat(transaction.unit_price) || 0) : formatCurrency(product.buying_price)}</td>
            <td>${transaction.type === 'OUT' ? formatCurrency(parseFloat(transaction.unit_price) || 0) : formatCurrency(product.selling_price)}</td>
            <td>${formatCurrency(wastage)}</td>
            <td>${formatCurrency(transaction.discount)}</td>
            <td>${formatCurrency(transaction.payable_amount)}</td>
            <td>${transaction.type === 'OUT' ? `${formatCurrency(transaction.profit_margin)} (${((transaction.profit_margin / transaction.buying_price) * 100).toFixed(2)}%)` : '-'}</td>
            <td class="${transaction.type === 'OUT' ? 'text-success' : 'text-danger'}">${transaction.type === 'OUT' ? formatCurrency(transaction.total_profit) : '-'}</td>
            <td>${transaction.supplier_name || transaction.client_name || '-'}</td>
            <td>${transaction.reference_number || '-'}</td>
            <td>${transaction.notes || '-'}</td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Show message if no history
    if (sortedHistory.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No stock transactions found</td></tr>';
    }
}

// Function to generate a custom report based on selected filters
async function generateCustomReport() {
    // Get form values
    const reportType = document.getElementById('reportType').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const product = document.getElementById('productFilter').value;
    const supplier = document.getElementById('supplierFilter').value;
    const client = document.getElementById('clientFilter').value;
    
    // Show loading state
    const loadingElement = document.getElementById('reportLoading');
    if (loadingElement) {
        loadingElement.classList.remove('d-none');
    }
    
    try {
        // Get authentication token
        const token = localStorage.getItem('auth_token') || localStorage.getItem('authToken');
        if (!token) {
            showNotification('You need to be logged in to generate reports', 'danger');
            if (loadingElement) loadingElement.classList.add('d-none');
            return;
        }
        
        console.log('Generating report using token:', token);
        
        // Fetch stock history data using the helper function from app.js
        const stockHistory = await getStockHistory();
        
        if (!stockHistory || stockHistory.length === 0) {
            console.warn('No stock history data available');
            showNotification('No stock history data available. Please check your connection or try again later.', 'warning');
            if (loadingElement) loadingElement.classList.add('d-none');
            return;
        }
        
        // Filter stock history based on selected filters
        let filteredData = [...stockHistory];
        
        // Filter by date range
        if (startDate) {
            const startDateTime = new Date(startDate);
            filteredData = filteredData.filter(item => new Date(item.date) >= startDateTime);
        }
        
        if (endDate) {
            const endDateTime = new Date(endDate);
            endDateTime.setHours(23, 59, 59, 999); // End of the day
            filteredData = filteredData.filter(item => new Date(item.date) <= endDateTime);
        }
        
        // Filter by transaction type
        if (reportType !== 'all') {
            if (reportType === 'sales') {
                filteredData = filteredData.filter(item => item.type === 'OUT');
            } else if (reportType === 'purchases') {
                filteredData = filteredData.filter(item => item.type === 'IN');
            }
        }
        
        // Filter by product
        if (product && product !== 'all') {
            filteredData = filteredData.filter(item => String(item.product) === String(product));
        }
        
        // Filter by supplier
        if (supplier && supplier !== 'all') {
            filteredData = filteredData.filter(item => 
                String(item.supplier) === String(supplier) || 
                (item.supplier_ref && String(item.supplier_ref) === String(supplier))
            );
        }
        
        // Filter by client
        if (client && client !== 'all') {
            filteredData = filteredData.filter(item => 
                String(item.client) === String(client) || 
                (item.client_ref && String(item.client_ref) === String(client))
            );
        }
        
        // Sort by date (newest first)
        filteredData.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        // Enhance transaction data with additional fields
        const enhancedData = await Promise.all(filteredData.map(async (transaction) => {
            // Get product details
            const product = await getProductById(transaction.product);
            
            // Normalize wastage field - check both possible field names
            let wastage = 0;
            if (typeof transaction.wastage === 'number' && !isNaN(transaction.wastage)) {
                wastage = transaction.wastage;
            } else if (typeof transaction.wastage === 'string' && transaction.wastage.trim() !== '' && !isNaN(parseFloat(transaction.wastage))) {
                wastage = parseFloat(transaction.wastage);
            } else if (typeof transaction.wastage_amount === 'number' && !isNaN(transaction.wastage_amount)) {
                wastage = transaction.wastage_amount;
            } else if (typeof transaction.wastage_amount === 'string' && transaction.wastage_amount.trim() !== '' && !isNaN(parseFloat(transaction.wastage_amount))) {
                wastage = parseFloat(transaction.wastage_amount);
            } else if (transaction.is_wastage === true) {
                const unitPrice = parseFloat(transaction.unit_price) || 0;
                const quantity = parseInt(transaction.quantity) || 0;
                wastage = unitPrice * quantity;
            } else {
                wastage = 0;
            }
            
            // Calculate profit for OUT transactions
            let profit = 0;
            let profitMargin = 0;
            
            if (transaction.type === 'OUT') {
                const sellingPrice = parseFloat(transaction.unit_price) || 0;
                const buyingPrice = parseFloat(product.buying_price) || 0;
                const quantity = parseInt(transaction.quantity) || 0;
                const discount = parseFloat(transaction.discount) || 0;
                
                // Calculate total profit
                profit = (sellingPrice - buyingPrice) * quantity - discount - wastage;
                
                // Calculate profit margin percentage
                const revenue = sellingPrice * quantity - discount;
                if (revenue > 0) {
                    profitMargin = (profit / revenue) * 100;
                }
            }
            
            return {
                ...transaction,
                product_details: product,
                profit,
                profit_margin: profitMargin,
                wastage: wastage // Ensure wastage is normalized
            };
        }));
        
        // Display the report results
        displayReportResults(enhancedData, reportType, startDate, endDate);
        
    } catch (error) {
        console.error('Error generating report:', error);
        showNotification('Error generating report', 'danger');
    } finally {
        // Hide loading state
        if (loadingElement) {
            loadingElement.classList.add('d-none');
        }
    }
}

// Display report results
function displayReportResults(filteredData, reportType, startDate, endDate) {
    // Show results section
    const reportResultsElement = document.getElementById('reportResults');
    if (!reportResultsElement) {
        console.error("Report results element not found with ID 'reportResults'");
        return;
    }
    reportResultsElement.style.display = 'block';
    reportResultsElement.classList.remove('d-none');
    
    // Generate report description
    let reportDescription = 'All Transactions';
    if (reportType === 'sales') {
        reportDescription = 'Sales Transactions';
    } else if (reportType === 'purchases') {
        reportDescription = 'Purchase Transactions';
    }
    
    if (startDate && endDate) {
        reportDescription += ` from ${formatDate(startDate)} to ${formatDate(endDate)}`;
    } else if (startDate) {
        reportDescription += ` from ${formatDate(startDate)}`;
    } else if (endDate) {
        reportDescription += ` until ${formatDate(endDate)}`;
    }
    
    const reportDescriptionElement = document.getElementById('reportDescription');
    if (reportDescriptionElement) {
        reportDescriptionElement.textContent = reportDescription;
    }
    
    // Calculate summary statistics
    let totalTransactions = filteredData.length;
    let totalValue = 0;
    let totalItems = 0;
    let totalDiscount = 0;
    let totalWastage = 0;
    let totalPayable = 0;
    let totalProfit = 0;
    
    // Process each transaction
    filteredData.forEach(transaction => {
        const quantity = parseInt(transaction.quantity) || 0;
        const unitPrice = parseFloat(transaction.unit_price) || 0;
        const discount = parseFloat(transaction.discount) || 0;
        const wastage = parseFloat(transaction.wastage) || 0;
        
        totalItems += quantity;
        totalDiscount += discount;
        totalWastage += wastage;
        
        if (transaction.type === 'IN') {
            // For purchases
            const transactionValue = quantity * unitPrice;
            totalValue += transactionValue;
            totalPayable += transactionValue - discount;
        } else {
            // For sales
            const transactionValue = quantity * unitPrice;
            totalValue += transactionValue;
            totalPayable += transactionValue - discount;
            totalProfit += transaction.profit;
        }
    });
    
    // Update summary cards - with null checks
    const elementsToUpdate = {
        'totalTransactions': totalTransactions,
        'totalValue': formatCurrency(totalValue),
        'totalItems': totalItems,
        'totalDiscount': formatCurrency(totalDiscount),
        'totalWastage': formatCurrency(totalWastage),
        'totalPayable': formatCurrency(totalPayable),
        'totalProfit': formatCurrency(totalProfit)
    };
    
    // Update each element if it exists
    for (const [id, value] of Object.entries(elementsToUpdate)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        } else {
            console.warn(`Element with ID '${id}' not found`);
        }
    }
    
    // Set profit/loss color
    const profitElement = document.getElementById('totalProfit');
    if (profitElement) {
        if (totalProfit > 0) {
            profitElement.classList.remove('text-danger');
            profitElement.classList.add('text-success');
        } else {
            profitElement.classList.remove('text-success');
            profitElement.classList.add('text-danger');
        }
    }
    
    // Apply custom styling to make summary tiles fit in one row
    applySummaryTileStyling();
    
    // Generate transaction table
    const tableBody = document.getElementById('customReportTable');
    if (!tableBody) {
        console.error("Table body element not found with ID 'customReportTable'");
        return; // Exit the function if the element doesn't exist
    }
    tableBody.innerHTML = '';
    
    if (filteredData.length > 0) {
        filteredData.forEach(transaction => {
            // Format date
            const date = new Date(transaction.date);
            const formattedDate = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
            
            // Get product info
            const product = transaction.product_details;
            
            // Create table row
            const row = document.createElement('tr');
            
            // Set row class based on transaction type
            if (transaction.type === 'IN') {
                row.classList.add('table-success');
            } else {
                row.classList.add('table-warning');
            }
            
            // Determine profit class
            let profitClass = '';
            if (transaction.profit > 0) {
                profitClass = 'text-success';
            } else if (transaction.profit < 0) {
                profitClass = 'text-danger';
            }
            
            // Populate row
            row.innerHTML = `
                <td>${formattedDate}</td>
                <td>${product.name}</td>
                <td>${product.sku}</td>
                <td>${transaction.type === 'IN' ? 'Purchase' : 'Sale'}</td>
                <td>${transaction.quantity}</td>
                <td>${product.unit_of_measure || 'Unit'}</td>
                <td>${transaction.type === 'IN' ? formatCurrency(parseFloat(transaction.unit_price) || 0) : formatCurrency(product.buying_price)}</td>
                <td>${transaction.type === 'OUT' ? formatCurrency(parseFloat(transaction.unit_price) || 0) : formatCurrency(product.selling_price)}</td>
                <td>${formatCurrency(transaction.wastage)}</td>
                <td>${formatCurrency(parseFloat(transaction.discount) || 0)}</td>
                <td>${formatCurrency(transaction.quantity * transaction.unit_price - transaction.discount)}</td>
                <td class="${profitClass}">${transaction.type === 'OUT' ? transaction.profit_margin.toFixed(2) + '%' : '-'}</td>
                <td class="${profitClass}">${transaction.type === 'OUT' ? formatCurrency(transaction.profit) : '-'}</td>
                <td>${transaction.supplier_name || transaction.client_name || transaction.supplier || transaction.client || '-'}</td>
                <td>${transaction.reference_number || '-'}</td>
                <td>${transaction.notes || '-'}</td>
            `;
            
            tableBody.appendChild(row);
        });
    } else {
        // No transactions found
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="16" class="text-center">No transactions found for the selected criteria.</td>
        `;
        tableBody.appendChild(row);
    }
    
    // Generate chart if included
    const chartContainer = document.getElementById('customReportChartContainer');
    if (chartContainer && document.getElementById('includeCharts') && document.getElementById('includeCharts').checked) {
        chartContainer.style.display = 'block';
        createCustomReportChart(filteredData, startDate, endDate);
    } else if (chartContainer) {
        chartContainer.style.display = 'none';
    }
}

// Apply special styling to make the summary tiles smaller and fit in one row
function applySummaryTileStyling() {
    // Get all card-stats elements
    const cardStats = document.querySelectorAll('.card-stats');
    const cardValues = document.querySelectorAll('.card-value');
    const cardTitles = document.querySelectorAll('.card-title');
    
    // Update styles for the cards - make them smaller
    cardStats.forEach(card => {
        card.style.padding = '0';
        card.style.margin = '0 0 10px 0';
        card.style.height = 'auto';
        
        // Find the card-body inside this card
        const cardBody = card.querySelector('.card-body');
        if (cardBody) {
            cardBody.style.padding = '10px';
        }
    });
    
    // Make the numbers smaller and allow them to wrap if needed
    cardValues.forEach(value => {
        value.style.fontSize = '1.1rem';
        value.style.fontWeight = '600';
        value.style.lineHeight = '1.2';
        value.style.whiteSpace = 'nowrap';
        value.style.overflow = 'hidden';
        value.style.textOverflow = 'ellipsis';
    });
    
    // Make the title text smaller
    cardTitles.forEach(title => {
        title.style.fontSize = '0.75rem';
        title.style.marginBottom = '0.25rem';
    });
    
    // Update the column widths to fit all 7 tiles in one row
    const summaryRow = document.querySelector('#reportResults .row.mb-4');
    if (summaryRow) {
        const columns = summaryRow.querySelectorAll('.col-md-2');
        columns.forEach(col => {
            col.classList.remove('col-md-2');
            col.classList.add('col-md-auto');
            col.style.flex = '1';
            col.style.maxWidth = 'calc(100% / 7)'; // Ensure all 7 fit in one row
            col.style.padding = '0 5px';
        });
    }
    
    // Make icons smaller
    const cardIcons = document.querySelectorAll('.card-icon');
    cardIcons.forEach(icon => {
        icon.style.fontSize = '1.5rem';
        icon.style.marginTop = '0';
    });
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Set up event listeners
function setupEventListeners(products, stockHistory, suppliers, clients) {
    // Export buttons
    document.getElementById('exportCsvBtn').addEventListener('click', function() {
        // Export the appropriate table based on whether a custom report is displayed
        const tableId = document.getElementById('reportResults').style.display !== 'none' ? 
            'customReportTable' : 'stockHistoryTable';
        const filename = document.getElementById('reportResults').style.display !== 'none' ?
            'golden_niche_custom_report.csv' : 'golden_niche_stock_history.csv';
        exportTableToCSV(tableId, filename);
    });
    
    document.getElementById('exportExcelBtn').addEventListener('click', function() {
        // Export the appropriate table based on whether a custom report is displayed
        const tableId = document.getElementById('reportResults').style.display !== 'none' ? 
            'customReportTable' : 'stockHistoryTable';
        const filename = document.getElementById('reportResults').style.display !== 'none' ?
            'golden_niche_custom_report.xlsx' : 'golden_niche_stock_history.xlsx';
        exportTableToExcel(tableId, filename);
    });
    
    document.getElementById('exportPdfBtn').addEventListener('click', function() {
        // Export the appropriate table based on whether a custom report is displayed
        const isCustomReport = document.getElementById('reportResults').style.display !== 'none';
        const tableId = isCustomReport ? 'customReportTable' : 'stockHistoryTable';
        const filename = isCustomReport ?
            'golden_niche_custom_report.pdf' : 'golden_niche_stock_history.pdf';
        
        // Verify the table exists and has data
        const table = document.getElementById(tableId);
        if (!table) {
            console.error(`Table with ID ${tableId} not found`);
            alert('Error: Could not find the table to export. Please try again.');
            return;
        }
        
        exportTableToPDF(tableId, filename);
    });
    
    // Generate report form
    document.getElementById('reportForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get selected product ID
        const productId = document.getElementById('productFilter').value;
        
        // If a specific product is selected, check if there are transactions for it
        if (productId !== 'all') {
            const productTransactions = stockHistory.filter(t => String(t.product) === String(productId));
            
            if (productTransactions.length === 0) {
                console.warn(`No transactions found for product ID ${productId}`);
                showNotification(`No transactions found for the selected product. Please select another product or adjust your filters.`, 'warning');
            }
        }
        
        generateCustomReport();
    });
    
    // Modify report button
    document.getElementById('modifyReportBtn').addEventListener('click', function() {
        const reportResults = document.getElementById('reportResults');
        reportResults.style.display = 'none';
        reportResults.classList.add('d-none');
        
        // Refresh the filters to ensure all products are shown
        initializeReportFilters(products, suppliers, clients);
    });
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    // If we're exporting a custom report, add report header info
    if (tableId === 'customReportTable') {
        const reportDescription = document.getElementById('reportDescription').textContent;
        csv.push(`QBITX IMS Transform Suppliers - ${reportDescription}`);
        csv.push(`Generated on: ${new Date().toLocaleString()}`);
        csv.push(''); // Empty line for spacing
        
        // Add summary statistics
        csv.push('Report Summary:');
        csv.push(`Total Transactions: ${document.getElementById('totalTransactions').textContent}`);
        csv.push(`Total Value: ${document.getElementById('totalValue').textContent}`);
        csv.push(`Total Items: ${document.getElementById('totalItems').textContent}`);
        csv.push(`Total Profit: ${document.getElementById('totalProfit').textContent}`);
        csv.push(''); // Empty line for spacing
    }
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Get text content and clean it
            let data = cols[j].textContent.replace(/(\r\n|\n|\r)/gm, '').trim();
            
            // Quote fields with commas
            if (data.includes(',')) {
                data = `"${data}"`;
            }
            
            row.push(data);
        }
        
        csv.push(row.join(','));
    }
    
    // Download CSV file
    downloadCSV(csv.join('\n'), filename);
}

// Download CSV file
function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], {type: 'text/csv'});
    const downloadLink = document.createElement('a');
    
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Export table to Excel
function exportTableToExcel(tableId, filename) {
    // This is a simplified version - in a real app, you might use a library like SheetJS
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Convert table to CSV first
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    // If we're exporting a custom report, add report header info
    if (tableId === 'customReportTable') {
        const reportDescription = document.getElementById('reportDescription').textContent;
        csv.push(`QBITX IMS Transform Suppliers - ${reportDescription}`);
        csv.push(`Generated on: ${new Date().toLocaleString()}`);
        csv.push(''); // Empty line for spacing
        
        // Add summary statistics
        csv.push('Report Summary:');
        csv.push(`Total Transactions:\t${document.getElementById('totalTransactions').textContent}`);
        csv.push(`Total Value:\t${document.getElementById('totalValue').textContent}`);
        csv.push(`Total Items:\t${document.getElementById('totalItems').textContent}`);
        csv.push(`Total Profit:\t${document.getElementById('totalProfit').textContent}`);
        csv.push(''); // Empty line for spacing
    }
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            row.push(cols[j].textContent.trim());
        }
        
        csv.push(row.join('\t'));
    }
    
    // Create Excel file (actually a TSV file that Excel can open)
    const csvFile = new Blob([csv.join('\n')], {type: 'application/vnd.ms-excel'});
    const downloadLink = document.createElement('a');
    
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Export table to PDF
function exportTableToPDF(tableId, filename) {
    // Show the terms and conditions modal
    const termsModal = new bootstrap.Modal(document.getElementById('termsModal'));
    termsModal.show();
    
    // Set up the generate PDF button
    document.getElementById('generatePdfWithTerms').addEventListener('click', function() {
        // Get terms and company information
        const companyName = document.getElementById('companyName').value || 'QBITX IMS Transform Suppliers';
        const companyAddress = document.getElementById('companyAddress').value || '';
        const companyContact = document.getElementById('companyContact').value || '';
        const reportNotes = document.getElementById('reportNotes').value;
        const termsText = document.getElementById('termsText').value;
        const signatureName = document.getElementById('signatureName').value;
        
        // Generate PDF with terms
        generatePDF(tableId, filename, {
            companyName,
            companyAddress,
            companyContact,
            reportNotes,
            termsText,
            signatureName
        });
        
        // Close the modal
        termsModal.hide();
    }, { once: true }); // Ensure event listener is only added once
}

// Generate PDF with jsPDF
function generatePDF(tableId, filename, terms) {
    try {
        // Access jsPDF from the global scope
        if (!window.jspdf || !window.jspdf.jsPDF) {
            console.error('jsPDF library not found. Please ensure it is properly loaded.');
            alert('Error: PDF generation library not found. Please refresh the page and try again.');
            return;
        }
        
        // Create a new PDF document - use A4 landscape format
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('landscape', 'mm', 'a4');
        
        // Set document properties
        doc.setProperties({
            title: filename,
            subject: 'QBITX IMS Transform Suppliers Report',
            author: 'QBITX IMS Transform Suppliers',
            keywords: 'report, inventory, transactions',
            creator: 'QBITX IMS Transform Suppliers'
        });
        
        // Check if autoTable plugin is available
        if (typeof doc.autoTable !== 'function') {
            console.error('jsPDF autoTable plugin not found');
            alert('Error: PDF table plugin not found. Please refresh the page and try again.');
            return;
        }
        
        // Calculate page dimensions
        const pageWidth = doc.internal.pageSize.width;
        const pageHeight = doc.internal.pageSize.height;
        const margin = 5; // Minimal margin to maximize table space
        
        // Add company header
        doc.setFontSize(14);
        doc.setTextColor(0, 0, 0);
        doc.setFont(undefined, 'bold');
        doc.text(terms.companyName, margin, margin + 5);
        doc.setFont(undefined, 'normal');
        
        doc.setFontSize(8);
        doc.text(terms.companyAddress, margin, margin + 10);
        doc.text(terms.companyContact, margin, margin + 14);
        
        // Add report title and date
        const isCustomReport = tableId === 'customReportTable';
        let reportTitle = isCustomReport ? 
            document.getElementById('reportDescription').textContent : 
            'Stock History Report';
        
        // Add horizontal line under company info
        doc.setDrawColor(200, 200, 200);
        doc.setLineWidth(0.5);
        doc.line(margin, margin + 16, pageWidth - margin, margin + 16);
        
        // Add report title
        doc.setFontSize(11);
        doc.setFont(undefined, 'bold');
        doc.text(reportTitle, margin, margin + 22);
        doc.setFont(undefined, 'normal');
        
        // Get report info
        let startY = margin + 26; // Increased spacing to prevent overlap
        if (isCustomReport) {
            const reportType = document.getElementById('reportType').value;
            
            // Get the supplier/client info
            let partyType = '';
            let partyName = '';
            let partyDetails = '';
            
            if (reportType === 'sales') {
                partyType = 'Customer';
                
                const clientSelect = document.getElementById('clientFilter');
                if (clientSelect.value !== 'all') {
                    partyName = clientSelect.options[clientSelect.selectedIndex].text;
                    
                    // Get detailed client info if available
                    const clients = window.MOCK_CLIENTS || [];
                    const client = clients.find(c => c.name === partyName);
                    if (client) {
                        partyDetails = `${client.contact_person || 'N/A'}, ${client.address || 'N/A'}`;
                    }
                }
            } else if (reportType === 'purchases') {
                partyType = 'Supplier';
                
                const supplierSelect = document.getElementById('supplierFilter');
                if (supplierSelect.value !== 'all') {
                    partyName = supplierSelect.options[supplierSelect.selectedIndex].text;
                    
                    // Get detailed supplier info if available
                    const suppliers = window.MOCK_SUPPLIERS || [];
                    const supplier = suppliers.find(s => s.name === partyName);
                    if (supplier) {
                        partyDetails = `${supplier.contact_person || 'N/A'}, ${supplier.address || 'N/A'}`;
                    }
                }
            }
            
            // Add supplier/customer info if available
            if (partyName) {
                doc.setFontSize(9);
                doc.text(`${partyType} : ${partyName} - ${partyDetails}`, margin, startY);
                startY += 5;
            }
            
            // Add report details - on separate lines to prevent overlap
            doc.setFontSize(9);
            doc.text(`Report Type : ${reportType === 'sales' ? 'Sales' : reportType === 'purchases' ? 'Purchase' : 'All Transactions'}`, margin, startY);
            startY += 5;
            
            // Add date range
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            doc.text(`From Date : ${formatDate(startDate)}`, margin, startY);
            startY += 5;
            doc.text(`To Date : ${formatDate(endDate)}`, margin, startY);
            startY += 6; // Extra spacing before table
            
            // Add profit information
            const totalProfit = document.getElementById('totalProfit').textContent;
            doc.text(`Total Profit/Loss : ${totalProfit}`, margin, startY);
            startY += 6; // Extra spacing before table
        }
        
        // Add table data
        const table = document.getElementById(tableId);
        if (!table) {
            console.error(`Table with ID ${tableId} not found`);
            alert(`Error: Could not find the table to export. Please try again.`);
            return;
        }
        
        // Extract table headers and data
        let headers = [];
        const data = [];
        
        // Get headers
        const headerRow = table.querySelector('thead tr');
        if (headerRow) {
            headerRow.querySelectorAll('th').forEach(th => {
                headers.push(th.textContent.trim());
            });
        } else {
            // Define default headers based on table type if none found
            if (isCustomReport) {
                headers = ['Date', 'Product', 'SKU', 'Transaction', 'Qty', 'UOM', 'Buying Price', 'Selling Price', 
                          'Wastage', 'Discount', 'Payable Amount', 'Profit Margin', 'Total Profit',
                          'Supplier/Customer', 'Reference', 'Notes'];
            } else {
                headers = ['Date', 'Product', 'SKU', 'Transaction Type', 'Quantity', 'Notes'];
            }
        }
        
        // Helper to format currency values for PDF
        const formatPdfCurrency = (value) => {
            if (value === '-' || value === '') return '-';
            const num = parseFloat(value.toString().replace(/[^\d.-]/g, ''));
            if (isNaN(num)) return value;
            return num.toFixed(2);
        };
        
        // Get data rows
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach((tr, rowIndex) => {
            const rowData = [];
            tr.querySelectorAll('td').forEach((td, colIndex) => {
                // Get plain text content without HTML tags
                let text = td.textContent.trim();
                
                // Format money amounts to ensure they're properly aligned
                if (headers[colIndex] && (
                    headers[colIndex].includes('Price') || 
                    headers[colIndex].includes('Amount') || 
                    headers[colIndex].includes('Discount') || 
                    headers[colIndex].includes('Wastage') || 
                    headers[colIndex].includes('Value') ||
                    headers[colIndex].includes('Profit') ||
                    headers[colIndex].includes('Margin'))) {
                    
                    // Special handling for non-numeric values like '-'
                    if (text === '-') {
                        // Keep as is
                    } else {
                        // Format currency values for PDF
                        text = formatPdfCurrency(text);
                    }
                }
                
                rowData.push(text);
            });
            
            if (rowData.length > 0) {
                data.push(rowData);
            }
        });
        
        // If no data rows were found, add a message
        if (data.length === 0) {
            data.push(['No transactions found matching the selected criteria']);
        }
        
        // Define column styles for the table
        const columnStyles = {};
        
        // Set up auto-table configuration
        try {
            doc.autoTable({
                head: [headers],
                body: data,
                startY: startY,
                theme: 'grid',
                headStyles: {
                    fillColor: [240, 240, 240],
                    textColor: [0, 0, 0],
                    fontStyle: 'bold',
                    halign: 'center',
                    fontSize: 7
                },
                styles: {
                    fontSize: 6.5,
                    cellPadding: 1, // Reduced padding to fit more content
                    lineWidth: 0.1,
                    valign: 'middle'
                },
                columnStyles: columnStyles,
                margin: { top: margin, right: margin, bottom: margin, left: margin },
                tableWidth: 'auto', // Let jsPDF calculate the optimal width
                didDrawPage: function(data) {
                    // Add header to each page
                    doc.setFontSize(8);
                    doc.setTextColor(100, 100, 100);
                    doc.text(terms.companyName, margin, 5);
                    doc.text(reportTitle, pageWidth/2, 5, { align: 'center' });
                    doc.text(`Page ${data.pageNumber}`, pageWidth - margin, 5, { align: 'right' });
                    
                    // Add footer with page number
                    doc.text(`Page ${data.pageNumber} of ${doc.getNumberOfPages()}`, pageWidth/2, pageHeight - 5, { align: 'center' });
                }
            });
        } catch (error) {
            console.error('Error generating table in PDF:', error);
            alert('Error generating PDF table. Please try again. Error: ' + error.message);
            return;
        }
        
        // Save the PDF
        doc.save(filename);
        
        console.log('PDF successfully generated and saved as', filename);
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        alert('Error generating PDF. Please try again. Error: ' + error.message);
    }
} 