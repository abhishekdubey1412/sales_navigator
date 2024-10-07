from django.urls import path
from . import views

urlpatterns = [
    path('browser-scraping/', views.browser_scraping, name='browser_scraping'),
    path('scraping-setup/<slug:slug>/', views.scraping_setup, name='scraping_setup'),
    path('scraping-blog/<slug:slug>/', views.scraping_blog, name='scraping_blog'),
    path("launch/<str:scraping_id>/", views.launch, name="launch"),
    path('scraping-info/<str:scraping_id>/', views.scraping_info_detail, name='scraping_info_detail'),
    path('scraped-data/<str:scraping_id>/', views.scraped_data, name='scraped_data'),
    path('rename-scraping-info/<str:scraping_id>/', views.rename_scraping_info, name='rename_scraping_info'),
    path('delete-scraping-info/<str:scraping_id>/', views.delete_scraping_info, name='delete_scraping_info'),
    path('export-csv/<str:scraping_id>/', views.export_csv, name='export_csv'),
]