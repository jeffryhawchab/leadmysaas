from django.urls import path
from . import views

urlpatterns = [
    path('api/campaigns/', views.api_campaigns, name='api_campaigns'),
    path('api/campaigns/<int:pk>/', views.api_campaign_detail, name='api_campaign_detail'),
    path('api/campaigns/<int:pk>/scrape/', views.api_run_scrape, name='api_run_scrape'),
    path('api/leads/<int:pk>/', views.api_update_lead, name='api_update_lead'),
    path('api/campaigns/<int:pk>/export/', views.api_export_excel, name='api_export_excel'),
    path('', views.index, name='index'),
    path('<path:path>', views.index, name='index_catch'),
]
