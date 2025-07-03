from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'stock-history', views.StockHistoryViewSet)
router.register(r'product-types', views.ProductTypeViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'clients', views.ClientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stock/update/', views.StockUpdateView.as_view(), name='stock-update'),
    path('user-permissions/', views.UserPermissionsView.as_view(), name='user-permissions'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
] 