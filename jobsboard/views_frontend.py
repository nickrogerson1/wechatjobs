from django.views.generic import ListView
from django.views import View

from django.db.models import F, Q, When, Case, Count, Value, OuterRef, IntegerField
from django.db.models.functions import Now, JSONObject
from django.db.models.lookups import GreaterThan
from django.db.models.expressions import CombinedExpression

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, SearchHeadline
from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.http import Http404

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import resolve, reverse_lazy
from hitcount.views import HitCountDetailView

from .models import *
from .forms import *
import datetime
from urllib.parse import urlparse


# Two Views: Homepage and JobDetailView 
# The two most visited pages
# Plus the UpdateData endpoint



class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

class UpdateData(SuperUserRequiredMixin,View):
    # success_url = reverse_lazy('add')

    def post(self, request, *args, **kwargs):

        parsed_url = urlparse(request.META.get('HTTP_REFERER', 'No Referrer'))
        referring_path = parsed_url.path
        print(f'PATH: {referring_path}')

        # 1) Check for new WX_Alias
        for k in request.POST.dict():
            if k.startswith('wx-alias-'):
                wxid = k[9:]
                wx_alias = request.POST.get(k)
                print(wxid)
                print(wx_alias)
                wxid_alias = WxidAlias.objects.filter(wxid=wxid)
                if wx_alias not in wxid_alias[0].wx_alias:
                    wxid_alias.update(wx_alias=CombinedExpression(F('wx_alias'), '||', Value([wx_alias])))
                else:
                    print('WX_ALIAS was a dupe so not added!')

        # 2) Add timestamps to WX_Alias
        (WxidAlias.objects.filter(wxid__in=request.POST.getlist('wxid'))
        .update(wx_alias_requests_sent_by_me=CombinedExpression(F('wx_alias_requests_sent_by_me'), '||', Value([timezone.now()]))))

        return redirect(referring_path)
        # return render(request, 'jobsboard/home.html')




class SearchQuerysetMixin:
    # Returns a queryset based on any search parameters
    def get_search_queryset(self,queryset):

        query = Q()
        if 'options' in self.request.GET:
            if 'has_wechat' in self.request.GET['options']:
                query &= Q(~Q(wxid_alias__wx_alias__len=0))
            if 'is_employer' in self.request.GET['options']:
                query &= ~Q(employer=None)
            if 'no_wechat' in self.request.GET['options'] or resolve(self.request.path_info).url_name == 'add':
                query &= Q(wxid_alias__wx_alias__len=0)

        if 'sub' in self.request.GET:
            query &= Q(subjects__contains=[self.request.GET.get('sub')])
        if 'loc' in self.request.GET:
            query &= Q(cities__contains=[self.request.GET.get('loc')])
        if 'type' in self.request.GET:
            query &= Q(job_types__contains=[self.request.GET.get('type')])
        if 'wxid' in self.request.GET:
            query &= Q(wxid_alias__wxid=self.request.GET.get('wxid'))
        if 'group' in self.request.GET:
            query &= Q(group__group_id=self.request.GET.get('group'))

        # print(f'QUERY: {query}')

        # Finally work out the query
        return queryset.filter(query) if len(query) else queryset
    



class GetAppStatusAndFavesMixin:
 # Get app_status and faves for signed in **candidates**
    def include_app_status_and_faves(self,qs):
        status = (JobApplication.objects.filter(candidate__user=self.request.user,job=OuterRef('pk'))
        .values(json=JSONObject(status='status', employer_removed='employer_removed')))
        return (qs.annotate(app=ArraySubquery(status))
                .annotate(fave=Case(When(favourites__candidate__user=self.request.user, then=True))))



class Homepage(ListView,SearchQuerysetMixin,GetAppStatusAndFavesMixin):
    template_name = 'jobsboard/home.html'
    model = Job


    def get_paginate_by(self, queryset):
        if self.request.user.is_superuser:
            if resolve(self.request.path_info).url_name == 'home':
                return 300
            else:
        # Don't paginate for "add"
                return 0
        else:
        # Pagination for regular users
            return 25



    def get_context_data(self, **kwargs):
        context = super(Homepage, self).get_context_data(**kwargs)

        if self.request.user.is_superuser:

            unique_wxids_with_alias = self.queryset.filter(wxid_alias__wx_alias__len__gt=0).values_list('wxid_alias__wxid').distinct().count()
            total_wxids = self.queryset.exclude(wxid_alias__wxid=None).values_list('wxid_alias__wxid').distinct().count()

            # The amount of (non-unique) jobs with wxids
            jobs_with_wx_alias = self.queryset.filter(wxid_alias__wx_alias__len__gt=0).values_list('wxid_alias__wxid').count()
            total_jobs_exc_employers = self.queryset.exclude(wxid_alias__wxid=None).values_list('wxid_alias__wxid').count()


            poster_count = (self.queryset.exclude(wxid_alias__wxid=None)
                        .values('wxid_alias__wxid','wxid_alias__wx_alias')
                        .annotate(c=Count('wxid_alias__wxid')).order_by('-c')[:15])

            context['poster_count'] = poster_count
            context['total_wxids'] = total_wxids
            context['wxids_with_alias'] = unique_wxids_with_alias 
            context['jobs_with_wx_alias'] = jobs_with_wx_alias
            context['total_jobs_exc_employers'] = total_jobs_exc_employers
            if self.queryset:
                context['unique_percent'] = round((unique_wxids_with_alias / total_wxids) * 100, 2)
                context['total_percent'] = round((jobs_with_wx_alias / total_jobs_exc_employers) * 100, 2)

            context['group_order'] = (self.queryset.filter(Q(wxid_alias__wx_alias__len=0)).values('group__group_name', 'group__group_id')
                                        .annotate(c=Count('group__group_id')).order_by('-c'))[:15]
            
        # Create Javascript arrays of arrays for dynamic search box
        groups = list(self.queryset.filter(~Q(group=None)).values_list('group__group_name', 'group__group_id').distinct())
        context['groups']= [list(e) for e in groups if e[0]]

        posters = list(self.queryset.filter(~Q(wxid_alias=None)).values_list('wx_handle__handle', 'wxid_alias__wxid').distinct())
        context['posters'] = [list(e) for e in posters if e[0]]

        # context['jobs_last_day'] = self.queryset.filter(time_created__gt = timezone.now() - timezone.timedelta(days=1)).count()
        context['jobs_last_day'] = self.queryset.filter(GreaterThan(F('time_created'), Now() - timezone.timedelta(days=1))).count()
        
        context['total_count'] = self.queryset.count()
        # Only get the fields needed to populate the form dropdowns
        context['form'] = SearchJobs(self.queryset.only('job_types', 'cities', 'subjects'))


        # Build the query
        if self.request.GET:
            # Parameters added to the URLs in the on page links
            search_query = ''

            def search_text(prep):
                return f'  <span class="pxp-text-light">{prep}</span>' if search_query else f'{prep}</span>'

            if 'q' in self.request.GET:
                search_query += f"for</span> {self.request.GET.get('q').title()}"

            if 'loc' in self.request.GET:
                search_query += f"{search_text('in')} {self.request.GET.get('loc').capitalize()}"

            if 'type' in self.request.GET:
                search_query += f"{search_text('for')} {self.request.GET.get('type').title()}"

            if 'sub' in self.request.GET:
                search_query += f"{search_text('for')} {self.request.GET.get('sub').title()}"

            if 'wxid' in self.request.GET:
                wxid = self.queryset.filter(wxid_alias__wxid=self.request.GET.get('wxid'))
                wxid_name = wxid[0].wx_handle if len(wxid) else 'NO SUCH POSTER'
                search_query += f"{search_text('posted by')} {wxid_name}"

            if 'group' in self.request.GET:
                group = self.queryset.filter(group__group_id=self.request.GET.get('group'))
                group_name = group[0].group.group_name if len(group) else 'NO SUCH GROUP'
                search_query += f"{search_text('for')} {group_name}"

            
            if 'options' in self.request.GET:
                if 'has_wechat' in self.request.GET['options']:
                    search_query +=  f"{' ' if search_query else ''} with a Wechat ID"
                if 'no_wechat' in self.request.GET['options']:
                    search_query +=  f"{' ' if search_query else ''} without a Wechat ID"
                if 'is_employer' in self.request.GET['options']:
                    search_query +=  f"{' ' if search_query else ''} who are registered with the site"

        # Parameters for newest / oldest |&order=O
            q = re.sub(r'page=\d+&?|&?order=[ON]','',self.request.GET.urlencode())
            context['query_param1'] = '?' + q if q else ''
        # Parameters for pagination
            context['query_param2'] = re.sub(r'page=\d+&?','',self.request.GET.urlencode())
        # Readable text for user
            context['search_query'] = search_query

        return context



    
    def get_queryset(self):

    # Check for the page it came from
        if resolve(self.request.path_info).url_name == 'home' or resolve(self.request.path_info).url_name == 'add':
        # Get related objects to avoid extra SQL queries in template
            queryset = self.model.objects.select_related('employer__user','group','wx_handle','wxid_alias','promoted').filter(is_job=True,is_draft=False)
            # This is used as a reference for later context queries
            self.queryset = self.model.objects.filter(is_job=True)
        
    # Admin urls
        elif resolve(self.request.path_info).url_name == 'reject':
            queryset = self.model.objects.select_related('employer__user','group','wx_handle','wxid_alias').filter(is_job=False)
            self.queryset = self.model.objects.filter(is_job=False)
        else: # Then must be all of them
            queryset = self.model.objects.select_related('employer__user','group','wx_handle','wxid_alias').all()
            self.queryset = self.model.objects.all()


   
         # If it's the homepage and there are NO query parameters, then return it with promoted jobs
        if resolve(self.request.path_info).url_name == 'home' and not self.request.GET:
            qs = (queryset.annotate(active_promotion=Case(
                When(GreaterThan(F('promoted__expiry_date'), timezone.now()), then=True))))
        
            # Candidates also need faves and app statuses
            if hasattr(self.request.user, 'candidate'):
                qs = self.include_app_status_and_faves(qs)
            
            return qs.order_by('active_promotion', '-time_created')


        # Add is an admin page, so block non-Admin users
        if resolve(self.request.path_info).url_name == 'add' and 'q' not in self.request.GET:
            if self.request.user.is_superuser:
                 return self.get_wxids_to_add(queryset)
            else:
                raise PermissionDenied
        
        # Admin page to isolate requested
        if resolve(self.request.path_info).url_name == 'requested' and 'q' not in self.request.GET:
            if self.request.user.is_superuser:
                jobs_qs = queryset.filter(
                    wxid_alias__wx_alias_request_by_user__isnull=False,
                    wxid_alias__wx_alias_requests_sent_by_me__len=0,
                    wxid_alias__wx_alias__len=0,
                    wxid_alias__notes__exact=''
                ).distinct('wxid_alias')
            
                self.extra_context = {
                    'requested_ids': len(jobs_qs)
                }
                return jobs_qs
            else:
                raise PermissionDenied
            

        # Build the search query
        qs = self.get_search_queryset(queryset)

    # Stop here if no kw search query and check the order
        if 'q' not in self.request.GET:
            v = '-'
            if 'order' in self.request.GET and 'O' in self.request.GET['order']:
                v = ''
            # print(f'V: {v}')

            # Candidates also need faves and app statuses
            if hasattr(self.request.user, 'candidate'):
                qs = self.include_app_status_and_faves(qs)

            return qs.order_by(f'{v}time_created')


    # Else this was a search
        query = self.request.GET.get('q')
        print(f'KW SEARCH: {query}')

        # Default ordering is by score
        order = ('-score', '-time_created')

        # Change if they request an ordering by date
        if 'order' in self.request.GET:
            if 'O' in self.request.GET['order']:
                order = ('time_created','-score',)
            elif 'N' in self.request.GET['order']:
                order = ('-time_created','-score',)
        
        vector = SearchVector('job_description')
        q = SearchQuery(query, search_type='phrase')
        qs = qs.annotate(score=SearchRank(vector, query),
                    keyword_search_desc=SearchHeadline(
                        'job_description',
                        q,
                        start_sel='<span style="color:red;">',
                        stop_sel="</span>",
                        min_words=50,
                        max_words=100
                    ),
                ).filter(score__gte=0.01)
        
        if hasattr(self.request.user, 'candidate'):
            qs = self.include_app_status_and_faves(qs)
        
        return qs.order_by(*order)
    



    def get_wxids_to_add(self,qs):
        # Default time between re-requesting WX_ALIAS
        days = 45
        # Can override this by adding ?days=NUM in URL
        if 'days' in self.request.GET:
            days = int(self.request.GET.get('days'))

        print(f'DAYS: {days}')

        vals = (qs.filter(wxid_alias__wx_alias__len=0)
                .values_list('group__group_id','wxid_alias__wxid',
                'pk','wxid_alias__wx_alias_requests_sent_by_me'))
        

        # Steps
        # 1st: Get rid of elements that have had requests in the last X days and sort into groups
        # 2nd: Delete duplicate wxids, keeping the ones in the largest groups and removing those in the smallest
        # 3rd: Build the queryset with when conditionals to make the DB do the work
        # 4th: Add additional infomation for UI purposes

        groups_d = {}
        wxids = []
        # k = 'group__group_id'
        # v1 ='wxid_alias__wxid'
        # v2 = 'job_pk'
        # v3 = 'wxid_alias__wx_alias_requests_sent_by_me'
        # Sorts them into their respective groups
        for k,v1,v2,v3 in vals:
        # Skip if any dates less than a week old
            if any(date > timezone.now() - datetime.timedelta(days=days) for date in v3):
                continue
            # Append unique wxids
            if v1 not in wxids:
                wxids.append(v1)
            # Append unique groups
            if k not in groups_d:
                groups_d[k] = [(v1,v2)]
            else:
                groups_d[k].append((v1,v2))

        def sort_groups(group_dict):
            return {k: v for k, v in sorted(group_dict.items(), key=lambda item: len(item[1]), reverse=True)}
  
        sorted_groups = sort_groups(groups_d)
        # print(f'LEN SORTED G1: {len(sorted_groups)}')

        # Store the values that pass
        groups_copy = {}
        
        # tup = (wxid, job_pk)
        # Loop over the groups from largest to smallest
        for group_id in sorted_groups:
            this_group = sorted_groups[group_id]
            new_group = []
            for wxid,job_pk in this_group:
                if wxid in wxids:
            # Remove this wxid from the wxids list
                    wxids.pop(wxids.index(wxid))
            # Then add to new group
                    new_group.append((wxid, job_pk))
            # Then add thre group to the groups_copy
            # So long as it still has any values
            if new_group:
                groups_copy[group_id] = new_group

        # Re-order the groups again
        sorted_groups = sort_groups(groups_copy)
        # print(f'LEN SORTED G2: {len(sorted_groups)}')
        # print(f'SORTED G2: {sorted_groups}')

        _whens = []
        group_vals = []

        # Build the _whens conditions and keep track of the groups
        for i,group in enumerate(sorted_groups.values()):
            for tup in group:
                # print(f'TUP: {tup}')
                wxid,job_pk = tup
                _whens.append(When(pk=job_pk, then=len(_whens)))
                group_vals.append((i,len(group)))
        
        # Create the new queryset with the _whens now in place
        queryset = (qs.filter(wxid_alias__wx_alias__len=0)
            .annotate(index=Case(*_whens, output_field=IntegerField()))
            .filter(~Q(index=None)).order_by('index'))
        
        # Add in extra information about this query to make it easier to read client side
        for i,q in enumerate(queryset):
            j,length = group_vals[i]
            alt = '<span style="color:red";>***</span>' if j % 2 else '<span style="color:green";>---</span>'
            q.score = f'{alt} {length} {alt}'

        self.extra_context = {
            'total_without_ids': len(queryset), 
            'groups_without_alias': len(sorted_groups),
            'days': days  
        }
        return queryset






class EmployerProfileMixin:

    def get_company_size(self, employer):
        company_size = ''
        employer = employer if employer else self.request.user.employer

        if employer.company_size:
            for t in NUM_EMPLOYEES:
                if t[0] == int(employer.company_size):
                    company_size = t[1]
                    break
        return company_size
    



class JobDetailView(HitCountDetailView,SearchQuerysetMixin,
                    EmployerProfileMixin,GetAppStatusAndFavesMixin):
    model = Job
    template_name = 'jobsboard/job-detail.html'
    context_object_name = 'job'
    count_hit = True 


    def get_context_data(self, **kwargs):
        context = super(JobDetailView, self).get_context_data(**kwargs)


    # This generates a list of related jobs
    # First checks to see if there was a search (if any)
    # Then subjects, job_types, then cities
        related = []
        related_max_length = 4

        qs = (self.model.objects.select_related('employer__user','wx_handle','wxid_alias').filter(is_job=True)
                         .exclude(pk=self.kwargs['pk']).order_by('-time_updated'))


        if self.request.GET:
            search_qs = self.get_search_queryset(qs)
            # print(f'QS: {search_qs}')
            # print(f'GET: {self.request.GET}')

            for job in search_qs:
                if len(related) < related_max_length:
                    related.append(job)


        subjects = self.object.subjects
        job_types = self.object.job_types
        cities = self.object.cities
       
        if len(related) < related_max_length and subjects:
            for job in qs:
                # print(f'JOB>SUBJECTS: {job.subjects}')
                if any(w in subjects for w in job.subjects):
                    related.append(job)
                    if len(related) >= related_max_length:
                        break
        # Then related job_types
        if len(related) < related_max_length:
            for job in qs:
                # print(f'JOB>JOBTYPES: {job.job_types}')
                if any(w in job_types for w in job.job_types):
                    related.append(job)
                    if len(related) >= related_max_length:
                        break
        # Finally related cities
        if len(related) < related_max_length:
            for job in qs:
                # print(f'JOB>CITIES: {job.cities}')
                if any(w in cities for w in job.cities):
                    related.append(job)
                    if len(related) >= related_max_length:
                        break

        context['related_jobs'] = related

        # print(self.object.__dict__)

    # Get company size for registered employers
        if hasattr(self.object, 'employer') and self.object.employer:
            context['company_size'] = self.get_company_size(self.object.employer)
         
        # print(self.object.__dict__)

        job_attributes = (
                    ('Years Experience', self.object.get_experience_display() if self.object.experience else False, True), 
                    ('Employment Type', self.object.get_employment_type_display() if self.object.employment_type else False, True),
                    ('Salary Lower Range', f'{self.object.salary_lower_range} RMB' if self.object.salary_lower_range else False, True),
                    ('Salary Upper Range', f'{self.object.salary_upper_range} RMB' if self.object.salary_upper_range else False, True),
                    ('Accommodation', self.object.get_accommodation_display() if self.object.accommodation else False, True),
                    ('Start Date', self.object.start_date),
                    ('Contract Length', self.object.get_contract_length_display() if self.object.contract_length else False, True),
                    ('Pay Settlement Date', self.object.get_pay_settlement_date_display() if self.object.pay_settlement_date else False, True),
                )
        
        job_details = []
        
        for a in job_attributes:
            if a[1]:
                if len(a) == 3:
                    print(a)
                    vals = (a[0], a[1][:a[1].rfind(' ')])
                    job_details.append(vals)
                else:
                    job_details.append(a)

        context['job_details'] = job_details

        return context
    


    def get_object(self):

        pk = self.kwargs['pk']

        if pk is None:
            raise Http404

        qs = self.model.objects.select_related('employer__user','wx_handle','wxid_alias','promoted')

        if hasattr(self.request.user, 'candidate'):
            qs = self.include_app_status_and_faves(qs)
        
        try:
        # Get the single item from the filtered queryset
            obj = qs.get(pk=pk)
        except self.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": self.queryset.model._meta.verbose_name}
            )
        
        return obj