from django.urls import path, re_path
from django.views.generic import TemplateView
from .views import *
from .views_candidates import *
from .views_employers import *
from .views_frontend import *
from django.contrib.auth.views import *
from .job_processor.processor import HttpCallback
from .stripe import *

from django.contrib.sitemaps.views import sitemap


urlpatterns = [
    
    path('403/', TemplateView.as_view(template_name='403.html')),
    path('404/', TemplateView.as_view(template_name='404.html')),
    path('408/', TemplateView.as_view(template_name='408.html')),
    path('500/', TemplateView.as_view(template_name='500.html')),

    path('update-data/', UpdateData.as_view(), name='update-data'),
    
    path('', Homepage.as_view(), name='home'),
    path('all/', Homepage.as_view(), name='all_jobs'),
    path('reject/', Homepage.as_view(), name='reject'),
    path('add/', Homepage.as_view(), name='add'),
    path('requested/', Homepage.as_view(), name='requested'),

    path('wx-endpoint/', HttpCallback.as_view()),

    path('job/<int:pk>/', JobDetailView.as_view(), name='job'),

    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': {'jobs': JobSitemap()}},
        name='django.contrib.sitemaps.views.sitemap',
    ),

    path('robots.txt', TemplateView.as_view(template_name='jobsboard/robots.txt', content_type='text/plain')),
    path("faq/", TemplateView.as_view(template_name='jobsboard/faqs/faqs.html'), name="faq"),
    path("about/", AboutView.as_view(), name="about"),
    path('contact/', ContactView.as_view(), name='contact'),
    path('message-sent/', MessageSentSuccess.as_view(), name='message-sent'),
    path('terms-and-conditions/', TemplateView.as_view(template_name='jobsboard/terms.html'), name='terms'),

    path('register/', Registration.as_view(), name='register'),
    path('login/', LoginUser.as_view(), name='login'),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Activate account
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,50})/$',
    activate_account, name='activate'),
    path('account-activated/', TemplateView.as_view(template_name='registration/account_activated.html'), name='activated'),

    # Password Reset
    path('reset-password/', CustomPasswordResetView.as_view(), name ='reset_password'),
    path('reset-password-sent/', PasswordResetDoneView.as_view(), name ='password_reset_done'),
    re_path(r'reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,50})/$', CustomPasswordResetConfirmView.as_view(), name ='password_reset_confirm'),
    path('reset-password-complete/', PasswordResetCompleteView.as_view(), name ='password_reset_complete'),
    path('password-updated/', TemplateView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),


    # Payments
    # path('pay/', CreateStripeCheckoutSessionView.as_view(), name='pay'),
    path('payment-successful/', SuccessfulPaymentView.as_view()),
    path('payment-cancelled/', TemplateView.as_view(template_name="jobsboard/stripe/cancel.html")),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),


    # Shared backend URLs
    re_path(r'view-candidate/(?P<pk>\d+)?/?$', CandidateProfile.as_view(), name='view-candidate'),
    path('delete-profile-pic/', DeleteProfilePic.as_view()), #done
    path('update-app-status/', UpdateAppStatus.as_view(), name='update-status'),
    path('change-password/', ChangePasswordInProfile.as_view(), name ='change-password'),
    re_path(r'delete-job-app/(?P<pk>\d+)?$', DeleteJobApplication.as_view(), name='delete-job-app'),
    re_path(r'view-employer/(?P<pk>\d+)?/?$', ViewEmployerProfile.as_view(), name='view-employer'),


   

    # Candidate URLs
    path('get-wechat-id/', GetWechatID.as_view(), name='get-wechat'),
    path('edit-candidate-profile/', EditCandidateProfile.as_view(), name='edit-candidate'),
    path('edit-candidate-media/', EditCandidateMedia.as_view(), name='edit-candidate-media'),
    path('delete-cv/', DeleteCV.as_view(), name='delete-cv'), #done
    re_path(r'delete-media/(?P<media>([0-9]+/)+)?$', DeleteMedia.as_view(), name='delete-media'), #done
    path('handle-likes/', CreateDeleteLike.as_view(), name='create-delete-like'),
    path('favourite-jobs/', FavouriteJobs.as_view(), name='fav-jobs'),
    path('job-applications/', JobApplications.as_view(), name='job-apps'),





  # Employer URLs
    path('edit-employer-profile/', EditEmployerProfile.as_view(), name='edit-employer'), 
    path('post-job/', JobPostView.as_view(), name='post-job'),
    re_path(r'promote-job/(?P<pk>\d+)?/?$', PromoteJob.as_view(), name='promote-job'),
    path('manage-jobs/', ManageJobs.as_view(), name='manage-jobs'),
    path('edit-job/<int:pk>/', EditJobView.as_view(), name='edit-job'),
    re_path(r'delete-job/(?P<pk>\d+)?/?$', DeleteJob.as_view(), name='delete-job'), #not done
    path('view-applications/', ViewApplications.as_view(), name='employer-apps'),
    path('view-applications/<int:pk>/', ViewApplicantsForJob.as_view(), name='apps-by-job'),
   
]