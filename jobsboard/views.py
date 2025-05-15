from django.views import View
from django.views.generic import FormView, TemplateView, DeleteView
from django.views.generic.edit import CreateView

from django.shortcuts import render, redirect
from django.db.models import Q

from django.http import HttpResponse, JsonResponse

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import PasswordChangeView, LoginView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sitemaps import Sitemap

from django.utils import six, timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _

from django.template.loader import render_to_string
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import PermissionDenied

from django.urls import reverse

from .models import *
from .forms import *
from .tasks import *
from django.core.mail import send_mail


from io import BytesIO
import sys
import json
from PIL import Image


# Generic views that everyone can access
# Mainly for authentication and user admin


# Currently not in use
# class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
#     def test_func(self):
#         return self.request.user.is_superuser


class JobSitemap(Sitemap):
    changefreq = 'daily'

    def items(self):
        return Job.objects.filter(is_job=True).order_by('-time_updated')



class AboutView(TemplateView):
    template_name = 'jobsboard/about.html'

    def get_context_data(self, **kwargs):
        context = super(AboutView, self).get_context_data(**kwargs)

        jobs = Job.objects.filter(is_job=True)

        context['jobs_last_day'] = jobs.filter(time_created__gt = timezone.now() - timezone.timedelta(days=1)).count()
        context['total_count'] = jobs.count()
        context['teach_related'] = jobs.filter(job_types__contains=['teaching']).count()

        return context
        


class LoginUser(LoginView):
    redirect_authenticated_user = True
    form_class = LoginForm



class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )


class Registration(CreateView):

    form_class = SignUpForm
    template_name = 'registration/register.html'
    # success_url = reverse_lazy('home')

    def post(self, request):
        form = self.get_form()

        print(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False

            wechat = request.POST.get('wechat')

            if wechat:
                user.wechat_id = wechat
            
            user.save()

            user_type = request.POST.get('user_type')


            print(f'WECHAT: {wechat}')
            print(f'USER TYPE: {user_type}')


            if user_type == 'candidate':
                sex = 1 if request.POST.get('sex') == 'male' else 0
                Candidate.objects.create(user=user,sex=sex)
            else:
                employer = Employer.objects.create(user=user)

            # If wechat provided
            # 1) Check if it exists - post subscription
            # 2) If employer, check if any jobs are associated with it

                # if wechat:
                #     jobs = Job.objects.filter(wxid_alias__wx_alias__contains=[wechat])
                #     jobs.update(employer=employer)

                #     print(f'ASSOCIATED JOBS: {jobs}')

            
            

            self.send_activation_email(request, user)
            return render(request, 'registration/confirm_email.html', {'email' : user.email})
        
        else:
            print('FORM INVALID!')
            self.object = ''
            return super().form_invalid(form)
        
        
    def send_activation_email(self, request, user):
            
            account_activation_token = TokenGenerator()

            message = render_to_string('registration/activate_account.html', {
                'name': user.first_name,
                'domain': 'wechatjobs.com',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http'
            })
            
            send_mail(
                'Activate your account',
                message,
                '"Wechat Jobs" <registration@wechatjobs.com>',
                [user.email],
                html_message = message
            )

            message = render_to_string('admin_emails/new_user.html', {
                    'username': user.username,
                    'first_name': user.first_name,
                    'country': user.get_country_display(),
                    'user_type': 'Candidate' if hasattr(user, 'candidate') else 'Employer'                    
                })

            send_mail(
                'New User Sign Up for WeChatJobs',
                message,
                '"Wechat Jobs" <mail@wechatjobs.com>',
                ['nickrogerson11@gmail.com'],
                html_message = message
            )
        


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = SiteUser.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, SiteUser.DoesNotExist):
        user = None

    account_activation_token = TokenGenerator()

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

    # Log them out if they're already signed in
        logout(request)
        return redirect('activated')
    else:
        return HttpResponse('Activation link is invalid!')
    



# Password reset
class CustomPasswordResetView(PasswordResetView):
    form_class = PasswordResetEmail
    from_email = '"Password Reset" <password-reset@wechatjobs.com>'
    # '"WechatJobs" <mail@wechatjobs.com>',
    html_email_template_name = 'registration/password_reset_email.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = PasswordResetPass


class ChangePasswordInProfile(PasswordChangeView):
    template_name='jobsboard/profile-change-password.html'
    form_class = ChangePasswordInProfileForm



class ContactView(FormView):
    # template_name = 'jobsboard/contact/internal.html'
    form_class = ContactForm
    success_url = '/message-sent/'


    def get_form_class(self):
        if self.request.user.is_authenticated:
            return ContactForm
        else:
            return ExternalContactForm
	

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ['jobsboard/contact/internal.html']
        else:
            return ['jobsboard/contact/external.html']


    def post(self, request, *args, **kwargs):

        form = self.get_form()

        print(request.POST)

        if form.is_valid():
            print('FORM VALID!')

            # honeypot = form.cleaned_data['surname']

            # if honeypot:
            #     return HttpResponse('Bot detected!')

            # Applies to both groups
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            if request.user.is_authenticated:
                honeypot ='N/A for internal users'
                username = request.user.username
                name = request.user.first_name
                email = request.user.email
                wechat = request.user.wechat_id
                email_subject = 'New Message from Internal Contact Form'
                if hasattr(request.user, 'candidate'):
                    user_type = 'Candidate'
                    base_html = 'jobsboard/layouts/candidate-base.html'
                else:
                    user_type = 'Employer'
                    base_html = 'jobsboard/layouts/employer-base.html'
            else:
                honeypot = form.cleaned_data['surname']
                username = None
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                wechat = form.cleaned_data['wechat']
                user_type = None
                email_subject = 'New Message from External Contact Form'
                base_html = 'jobsboard/layouts/base.html'
              
            request.session['base_html'] = base_html

            message = render_to_string('admin_emails/contact_form.html', {
                'honeypot': honeypot,
                'username': username,
                'name': name,
                'email': email,
                'wechat': wechat,
                'user_type': user_type,
                'subject': subject,
                'message': message     
            })

            send_mail(
                email_subject,
                message,
                '"WechatJobs" <mail@wechatjobs.com>',
                ['nickrogerson11@gmail.com'],
                html_message = message
            )
        
            return redirect(self.success_url)
        
        else:
            print('FORM INVALID!')
            print(form.errors)
            return self.form_invalid(form)



class MessageSentSuccess(View):
    template_name='jobsboard/contact/sent-success.html'

# Move the session to context and delete the session variable
    def get(self, request):
        cxt = ''

        if 'base_html' in self.request.session:
            cxt = {'base_html': self.request.session['base_html']}
            del self.request.session['base_html']

        return render(request, self.template_name, context=cxt)




##################################################################
# These next classes available for both candidates and employers #
##################################################################



class DeleteProfilePic(LoginRequiredMixin,DeleteView):

    def delete(self, request, *args, **kwargs):

        try:
            request.user.profile_pic.delete(save=False)
            request.user.profile_pic.delete()
            request.user.save()
            return HttpResponse(json.dumps({'status': 'OK'}), content_type='application/json')
        except SiteUser.DoesNotExist:
                print('User does not exist!')


class MediaMixin:
    # Just creates an in-memory webp image
    def create_webp_image(self, tu, fname, profile_pic=False):
        image = Image.open(tu.file)
        # print(f'IMAGE SIZE: {image.size}')
        IMG_MAX_WIDTH = 300 if profile_pic else 1500
        width = IMG_MAX_WIDTH if image.size[0] > IMG_MAX_WIDTH else image.size[0]

    # Resize image if it's too big
        if width == IMG_MAX_WIDTH:
            wpercent = (width / float(image.size[0]))
        # Make it the same height as the width if it's the profile pic
            hsize = width if profile_pic else int((float(image.size[1]) * float(wpercent)))
            image = image.resize((width, hsize), Image.Resampling.LANCZOS)

    # Then convert it to a WEBP
        buf = BytesIO() 
        image.save(buf, 'WEBP')
        buf.seek(0)
        # image.close()
        return InMemoryUploadedFile(buf, 'ImageField',fname,'image/webp',sys.getsizeof(buf), None)






# Handles the status of removed job apps in the backend for both candidates and employers
# Job Applications are not deleteable by users
class DeleteJobApplication(LoginRequiredMixin,View):
    model = JobApplication

    def post(self, request, pk=None, *args, **kwargs):

        try:  
            print('Made it here in Delete Job App!')
            print(f'PK: {pk}')
            if pk:
                obj = self.model.objects.get(pk=pk)
                # Candidate
                if hasattr(request.user, 'candidate'):
                    if obj.status != 'rejected':
                        obj.status='revoked'
                    obj.candidate_removed=True
                else:
                # Employer
                # Only change the status to rejected when the employer deletes
                    if obj.status == 'revoked':
                        obj.employer_removed=True
                    else:
                # Can assume this was a rejection if the employer deletes it
                        obj.status='rejected'
                    obj.employer_removed=True
                obj.save()


            else:
                del_type = self.request.POST.get('deleteType')
                print(f'DEL TYPE: {del_type}')

                if del_type == 'revoke':
                    checked = self.request.POST.get('pks')
                    print(f'1st check: {checked}')
                    checked = json.loads(checked).split(',')
                    print(f'RAW1: {checked}')
                else:
                    print('Made it to else!')
                    checked = self.request.POST.getlist('pks')
                    print(checked)
                    # print(f'CHECKED: {list(map(int,checked))}')

                qs = self.model.objects.filter(pk__in=list(map(int,checked)))

                print(f'QS: {qs}')

            # If the candidate is revoking them
                if hasattr(request.user, 'candidate'):
                    if del_type == 'revoke':
                        qs.update(status='revoked')
                    else:
                    # if they're deleting them, then we can assume it's been revoked as well
                        qs.update(status='revoked', candidate_removed=True)
                else:
            # Otherwise, loop through and find the ones revoked and rejected, then update
                    for obj in qs:
                        print(obj.status)
                # Reject it as well if user hasn't revoked it
                        if obj.status != 'revoked':
                            obj.status='rejected'
                        obj.employer_removed=True
                        obj.save()
               

            g = ' was'     
            if 'checked' in locals():
                if len(checked) != 1: g = 's were'
            messages.success(request, f'The selected job application{g} successfully removed.')
        except Exception as e:
            print(e)
            messages.error(request, 'Operation failed!')

        if hasattr(request.user, 'candidate'):
            return redirect(reverse('job-apps'))
        else:
        # There are two pages that this can be called on so needs to redirect appropriately
        # To the previous page before the delete was called
            print(f"PATH: {request.META.get('HTTP_REFERER')}")
            return redirect(request.META.get('HTTP_REFERER'))
    



# Any user can update the app status for the sake of simplicity so long
# as they are associated with the app and have the correct permissions
class UpdateAppStatus(LoginRequiredMixin,View):
    model = JobApplication

    def post(self, request, *args, **kwargs):

        print(request.POST)

        # Convert all pks to a list of integers
        pks = [int(x) for x in json.loads(request.POST.get('pks')).split(',')]
        status = request.POST.get('status')

        print(f'PKS: {pks}')
        print(f'STATUS: {status}')

    # Make sure the user is associated with this app
    # And has the relevant permissions
        if hasattr(request.user, 'candidate'):
            print('is candidate')
            if status in ('pending','revoked'):
            
        # Change update if coming from a page with a Job pk
                if request.POST.get('jobPk'):
                    q = Q(job__pk__in=pks)
                else:
                    q = Q(pk__in=pks)
                
                q &= Q(candidate__user__pk=request.user.pk)
                
            else:
                raise PermissionDenied
        else:
            if status in ('pending','approved','rejected'):
                q = Q(pk__in=pks) & Q(job__employer__user__pk=request.user.pk)
            else:
                raise PermissionDenied

        try:
        # Update only the applications owned by this user as added security check
            # self.model.objects.filter(q).update(status=status)
            app = self.model.objects.get(q)
            app.status = status
            app.save()

        except self.model.DoesNotExist:
        # Then create a new application
            try:
                job = Job.objects.get(pk=pks[0])
                self.model.objects.create(candidate=self.request.user.candidate, job=job)
                print('Created new job app!')
                return JsonResponse({'success': True})
            except:
                print(e)
                return JsonResponse({'success': False})
            
        except Exception as e:
            print(e)
            return JsonResponse({'success': False,})

        return JsonResponse({'success': True})