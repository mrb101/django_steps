from django.urls import path
from . import views

app_name = 'claims'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Customer URLs
    path('customers/', views.CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    path('customers/new/', views.CustomerCreateView.as_view(), name='customer-create'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer-update'),

    # Policy URLs
    path('policies/', views.PolicyListView.as_view(), name='policy-list'),
    path('policies/<int:pk>/', views.PolicyDetailView.as_view(), name='policy-detail'),
    path('policies/new/', views.PolicyCreateView.as_view(), name='policy-create'),
    path('policies/new/<int:customer_id>/', views.PolicyCreateView.as_view(), name='policy-create-for-customer'),
    path('policies/<int:pk>/edit/', views.PolicyUpdateView.as_view(), name='policy-update'),

    # Claim URLs
    path('claims/', views.ClaimListView.as_view(), name='claim-list'),
    path('claims/<int:pk>/', views.ClaimDetailView.as_view(), name='claim-detail'),
    path('claims/new/', views.ClaimCreateView.as_view(), name='claim-create'),
    path('claims/new/<int:policy_id>/', views.ClaimCreateView.as_view(), name='claim-create-for-policy'),

    # Claim Processing URLs
    path('claims/<int:pk>/note/add/', views.add_claim_note, name='add-claim-note'),
    path('claims/<int:pk>/start-review/', views.start_claim_review, name='start-claim-review'),
    path('claims/<int:pk>/review/', views.process_claim_review, name='process-claim-review'),
    path('claims/<int:pk>/approve/', views.process_claim_approval, name='process-claim-approval'),
    path('claims/<int:pk>/cancel/', views.cancel_claim, name='cancel-claim'),
    path('claims/<int:pk>/payment/', views.process_claim_payment, name='process-claim-payment'),
]
