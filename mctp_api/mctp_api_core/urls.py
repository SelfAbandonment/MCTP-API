"""
mctp_api_core URL 配置
"""

from django.urls import path

from mctp_api.mctp_api_core.views import HealthCheckDetailView, HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("health/detail/", HealthCheckDetailView.as_view(), name="health-check-detail"),
]
