from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from auth_api.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/auth/', include('auth_api.urls')),  
    path('api/auth/login/', LoginView.as_view(), name='token_obtain_pair'),
    # path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
