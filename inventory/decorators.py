from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.contrib import messages
from functools import wraps

def permission_required(permission):
    """
    Decorator for views that checks whether a user has a particular permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.has_perm(permission) or request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, f"You don't have permission to access this page. Required permission: {permission}")
                    # Show access denied page with the error message instead of redirecting to login
                    return render(request, 'access_denied.html', {'permission': permission})
            else:
                return redirect('login')
        return _wrapped_view
    return decorator

def view_dashboard_required(function):
    """Decorator for views that require dashboard view permission."""
    return permission_required('auth.view_dashboard')(function)

def view_products_required(function):
    """Decorator for views that require product view permission."""
    return permission_required('inventory.view_product')(function)

def change_products_required(function):
    """Decorator for views that require product change permission."""
    return permission_required('inventory.change_product')(function)

def add_products_required(function):
    """Decorator for views that require product add permission."""
    return permission_required('inventory.add_product')(function)

def delete_products_required(function):
    """Decorator for views that require product delete permission."""
    return permission_required('inventory.delete_product')(function)

def view_suppliers_required(function):
    """Decorator for views that require supplier view permission."""
    return permission_required('inventory.view_supplier')(function)

def change_suppliers_required(function):
    """Decorator for views that require supplier change permission."""
    return permission_required('inventory.change_supplier')(function)

def add_suppliers_required(function):
    """Decorator for views that require supplier add permission."""
    return permission_required('inventory.add_supplier')(function)

def delete_suppliers_required(function):
    """Decorator for views that require supplier delete permission."""
    return permission_required('inventory.delete_supplier')(function)

def view_clients_required(function):
    """Decorator for views that require client view permission."""
    return permission_required('inventory.view_client')(function)

def change_clients_required(function):
    """Decorator for views that require client change permission."""
    return permission_required('inventory.change_client')(function)

def add_clients_required(function):
    """Decorator for views that require client add permission."""
    return permission_required('inventory.add_client')(function)

def delete_clients_required(function):
    """Decorator for views that require client delete permission."""
    return permission_required('inventory.delete_client')(function)

def view_stock_required(function):
    """Decorator for views that require stock transaction view permission."""
    return permission_required('inventory.view_stocktransaction')(function)

def add_stock_required(function):
    """Decorator for views that require stock transaction add permission."""
    return permission_required('inventory.add_stocktransaction')(function)

def view_reports_required(function):
    """Decorator for views that require report view permission."""
    return permission_required('auth.view_report')(function)

def view_invoices_required(function):
    """Decorator for views that require invoice view permission."""
    return permission_required('inventory.view_invoice')(function)

def add_invoices_required(function):
    """Decorator for views that require invoice add permission."""
    return permission_required('inventory.add_invoice')(function) 