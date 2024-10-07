from . import views
from django.urls import path

urlpatterns = [
    path('', views.home, name="home"),   
    path("faqs/", views.faqs, name="faqs"),  
    path("contact/", views.contact, name="contact"),  
    path("thank-you/", views.thank_you, name="thank_you"),
    path("terms-and-conditions/", views.terms_and_conditions, name="terms_and_conditions"),
    path('filter-page/', views.filter_page, name='filter_page'),
]