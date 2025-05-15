from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group
from django.forms import BaseInlineFormSet
from .models import *



class UserAdminMixin(admin.ModelAdmin):

    @admin.display(description='Username')
    def username(self, obj):
        return obj.user.username
    
    @admin.display(description='First Name')
    def first_name(self, obj):
        return obj.user.first_name
    
    @admin.display(description='Last Name')
    def last_name(self, obj):
        return obj.user.last_name
    
    @admin.display(description='Email')
    def email(self, obj):
        return obj.user.email
    
    @admin.display(description='Wechat ID')
    def wechat(self, obj):
        return obj.user.wechat_id
    
    @admin.display(description='Phone Number')
    def phone_no(self, obj):
        return obj.user.phone_number
    
    @admin.display(description='City')
    def city(self, obj):
        return obj.user.city
    
    @admin.display(description='Country')
    def country(self, obj):
        return obj.user.get_country_display()
    
    @admin.display(description='Intro')
    def intro(self, obj):
        return obj.user.intro
    
    @admin.display(description='Job Types')
    def job_types(self, obj):
        return obj.user.job_types
    
    @admin.display(description='last_login')
    def last_login(self, obj):
        return obj.user.last_login
    
    @admin.display(description='is_staff')
    def is_staff(self, obj):
        return obj.user.is_staff
    
    @admin.display(description='is_active')
    def is_active(self, obj):
        return obj.user.is_active
    
    @admin.display(description='date_joined')
    def date_joined(self, obj):
        return obj.user.date_joined



BASE_USER_FIELDSETS = [
        (_("Important Dates"), {"fields": ("last_login", "date_joined")}),
    ]

BASE_READONLY_FIELDS = ['wechat', 'phone_no', 'city', 'country', 'intro', 'job_types', 'first_name','last_name', 'email', 'last_login', 'date_joined']



# Removes images from S3 deleted in the admin
class ChildFormSet(BaseInlineFormSet):
    def delete_existing(self, obj, commit=True):
        if hasattr(obj, 'image'):
            obj.image.delete(save=False)
        else:
            obj.video.delete(save=False)
        obj.delete()



class CandidateImageInline(admin.TabularInline):
    model = CandidateImage
    extra = 0
    formset = ChildFormSet

class CandidateVideoInline(admin.TabularInline):
    model = CandidateVideo
    extra = 0
    formset = ChildFormSet


class FavouriteJobsInline(admin.TabularInline):
    model = FavouriteJob
    extra = 0


class JobApplicationsInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    



class JobOfferedInline(admin.TabularInline):
    model = Job
    extra = 0
    show_change_link = True
    fields = ['job_title']
    readonly_fields = ['job_title']




class CandidateAdmin(UserAdminMixin):
    list_display = ('user', 'sex', 'city', 'country', 'dob',)
    list_per_page = 25
    # fields = ['user', '_first_name', 'country', 'dob']
    # add_fieldsets =  UserAdmin.add_fieldsets + ((_("Personal info"), {"fields": ['user']}),)

    fieldsets = [
                ['Candidate Profile', {'fields': ('user', 'first_name', 'email', 'wechat', 'phone_no', '_sex', 'city','country', 'dob', 'job_types', 'cv', 'intro' )}]
    ] + BASE_USER_FIELDSETS

    readonly_fields =  BASE_READONLY_FIELDS + ['_sex']


    inlines = [CandidateImageInline, CandidateVideoInline, FavouriteJobsInline, JobApplicationsInline]


    @admin.display(description='Sex')
    def _sex(self, obj):
        # print(obj.__dict__)
        if obj.sex:
            return 'Male'
        return 'Female'



class EmployerAdmin(UserAdminMixin):
    list_display = ('user', 'country')
    list_per_page = 25

    fieldsets = [
                ['Employer Profile', {'fields': ('user','first_name', 'email', 'wechat', 'phone_no', 'website', 'city', 'country', 'job_types', 'intro')}]
    ] + BASE_USER_FIELDSETS

    readonly_fields = BASE_READONLY_FIELDS

    inlines = [JobOfferedInline]



class JobsAdmin(admin.ModelAdmin):
    list_display = ('time_created', 'wxid', 'wx_alias', 'group', 'cities', 'job_types')
    list_per_page = 25
    fields = [field.name for field in Job._meta.get_fields() if field.name not in  ['id', 'favourites', 'applications', 'promoted']] + ['fav_count', 'app_count', '_promoted']
    # fields.insert(3,'wx_alias')
    fields[3:3] = ['wx_alias', 'wxid']
    readonly_fields = ['time_created', 'time_updated', 'fav_count', 'app_count','wx_alias', 'wxid', '_promoted']

    inlines = [FavouriteJobsInline, JobApplicationsInline]

    @admin.display(description='WX Alias')
    def wx_alias(self, obj):
        if obj.wxid_alias:
            return ', '.join(obj.wxid_alias.wx_alias)
        return None
    
    @admin.display(description='WXID')
    def wxid(self, obj):
        if obj.wxid_alias:
            return obj.wxid_alias.wxid
        return None

    @admin.display(description='Favourited')
    def fav_count(self, obj):
        times = 'time' if obj.favourites.count() == 1 else 'times'
        return f'{obj.favourites.count()} {times}'
    
    @admin.display(description='Total Apps')
    def app_count(self, obj):
        p = 'app'
        times = p if obj.applications.count() == 1 else p + 's'
        return f'{obj.applications.count()} {times}'
    
    @admin.display(description='Promoted')
    def _promoted(self, obj):
        return mark_safe(f'<a href="/admin/jobsboard/promotedjob/{obj.promoted.pk}/change/">PromotedJob: {obj.promoted}</a>')




class UserAdmin(UserAdmin):
    list_display = ('username','_user_type','email','is_active','last_login')
    list_per_page = 25
    # fields = ('username','first_name', 'last_name', 'email', 'user_type')
    readonly_fields = ['_user_type']

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal Info"), {"fields": ("first_name", "email", 'wechat_id', 'phone_number', 'country', '_user_type', 'profile_pic' )}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important Dates"), {"fields": ("last_login", "date_joined")}),
    )

    @admin.display(description='User Profile')
    def _user_type(self, obj):
        if hasattr(obj,"candidate"):
            return mark_safe(f'<a href="/admin/jobsboard/candidate/{obj.candidate.id}/change/">Candidate: {obj.username}</a>')
        # It's an employer
        else:
            return mark_safe(f'<a href="/admin/jobsboard/employer/{obj.employer.id}/change/">Employer: {obj.employer}</a>')
            


class WxidAliasAdmin(admin.ModelAdmin):
    list_display = ('wxid', 'wx_alias', 'wx_alias_request_by_user', 'wx_alias_requests_sent_by_me','notes')
    list_per_page = 25

    inlines = [JobOfferedInline]



class GroupIdAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'group_name')
    list_per_page = 25

class HandleAdmin(admin.ModelAdmin):
    list_display = ('wxid', 'group', 'handle')
    list_per_page = 25



class PromotedJobAdmin(admin.ModelAdmin):
    list_display = ('time_created', 'expiry_date', 'amount', 'currency')
    list_per_page = 25
    fields = ['time_created', 'expiry_date', 'amount', 'currency', 'payment_method', 'job', '_user' ]
    readonly_fields = ['time_created', '_user' ]
   
    @admin.display(description='User')
    def _user(self, obj):
        print(f'OBJ: {obj}')
        return mark_safe(f'<a href="/admin/jobsboard/siteuser/{obj.job.employer.user.pk}/change/">{obj.job.employer.user}</a>')



class AdMessageAdmin(admin.ModelAdmin):
    list_display = fields = ['text']
    list_per_page = 25


admin.site.register(Job,JobsAdmin)
admin.site.register(SiteUser,UserAdmin)
admin.site.register(Candidate,CandidateAdmin)
admin.site.register(Employer,EmployerAdmin)
admin.site.register(WxidAlias,WxidAliasAdmin)
admin.site.register(GroupId,GroupIdAdmin)
admin.site.register(Handle,HandleAdmin)
admin.site.register(PromotedJob,PromotedJobAdmin)
admin.site.register(AdMessage,AdMessageAdmin)
admin.site.unregister(Group)