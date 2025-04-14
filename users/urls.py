from django.urls import path
from .views import SignupView, CustomTokenObtainPairView, UserProfileView, AddressListView, AddressDetailView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('addresses/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:address_id>/', AddressDetailView.as_view(), name='address-detail'),
]