from django.urls import path
from . import views
urlpatterns = [
    path('', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create_request/', views.create_request, name='create_request'),
    path('view_request/', views.view_request, name='view_request'),
    path('update_project_planner_request/<str:pk>', views.update_project_planner_request, name='update_project_planner_request'),
    path('history_request/', views.history_request, name='history_request'),
    path('completed_ticket_data/', views.completeticketdata, name='completed_ticket_data'),
    path('completed_request/<str:pk>', views.completed_request, name='completed_request'),
    path('reject_request/<str:pk>', views.reject_request, name='reject_request'),
    path('project_create_request/', views.project_create_request, name='project_create_request'),
    path('project_view_request/', views.project_view_request, name='project_view_request'),
    path('logout/', views.user_logout, name="logout"),
    path('financial_approval/', views.financial_approval, name='financial_approval'),
    path('completed_financial_approval/<str:pk>', views.completed_financial_approval, name='completed_financial_approval'),
    path('financial_completed_request/', views.financial_completed_request, name='financial_completed_request'),
    path('procurement_approval/', views.procurement_approval, name='procurement_approval'),
    path('completed_procurement_approval/<str:pk>', views.completed_procurement_approval, name='completed_procurement_approval'),
    path('procurement_completed_request/', views.procurement_completed_request, name='procurement_completed_request'),
    path('admin_view_request/', views.admin_view_request, name='admin_view_request'),
    path('admin_completed_request/', views.admin_completed_request, name='admin_completed_request'),
]