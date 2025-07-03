// auth.js - Authentication functionality for Golden Niche IMS

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
                document.getElementById('emailError').textContent = 'Email is required';
                isValid = false;
            } else if (!isValidEmail(email)) {
                document.getElementById('emailError').textContent = 'Please enter a valid email address';
                isValid = false;
            }
            
            if (!password) {
                document.getElementById('passwordError').textContent = 'Password is required';
                isValid = false;
            }
            
            if (isValid) {
                // For demo purposes, use hardcoded credentials
                // In a real implementation, this would call a Django API endpoint
                if (email === 'admin@example.com' && password === 'password123') {
                    // Set authentication state
                    localStorage.setItem('isAuthenticated', 'true');
                    localStorage.setItem('currentUser', JSON.stringify({
                        email: email,
                        name: 'Admin User'
                    }));
                    
                    // Redirect to dashboard
                    window.location.href = 'dashboard.html';
                } else {
                    // Show login error
                    alert('Invalid email or password. Please try again.');
                }
            }
        });
    }
});

// Check if user is authenticated, redirect to login if not
function checkAuth() {
    if (localStorage.getItem('isAuthenticated') !== 'true' && 
        !window.location.pathname.includes('index.html')) {
        window.location.href = 'index.html';
        return false;
    }
    return true;
}

// Handle logout
function logout() {
    localStorage.setItem('isAuthenticated', 'false');
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}

// Email validation helper
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
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
    }
}); 