from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
import os


NUM_EMPLOYEES = (
    (5,'Less Than 5'),
    (10,'6-10'),
    (20,'11-20'),
    (50,'21-50'),
    (100,'51-100'),
    (200,'101-200'),
    (500,'201-500'),
    (1000,'More Than 500')
)



# Cut down DB hits by fetching candidates and employers
class CustomUserManager(UserManager):
    def get(self, *args, **kwargs):
        return super().select_related('candidate','employer').get(*args, **kwargs)
       


class SiteUser(AbstractUser):
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    # last_name = models.CharField(_("last name"), max_length=150, blank=False)
    email = models.EmailField(_("email address"), unique=True, validators=[EmailValidator()], error_messages={
            'unique': _('That email address has already been registered. Please use another one.'),
        })
    
    wechat_id = models.CharField(blank=True, null=True)
    phone_number = PhoneNumberField(blank=True)
    city = models.CharField(blank=True)
    country = CountryField(blank=True)
    intro = models.TextField(blank=True)
    job_types = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    profile_pic = models.ImageField(upload_to='images',null=True, blank=True)

    objects = CustomUserManager()
    
    class Meta:
        verbose_name = 'All User'



# Add type of agent - modelling, teacher etc
class Employer(models.Model):
    user = models.OneToOneField(SiteUser, on_delete=models.CASCADE, related_name='employer')
    website = models.CharField(blank=True)
    company_size = models.CharField(max_length=6, choices=NUM_EMPLOYEES, default=5)
    
    def __str__(self):
        return self.user.first_name
    


class Candidate(models.Model):
    user = models.OneToOneField(SiteUser, on_delete=models.CASCADE, related_name='candidate')
    sex = models.BooleanField(null=True)
    dob = models.DateField(max_length=8, blank=True, null=True)
    cv = models.FileField(upload_to='cvs', null=True, blank=True)
    cover_letter = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.user.first_name
    
    def cv_fname(self):
        return os.path.basename(self.cv.name)






# No need to validate as everything is converted to a webp
class CandidateImage(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images')
    thumbnail = models.ImageField(upload_to='images', blank=True, null=True)


class CandidateVideo(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='videos')
    # ,validators=[FileExtensionValidator(allowed_extensions=['mp4','webm'])] - doesn't work
    thumbnail = models.CharField()

    def extension(self):
        name, extension = os.path.splitext(self.video.name)
        return 'video/' + extension[1:]



# Database to store wxid and wx_alias pairs
class WxidAlias(models.Model):
    wxid = models.CharField(max_length=50, unique=True)
    wx_alias = ArrayField(models.CharField(max_length=100), null=True, blank=True, default=list) #Make this so it only contains unique items with validator
    wx_alias_request_by_user = models.ForeignKey(Candidate, on_delete=models.CASCADE, blank=True, null=True)
    # List of timestamps of when each request was sent
    wx_alias_requests_sent_by_me = ArrayField(models.DateTimeField(), null=True, blank=True, default=list)
    notes = models.TextField()

    def __str__(self):
        return self.wxid

    class Meta:
        verbose_name = 'WXID Aliase'

    


class GroupId(models.Model):
    group_id = models.CharField(max_length=50, unique=True)
    group_name = models.CharField(max_length=50)
    wxids = models.ManyToManyField(WxidAlias, through='Handle')

    def __str__(self):
        return self.group_name


class Handle(models.Model):
    wxid = models.ForeignKey(WxidAlias, on_delete=models.CASCADE, related_name='handle')
    group = models.ForeignKey(GroupId, on_delete=models.CASCADE, related_name='handle')
    handle = models.CharField(max_length=50)

    def __str__(self):
        return str(self.handle)



YEARS_EXPERIENCE = [
    (None, 'Enter a period of time 输入经验时间'),
    ('0', 'No experience 无经验'),
    ('6','At least 6 months 至少6个月'),
    ('12','At least 1 year 至少一年'),
    ('24','At least 2 years 至少两年'),
    ('36','At least 3 years 至少三年'),
    ('60','At least 5 years 至少五年'),
    ('120','At least 10 years 至少十年'),
    ('121','More than 10 years 多于十年'),
]

EMPLOYMENT_TYPE = [
    (None, 'Enter an employment type 输入工作种类'),
    ('full', 'Full Time 全职'),
    ('part', 'Part Time 兼职'),
    ('remote', 'Remote  远程'),
    ('intern', 'Internship 实习生'),
    ('contract', 'Contract 合同'),
    ('training', 'Training 培训')
]

ACCOMMODATION = [
    (None, 'Enter accomodation type 输入住房种类'),
    ('shared', 'Shared Flat 合租'), 
    ('independent', 'Independent Flat 独立'),
    ('allowance', 'Housing Allowance 住房补贴'),
    ('none', 'None Provided 无')
]

CONTRACT_LENGTH = [
    (None, 'Enter contract length 输入合同期限'),
    ('one_off', 'One Off 一次性'), 
    ('1_day', '1 Day 一天'),
    ('1_week', '1 Week 一周'),
    ('1_month', '1 Month 一月'),
    ('3_months', '3 Months 三月'),
    ('6_months', '6 Months 六月'),
    ('1_year', '1 Year 一年'),
    ('2_years', '2 Years 两年'),
    ('5_years', '5 Years 五年'),
    ('on-going', 'On-going 不限日期')
]

PAY_SETTLEMENT_DATE = [
    (None, 'Enter when they will get paid 输入什么时候发工资'),
    ('same_day', 'Same Day 当天'),
    ('after_job_completion', 'After Job Completion 完成工作'),
    ('weekly', 'Weekly 每周性'),
    ('monthly', 'Monthly 每月性')
]


# Need to use a callable for some reason
def empty_list():
    return []

# Need to comment out path("", include("jobsboard.urls")), in urls to makemigrations for new fields
class Job(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)
    time_updated = models.DateTimeField(auto_now_add=True)
    is_draft = models.BooleanField(default=False)
# All messages are saved for review purposes.
# This is whether the parser can figure out whether it's an actual job
    is_job = models.BooleanField(default=True)
    scraped = models.BooleanField(default=True)

# If it is put through manually, then will be "owned" by an employer
    wx_handle = models.ForeignKey(Handle, on_delete=models.CASCADE, blank=True, null=True)
    wxid_alias = models.ForeignKey(WxidAlias, on_delete=models.CASCADE, blank=True, null=True)
    group = models.ForeignKey(GroupId, on_delete=models.CASCADE, blank=True, null=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, null=True)

    cities = ArrayField(models.CharField(max_length=100), null=True, blank=True)
    job_types = ArrayField(models.CharField(max_length=100), null=True, blank=True, default=empty_list)
    subjects = ArrayField(models.CharField(max_length=100), null=True, blank=True, default=empty_list)
    job_description = models.TextField(unique=True, error_messages={
        'unique': _('A job with this job description already exists. Please do not copy and paste job descriptions across jobs.')
    })
    jd_translation = models.TextField(default='')
    job_title = models.CharField(max_length=200, null=True, blank=True)
    experience = models.CharField(choices=YEARS_EXPERIENCE, null=True, blank=True)
    employment_type = models.CharField(choices=EMPLOYMENT_TYPE, null=True, blank=True)
    salary_lower_range = models.PositiveIntegerField(null=True, blank=True)
    salary_upper_range = models.PositiveIntegerField(null=True, blank=True)

    accommodation = models.CharField(choices=ACCOMMODATION, null=True, blank=True)
    start_date = models.DateField(max_length=8, blank=True, null=True)
    contract_length = models.CharField(choices=CONTRACT_LENGTH, null=True, blank=True)
    pay_settlement_date = models.CharField(choices=PAY_SETTLEMENT_DATE, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Jobs"

    def __str__(self):
        return self.job_description[:20]
    
    def get_absolute_url(self):
        return f'/job/{self.id}/'
    



class FavouriteJob(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='favourites')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='favourites')

    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['candidate', 'job'], name='unique_favs')
    ]


STATUS = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('revoked', 'Revoked'),
]

class JobApplication(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(choices=STATUS, default='pending')
    employer_removed = models.BooleanField(default=False)
    candidate_removed = models.BooleanField(default=False)

    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['candidate', 'job'], name='unique_apps')
    ]
        
# Always starts with Pending

# Employer status
# Candidate revokes, candidate deletes => Revoked
# Employer approves, candidate deletes => Revoked
# Candidate revokes => Revoked

# Employer rejects, candidate deletes => Rejected
# Employer rejects => Rejected

# Employer approves => Approved

# Candidate status
# Candidate revokes, employer deletes => Revoked
# Candidate revokes => Revoked

# Employer approves, employer deletes => Rejected
# Employer rejects, employer deletes => Rejected
# Employer rejects => Rejected

# Employer approves => Approved




class PromotedJob(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)
    time_updated = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    currency = models.CharField(max_length=3, default='CNY')
    payment_method = models.CharField(max_length=20, default='Stripe')
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='promoted')
    times_promoted = models.PositiveSmallIntegerField(default=1)


    def __str__(self):
        return str(self.job)
    

class AdMessage(models.Model):
    text = models.TextField()

    class Meta:
        verbose_name_plural = 'Ad Messages'