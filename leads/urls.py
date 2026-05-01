from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('campaign/new/', views.create_campaign, name='create_campaign'),
    path('campaign/<int:pk>/', views.campaign_detail, name='campaign_detail'),
    path('campaign/<int:pk>/scrape/', views.run_scrape, name='run_scrape'),
    path('lead/<int:pk>/status/', views.update_lead_status, name='update_lead_status'),
]
