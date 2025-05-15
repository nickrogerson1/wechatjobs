from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.views.generic import FormView, ListView
from django.views import View
from django.shortcuts import redirect, render, get_object_or_404

from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q
from django.db.models.functions import Now, Extract

from .models import *
from .forms import *
from .tasks import delete_temp_files
from .views import MediaMixin
from .views_frontend import EmployerProfileMixin
from .stripe import create_stripe_checkout_session

from urllib.parse import urlparse
from django_drf_filepond.models import TemporaryUpload
import json



# Makes sure they are logged in as an Employer
class UserHasPermission(LoginRequiredMixin,UserPassesTestMixin):

    permission_denied_message = 'You need to be an Employer to view this!'
    user_type = 'employer'

    def test_func(self):
        return hasattr(self.request.user, self.user_type)   
    





# Used by candidates and employers to view employers including themselves    
class ViewEmployerProfile(LoginRequiredMixin,View,EmployerProfileMixin):
    model = SiteUser
    template_name = 'jobsboard/employers/view-employer-profile.html'

    def get(self, request, *args, **kwargs):

        if 'pk' in self.kwargs:
            pk = self.kwargs['pk']
        else:
            pk = request.user.pk

        e = self.model.objects.get(id=pk)
        # from pprint import pprint
        # print(e.__dict__)

        cxt = {
            'profile_pic_url': e.profile_pic.url if e.profile_pic else None,
            'name': e.first_name,
            'email': e.email,
            'wechat_id': e.wechat_id,
            'phone_number': e.phone_number,
            'city': e.city,
            'country': e.country,
            'intro': e.intro,
            'job_types': e.job_types,
            'company_size': self.get_company_size(e.employer),
            'url_pk': pk,
            'website': e.employer.website
        }

        if hasattr(self.request.user, 'candidate'):
            cxt['candidate_view'] = True

            try:
            # Populates all the jobs associated with this employer in the DB
                jobs = Job.objects.filter(employer__user__pk=self.kwargs['pk'])
                cxt['jobs'] = jobs

            except Exception as e:
                print('No jobs associated with this Employer')
        
        return render(request, self.template_name, context=cxt)



class EditEmployerProfile(UserHasPermission,FormView,MediaMixin):
    model = SiteUser
    template_name = 'jobsboard/employers/edit-employer-profile.html'
    form_class = EmployerForm

    # Need to set the object before it gets the form kwargs
    def dispatch(self, request, *args, **kwargs):
        print(f'METHOD: {request.method}')
        self.user = get_object_or_404(self.model, id=self.request.user.id)
        return super().dispatch(request, *args, **kwargs)


    def post(self, request, *args, **kwargs):
    # Turn this of as the check is done in cleaned_form
        self.model._meta.get_field('wechat_id')._unique = False
        u = self.user
        form = self.get_form()

        profile_pic_changed = request.POST.get('profile_pic') or json.loads(request.POST.get('profile_pic_removed'))
        
        if not form.has_changed() and not profile_pic_changed:
            messages.info(request, "Your profile was NOT updated as you didn't change anything.")
            return self.form_invalid(form)

        if form.is_valid():
            print('FORM IS VALID!')

            try:

                if form.cleaned_data['website'] or form.cleaned_data['company_size']:
                    u.employer.website = form.cleaned_data['website']
                    u.employer.company_size = form.cleaned_data['company_size']
                    u.employer.save()


                u.intro = form.cleaned_data['intro']
                u.wechat_id = form.cleaned_data['wechat_id']
                u.phone_number = form.cleaned_data['phone_number']
                u.city = form.cleaned_data['city']
                u.country = form.cleaned_data['country']
                u.job_types = form.cleaned_data['job_types']
            
                upload_id = request.POST.get('profile_pic')
                
                if upload_id:
                    tu = TemporaryUpload.objects.get(upload_id=upload_id)
                    print(f'TU: {tu}')
                    fname, ftype = tu.upload_name.split('.')
                    fpath = f'{upload_id}-{fname}.webp'
                    webp_image = self.create_webp_image(tu, fpath, True)
                    u.profile_pic.delete()
                    u.profile_pic = webp_image

                u.save()
                print('Save complete')

            # Need to update the user object to make sure the 
            # profile pic data is passed
                request.user = u
            
            except self.model.DoesNotExist:
                print("User doesn't exist")
            finally:
            # Remove the file if there was one
                if upload_id:
                    # delete_temp_files.apply_async(args=[upload_id], countdown=10)
                    delete_temp_files.delay()

            messages.success(request, 'Your profile has been successfully updated.')
            return self.get(self, request, *args, **kwargs)
            # return render(request, self.template_name, context=self.get_context_data(form=form))
        
        else:
            print('FORM INVALID!')
            messages.error(request, 'Your profile was not updated! Please review the errors.')
            return self.form_invalid(form)
        

    
    def get_form_kwargs(self):
        """ Passes the user to the form class and sets initial data. """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user

    # Ensure initial form data is set to the current data of the instance
    # Makes sure that form changes are detected properly
        initial_data = {
            'website': self.user.employer.website,
            'company_size': self.user.employer.company_size,
            'intro': self.user.intro,
            'wechat_id': self.user.wechat_id,
            'phone_number': self.user.phone_number,
            'city': self.user.city,
            'country': self.user.country,
            'job_types': self.user.job_types
        }
        kwargs['initial'] = initial_data
        return kwargs






class CheckMaxPromotedJobsMixin:

    def check_max_promoted_jobs(self):

        active_promoted_jobs = PromotedJob.objects.filter(expiry_date__gte=timezone.now()).count()
        print(f'ACTIVE PROMOTED JOBS: {active_promoted_jobs}')

        if active_promoted_jobs >= settings.MAX_PROMOTED_JOBS:
            print('max_promoted_jobs_exceeded added!')
            return True
        else:
            return False




class JobPostView(UserHasPermission,FormView,CheckMaxPromotedJobsMixin):
    model = Job
    template_name = 'jobsboard/employers/post-job.html'
    form_class = JobPostForm
    success_url = reverse_lazy('manage-jobs')

    def get(self, request, *args, **kwargs):
        # Limit promoted jobs
        max_promoted_jobs_exceeded = self.check_max_promoted_jobs()
        self.extra_context = {
            'new_post': True,
            'max_promoted_jobs_exceeded': max_promoted_jobs_exceeded
        }
        return super(JobPostView, self).get(self, request, *args, **kwargs)


    def post(self, request, *args, **kwargs):

        print(request.POST)

        form = self.get_form()
        if form.is_valid():
            print('FORM VALID!')


            kwargs = {
                'job_title': form.cleaned_data['job_title'],
                'cities': [x.lower() for x in form.cleaned_data['cities']],
                'job_types': form.cleaned_data['job_types'],
                'subjects': [x.lower() for x in form.cleaned_data['subjects']],
                'job_description': form.cleaned_data['job_description'],
                'salary_lower_range': form.cleaned_data['salary_lower_range'],
                'salary_upper_range': form.cleaned_data['salary_upper_range'],
                'employment_type': form.cleaned_data['employment_type'],
                'experience': form.cleaned_data['experience'],
                'employer': request.user.employer,
                'accommodation': form.cleaned_data['accommodation'],
                'start_date': form.cleaned_data['start_date'],
                'contract_length': form.cleaned_data['contract_length'],
                'pay_settlement_date': form.cleaned_data['pay_settlement_date'],
                'scraped': False
                # '': form.cleaned_data[''],
            }


            if 'draft-post' in request.POST:
                kwargs['is_draft'] = True
                request.session['is_draft'] = True

            if 'free-post' in request.POST:
                kwargs['is_draft'] = False
                request.session['post_success'] = True

            job = self.model.objects.create(**kwargs)

            
            if 'paid-post' in request.POST:
                return redirect(create_stripe_checkout_session(request.user, job.pk))
            else:
                return redirect(self.success_url)
                # return self.get(self, request, *args, **kwargs)
        else:
            print('FORM INVALID!')
            print(form.errors)
            self.extra_context = {
                'max_promoted_jobs_exceeded': self.check_max_promoted_jobs()
            }
            messages.error(request, "Your job was not posted. Please review the errors.")
            return self.form_invalid(form)
        

    def get_form_kwargs(self):
        kwargs = super(JobPostView, self).get_form_kwargs()
        if 'draft-post' in self.request.POST:
            kwargs['draft_post'] = True
        return kwargs
        



class EditJobView(UserHasPermission,FormView,CheckMaxPromotedJobsMixin):
    model = Job
    template_name = 'jobsboard/employers/post-job.html'
    form_class = EditJobForm
    # Next View down
    success_url = reverse_lazy('manage-jobs')


    def get(self, request, pk, *args, **kwargs):

        print('GET reran!!')
       
        self.job = self.model.objects.select_related('promoted').get(pk=pk)
        is_draft = self.job.is_draft
        is_promoted = True if hasattr(self.job, 'promoted') else False

        self.extra_context = {
            'is_draft': is_draft,
            'is_promoted': is_promoted,
            'max_promoted_jobs_exceeded':  self.check_max_promoted_jobs()          
        }
        
        print(f'KWARGS: {kwargs}')
        return super(EditJobView, self).get(self, request, pk, *args, **kwargs)


    def post(self, request, pk, *args, **kwargs):
        # Disable the model's unique check and handover to the cleaner
        self.model._meta.get_field('job_description')._unique = False
        self.job = self.model.objects.get(pk=pk)

        form = self.get_form()

        print(request.POST)

        # Only run change check for drafts and updated posts
        if not form.has_changed() and ('draft-post' in request.POST or 'post-updated' in request.POST):
            self.extra_context = {
                'is_draft': self.job.is_draft,
                'is_promoted': True if hasattr(self.job, 'promoted') else False,
                'max_promoted_jobs_exceeded':  self.check_max_promoted_jobs()    
            }
            messages.info(request, "Your job was NOT updated as you didn't change anything.")
            return self.form_invalid(form)

        if form.is_valid():
            print('FORM VALID!')

            kwargs = {
                'time_updated': timezone.now(),
                'job_title': form.cleaned_data['job_title'],
                'cities': [x.lower() for x in form.cleaned_data['cities']],
                # 'job_types': [x.lower() for x in form.cleaned_data['job_types']],
                'job_types': form.cleaned_data['job_types'],
                'subjects': [x.lower() for x in form.cleaned_data['subjects']],
                'job_description': form.cleaned_data['job_description'],
                'salary_lower_range': form.cleaned_data['salary_lower_range'],
                'salary_upper_range': form.cleaned_data['salary_upper_range'],
                'employment_type': form.cleaned_data['employment_type'],
                'experience': form.cleaned_data['experience'],
                'employer': request.user.employer,
                'accommodation': form.cleaned_data['accommodation'],
                'start_date': form.cleaned_data['start_date'],
                'contract_length': form.cleaned_data['contract_length'],
                'pay_settlement_date': form.cleaned_data['pay_settlement_date'],
                # '': form.cleaned_data[''],
            }


        

            if 'draft-post' in request.POST or 'unpublish' in request.POST:
                kwargs['is_draft'] = True
                request.session['is_draft'] = True

            if 'free-post' in request.POST:
                kwargs['is_draft'] = False
                kwargs['time_created'] = timezone.now()
                request.session['post_success'] = True

            if 'post-updated' in request.POST:
                request.session['post_updated'] = True

            if 'remove-promoted' in request.POST:
                self.job.promoted.delete()
                kwargs['is_draft'] = True
                request.session['promoted_removed'] = True

            if 'paid-post' in request.POST:
                kwargs['is_draft'] = False

            self.model.objects.filter(pk=pk).update(**kwargs)

                
            if 'paid-post' in request.POST:
                return redirect(create_stripe_checkout_session(request.user, pk))
            else:
                return redirect(self.success_url)


        else:
            print('FORM INVALID!')
            # print(form.errors)
            print(form.errors.as_json())
            self.extra_context = {
                'is_draft': self.job.is_draft,
                'is_promoted': True if hasattr(self.job, 'promoted') else False,
                'max_promoted_jobs_exceeded':  self.check_max_promoted_jobs()          
                 
            }
            if 'draft-post' in request.POST:
                text = 'updated'  
            elif 'unpublish' in request.POST:     
                text = 'unpublished'
            else:
                text = 'posted'
            messages.error(request, f'Your job was not {text}. Please review the errors.')
            return self.form_invalid(form)
        

    def get_form_kwargs(self):
        kwargs = super(EditJobView, self).get_form_kwargs()
        kwargs['job'] = self.job
        if 'draft-post' in self.request.POST:
            kwargs['draft_post'] = True
        return kwargs





class ManageJobs(UserHasPermission,ListView,CheckMaxPromotedJobsMixin):
    model = Job
    template_name = 'jobsboard/employers/manage-jobs.html'
    context_object_name = 'jobs'
    paginate_by = 10

# Counts how many applicants that are for each job which the employer hasn't removed
    def get_context_data(self, **kwargs):
        context = super(ManageJobs, self).get_context_data(**kwargs)

    # Check if there are enough promoted job slots
        context['max_promoted_jobs_exceeded'] = self.check_max_promoted_jobs()

        # Check if came from PostJob
        if 'HTTP_REFERER' in self.request.META:
            url = urlparse(self.request.META['HTTP_REFERER']).path

            if any(url.startswith(x) for x in ('/post-job/', '/edit-job/')):
                if 'is_draft' in self.request.session:
                    del self.request.session['is_draft']
                    context['is_draft'] = True
                if 'post_success' in self.request.session:
                    del self.request.session['post_success']
                    context['job_post_success'] = True
                if 'post_updated' in self.request.session:
                    del self.request.session['post_updated']
                    context['job_post_updated'] = True
                if 'promoted_removed' in self.request.session:
                    print('Promote removed fired!')
                    del self.request.session['promoted_removed']
                    context['promoted_removed'] = True

        return context


    def get_queryset(self):
        if self.request.GET.get('order') == 'A':
            order = ''
            self.extra_context = {'order': 'A'}
        else: 
            order = '-'

        return (self.model.objects.select_related('promoted')
            .filter(employer=self.request.user.employer)
            .annotate(app_count=Count('applications', filter=Q(applications__employer_removed=False)))
            .annotate(expiry_date=Extract(F('promoted__expiry_date') - Now(), 'epoch'))
            .order_by(f'{order}time_updated'))




# Just starts a Stripe Checkout Session when they click it
class PromoteJob(UserHasPermission,CheckMaxPromotedJobsMixin,View):

    def get(self, request, pk):
    # Do extra check in case they somehow bypassed it
        if self.check_max_promoted_jobs:
            return redirect(create_stripe_checkout_session(request.user, pk))
        else:
            raise PermissionDenied
    


class DeleteJob(UserHasPermission,View):

    def post(self, request, pk=None, *args, **kwargs):

        try:
            if pk:
                Job.objects.get(pk=pk).delete()
            else:
                print('Made it here!')
                checked = self.request.POST.getlist('checks')
                Job.objects.filter(pk__in=checked, 
        #Make sure they haven't messed about with the HTML and it's theirs
        #Need to double check this!!! Can only get candidate_id
                employer_id=request.user.employer.id 
                ).delete()

            g = ' was'     
            if 'checked' in locals():
                if len(checked) != 1: g = 's were'
            messages.success(request, f'Your selected job{g} successfully removed.')
        except Exception as e:
            print(e)
            messages.error(request, 'Operation failed!')

        return redirect(reverse('manage-jobs'))
    








# Pulls off all the applications for ALL jobs
class ViewApplications(UserHasPermission,ListView):
    model = JobApplication
    template_name = 'jobsboard/employers/view-applications.html'
    paginate_by = 10

    def get_queryset(self):
        if self.request.GET.get('order') == 'A':
            order = ''
            self.extra_context = {'order': 'A'}
        else: 
            order = '-'
        return self.model.objects.filter(job__employer=self.request.user.employer, employer_removed=False).order_by(f'{order}time_created')


# Pulls off all the applications for A SPECIFIC job
class ViewApplicantsForJob(UserHasPermission,ListView):
    model = JobApplication
    template_name = 'jobsboard/employers/view-applications.html'
    paginate_by = 10

    def get_queryset(self):

        if self.request.GET.get('order') == 'A':
            order = ''
            self.extra_context['order'] = 'A'
        else: 
            order = '-'

        kwargs = {
            'job__employer': self.request.user.employer, #auth check
            'job__pk': self.kwargs['pk'],
            'employer_removed': False
        }

        return self.model.objects.select_related('candidate__user').filter(**kwargs).order_by(f'{order}time_created')
    


    def get_context_data(self, **kwargs):
        cxt = super().get_context_data(**kwargs)

        try:
            job = Job.objects.get(pk=self.kwargs['pk'])

            if job.job_title:
                title = job.job_title[:60] + ('...' if len(job.job_title) >= 60 else '')
            else:
                title = job.job_description[:60] + ('...' if len(job.job_description) >= 60 else '')

            cxt['title'] = title

        except Job.DoesNotExist:
            print("Job doesn't exist" )
        except Exception as e:
            print(e)

        cxt['job_pk'] = self.kwargs['pk']
        
        return cxt