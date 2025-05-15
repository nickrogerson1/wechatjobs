from django import forms
from .models import *
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from django.contrib.auth.forms import (UserCreationForm, AuthenticationForm, 
UsernameField, PasswordResetForm, SetPasswordForm, PasswordChangeForm)
from django.contrib.auth.hashers import check_password
from django.contrib.auth import password_validation

from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

from phonenumber_field.formfields import PhoneNumberField
from captcha.fields import CaptchaField, CaptchaTextInput

from datetime import date
import re
import requests
import json


wId = os.getenv('wId')


class SearchBox(forms.Form):
    search_terms = forms.CharField(label="Search", max_length=200,
        widget=forms.TextInput(
            attrs={'placeholder': 'Search Job Descriptions'
    }))




# Customizes the HTML Select element
from django.forms import Select
class Select(Select):
    def create_option(self, *args,**kwargs):
        option = super().create_option(*args,**kwargs)
        if not option.get('value'):
            option['attrs']['disabled'] = 'disabled'
            option['attrs']['selected'] = 'selected'
        return option


# Dynamically get the available locations and job types
def get_option_list(qs, qtype):

    all_vals = []
    for q in qs:
        if qtype == 'cities':
            all_vals += q.cities
        elif qtype == 'types':
            all_vals += q.job_types
        elif qtype == 'subs':
            all_vals += q.subjects

    new_vals = []
    main_cities = ['beijing', 'guangzhou', 'shanghai', 'shenzhen']
    capital_subs = ['esl', 'ielts', 'toefl', 'toeic', 'p.e.']

    for x in sorted(set(all_vals)):
        if x not in main_cities:
            if ' ' in x:
                new_vals.append((x,x.title()))
            elif x in ['dj', 'ktv'] or x in capital_subs:
                # print(x)
                new_vals.append((x,x.upper()))
            else:
                new_vals.append((x,x.capitalize()))

    if qtype == 'cities':
        new_vals = [(c, c.capitalize()) for c in main_cities] + new_vals

    if qtype == 'cities':
        heading = 'Location'
    elif qtype == 'types':
        heading = 'Job Types'
    elif qtype == 'subs':
        heading = 'Subjects'

    return [(0, heading)] + new_vals




SEARCH_OPTIONS = (
    ('show_all', 'Show all results'),
    ('has_wechat', 'Only show adverts with Wechat IDs'),
    ('is_employer','Only show adverts from recruiters registered with this site'),
    ('no_wechat', 'Only show adverts without a Wechat ID'),
)


class SearchJobs(forms.Form):

# Pass the qs from the view to prevent further DB hits
    def __init__(self, qs, *args, **kwargs):
    
        super().__init__(*args, **kwargs)
        self.fields['type'].choices = get_option_list(qs, 'types')
        self.fields['loc'].choices = get_option_list(qs, 'cities')
        self.fields['sub'].choices = get_option_list(qs, 'subs')
        

    q = forms.CharField(max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
            'placeholder': 'Search By Keyword',
            # "autofocus": True,
            "class": "form-control",
    }))

    type = forms.ChoiceField(
        required=False,
        widget=Select(attrs={"class": "form-select"})
    )

    loc = forms.ChoiceField(
        required=False,
        widget=Select(attrs={"class": "form-select"})
    )

    sub = forms.ChoiceField(
        required=False,
        widget=Select(attrs={"class": "form-select"})
    )

    options = forms.ChoiceField(
        initial='show_all',
        widget=forms.RadioSelect(attrs={'form':'search-form'}),
        choices=SEARCH_OPTIONS,
    )

    posters = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'form':'search-form', 'class':'autocomplete', })
    )

    



class LoginForm(AuthenticationForm):
    
    username = UsernameField(
        widget=forms.TextInput(attrs={
            "autofocus": True,
            # "placeholder": "Username",
            # "class": "form-control"
        }))
    
    # email = forms.EmailField()
    
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "current-password",
            # "placeholder": "Password",
            # "class": "form-control"  
        }))

    error_messages = {
        "invalid_login": _('''
            <h5 class="text-danger">
            Please enter a valid Username and/or Password. Note that the password field is case-sensitive.</h5>        
        '''),

        "inactive": _('''
        <h2 class="text-center text-danger mb-2">This account is inactive!</h2> 
        <h5 class="text-danger">If this is your first time to log in, 
        then make sure you have activated the account with the email we sent you.</h5>
        '''),
    }

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_username(self):
        return self.cleaned_data['username'].lower()






class SiteUserMixin:
    
    def clean_wechat_id(self):
        wechat_id = self.cleaned_data['wechat_id'] or None

        if wechat_id:
            wechat_id = wechat_id.strip()
            print(f"Wechat ID: {wechat_id}")

        # Check if it exists (sign up) and same as before
            if hasattr(self,'old_wechat_id') and wechat_id == self.old_wechat_id:
                    return wechat_id 
        # Check if already registered
            if SiteUser.objects.filter(wechat_id=wechat_id).exists():
                raise ValidationError(
                    mark_safe(_('Someone else has already registered this Wechat ID. Pick another one.'))
                    )
        
        return wechat_id
    
    # Then check if it even exists
    #     headers = {
    #         'Authorization': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzE2MzI3MzY3NyIsInBhc3N3b3JkIjoiJDJhJDEwJHlUamdScXFNQnJvb3VWbGk2Y1hvc2VoL3V1cnVOSnYuWnU4Mjh1aDBJZWM0cDFrVHMwZENDIn0.3m2bDjrQzDJkV8poSZHakWgmt3zMKdeb1NX_hTrhDs5p0TWnpHZA5BiVj43rSZZ4z8AtkXyqgZCHAXoirKi8fw',
    #         'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    #         'Content-Type': 'application/json'
    #     }

    #     payload = {
    #         'wId' : wId,
    #         'wcId' : wechat_id
    #     }

    #     # Check for code 1000 otherwise throw error
    #     # https://wkteam.cn/api-wen-dang2/hao-you-cao-zuo/serchUser.html

    #     data = {}
        
    #     try:
    #         res = requests.post('http://59.36.146.193:9899/searchUser',headers=headers,data=json.dumps(payload))
    #         data = json.loads(res.text)['data']
    #         print(f'DATA: {data}')
    #     except Exception as e:
    #         print(e)

    # # Check if it errored. Won't work inside try block
    #     if 'errMsg' in data:
    #         raise ValidationError(
    #             mark_safe(_("Whoooa partner, can't seem to find that Wechat ID. Did you make a mistake?"))
    #             )

        return wechat_id




USER_TYPE = (
    ('candidate', 'Candidate 求职者'),
    ('employer', 'Employer 猎头雇佣的')
)

SEX = (
    ('male', 'male'),
    ('female', 'female')
)


class SignUpForm(UserCreationForm,SiteUserMixin):

    terms = forms.BooleanField(required=True)
    # wechat = forms.CharField(required=False)

    user_type = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=USER_TYPE,
        error_messages={'required': 'You must choose your User Type.'}
    )

    sex = forms.ChoiceField(
        required=False,
        widget=forms.RadioSelect,
        choices=SEX,
    )

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            print(f'FIELD: {field}')
            if field not in ('user_type', 'sex', 'country'):
                self.fields[field].widget.attrs['class'] = 'form-control'

        # self.fields['user_type'].empty_label = None
        # self.fields['user_type'].widget.attrs['class'] = 'form-select'
        self.fields['terms'].widget.attrs['class'] = 'select-box'
        self.fields['username'].widget.attrs['autofocus'] = False
        self.fields['country'].widget.attrs['class'] = 'form-select form-control'
        # self.fields['country'].initial = ''

    class Meta(UserCreationForm.Meta):
        model = SiteUser
        fields = UserCreationForm.Meta.fields + ('first_name', 'email', 'wechat_id', 'country')


    def clean_sex(self):
        sex = self.cleaned_data['sex']

    # Only clean this if there's a user_type
        if 'user_type' in self.cleaned_data:
            user_type = self.cleaned_data['user_type']
        else:
            return sex

        if user_type == 'candidate' and not sex:
            self.fields['sex']
            raise ValidationError(
                    mark_safe(_(f'You must select a Gender.'))
                )
        return sex
    

    def clean_username(self):
        return self.cleaned_data['username'].lower()







JOB_TYPES = [
    ('teacher', 'Teacher 老师'),
    ('online teacher', 'Online Teacher 在线老师'),
    ('model','Model 模特'),
    ('actor','Actor 演员'),
    ('voiceover','Voiceover 配音'),
    ('recording','Recording 录音'),
    ('tiktok','Tiktok 抖音'),
    ('translator','Translator 翻译'),
    ('bar work','Bar Work 酒吧'),
    ('singer','Singer 歌手'),
    ('musician','Musician 音乐家'),
    ('dancer','Dancer 舞蹈'),
    ('ktv','KTV'),
    ('travel companion', 'Travel Companion 伴游'),
    ('other', 'Other 其他'),
]



class JobFormMixin(forms.ModelForm):

    start_date = forms.DateField(required=False, 
        widget=forms.widgets.DateInput(attrs={'type': 'date'}))

    job_types = forms.MultipleChoiceField(
        choices=JOB_TYPES,
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )


    select_fields = ('experience','employment_type','accommodation','contract_length','pay_settlement_date')


    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['job_title'].widget.attrs['placeholder'] = 'Enter a job title'
        self.fields['cities'].widget.attrs['placeholder'] = 'beijing, shanghai, shenzhen, guangzhou'
        self.fields['subjects'].widget.attrs['placeholder'] = 'maths, science, general english'
        self.fields['job_description'].widget.attrs['placeholder'] = 'Describe your job as best you can here....'
        self.fields['salary_lower_range'].widget.attrs['placeholder'] = 10000
        self.fields['salary_upper_range'].widget.attrs['placeholder'] = 40000




    class Meta:
        model = Job
        exclude = ['is_job','scraped','is_draft','wx_handle','wxid_alias','group','employer','jd_translation']
        error_messages={
            'cities': {
                'item_invalid': _('Something is not right here. Check you have used the commas properly ie. beijing,shanghai,tianjin,shenzhen.'),
            },
            'subjects': {
                'item_invalid': _('Something is not right here. Check you have used the commas properly ie. science,english,geography.'),
            }
        }


    # This is a back up server side validator as this should be handled by the JS
    # And will only invoke errors if they somehow bypass it
    def do_word_count(self, text, field_text, chinese_word_count, latin_word_count):

        chinese_check = re.findall(u'[\u4e00-\u9fff]', text)
        print(f'CHINESE CHECK: {chinese_check}')

        if chinese_check:
            print('Its Chinese')
            print(f'WORDS: {len(text)}')
        
            if len(chinese_check) < chinese_word_count:
                raise ValidationError(
                        mark_safe(_('<strong>你写得太少了 —— 多写一点啊</strong>'))
                    )
      
        word_count = len(text.strip().split(' '))
        print(f'LATIN WORDS: {word_count}')

        if not word_count:
            raise ValidationError(
                mark_safe(_(f"<strong>You didn't write anything! Your job {field_text} needs to be more than {latin_word_count} words in length!</strong>"))
            )
        
        if word_count < latin_word_count:
            raise ValidationError(
                mark_safe(_(f"<strong>You only wrote {word_count} word{'' if word_count == 1 else 's'}. Your job {field_text} needs to be more than {latin_word_count} words in length!</strong>"))
            )
            
        return text
    


    def clean_job_description(self):
        desc = self.cleaned_data['job_description']

        if not hasattr(self, 'draft_post'):
            field_text = 'description'

            MIN_CHINESE_WORD_COUNT = 10
            MIN_LATIN_WORD_COUNT = 20

            self.do_word_count(desc, field_text, MIN_CHINESE_WORD_COUNT, MIN_LATIN_WORD_COUNT)
        
    # Only do this check if it's an edit
        if hasattr(self, 'job'):
            # Check if they're the same
            if desc == self.job.job_description:
                return desc  # If same as before, skip unique validation
            
            if Job.objects.filter(job_description=desc).exists():
                raise ValidationError(
                    mark_safe(_('This job description already exists. Please do not copy and paste job descriptions across jobs.'))
                    )
        return desc
    
        


    def clean_job_title(self):
        title = self.cleaned_data['job_title']

        if not hasattr(self, 'draft_post'):
            field_text = 'title'

            MIN_CHINESE_WORD_COUNT = 10
            MIN_LATIN_WORD_COUNT = 10

            return self.do_word_count(title, field_text, MIN_CHINESE_WORD_COUNT, MIN_LATIN_WORD_COUNT)
        return title
    

    def clean_job_types(self):

        # Make sure they've selected at least one when not a draft
        if not hasattr(self, 'draft_post') and not self.cleaned_data['job_types']:
             print('Validation error cleaned jobs')
             raise ValidationError(
                mark_safe(_(f'<strong>You need to select at least one type of job!</strong>'))
            )

        return self.cleaned_data['job_types']
    
    def clean_cities(self):

        cities = self.cleaned_data['cities']

        print(f'CITIES: {cities}')

        return cities




class JobPostForm(JobFormMixin):

    def __init__(self, *args, **kwargs):

    # Don't run extra checks for drafts
        if 'draft_post' in kwargs:
            self.draft_post = kwargs.pop('draft_post')

        super().__init__(*args, **kwargs)

        for f in self.fields:
            # print(f'FIELD: {f}')
            if f != 'job_types':
                self.fields[f].widget.attrs['class'] = 'form-control'

            if f in self.select_fields:
                self.fields[f].widget.attrs['class'] = 'form-select'




# Populates the form with the job data from the db
# Otherwise identical to the previous form
class EditJobForm(JobFormMixin):

    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop('job')

        if 'draft_post' in kwargs:
            self.draft_post = kwargs.pop('draft_post')

        super(EditJobForm, self).__init__(*args, **kwargs)

        for f in self.fields:
            # print(f'FIELD: {f}')
            self.fields[f].initial = getattr(self.job,f)

            if f != 'job_types':
                self.fields[f].widget.attrs['class'] = 'form-control'

            if f in self.select_fields:
                self.fields[f].widget.attrs['class'] = 'form-select'
       





SEXES = [
    ('M', 'Male'),
    ('F', 'Female')
]


# def validate_file_type(file):
#     valid_types = ('application/pdf','application/rtf','text/plain','application/msword',
#                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#     # print(f'VALUE123: {value.__dict__}')
#     if file.content_type not in valid_types:
#         raise ValidationError(f'{file.content_type} is an invalid file type.')


class CandidateForm(SiteUserMixin, forms.ModelForm):

    name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    sex = forms.ChoiceField(choices=SEXES)
    job_types = forms.MultipleChoiceField(
        choices=JOB_TYPES[1:],
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    dob = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    cv = forms.FileField(required=False, 
    validators=[FileExtensionValidator(['pdf','docx','doc','rtf','txt'])])

    phone_number = PhoneNumberField(required=False)
    phone_number.error_messages['invalid'] = 'Enter a correct number with an international dialling code like +86 136 5109 0846'


    def __init__(self, *args, **kwargs):
        d = kwargs.pop('user', None)
        self.old_wechat_id = d.wechat_id
        super(CandidateForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            # print(f'FIELD: {field}')
            if field != 'job_types':
                self.fields[field].widget.attrs['class'] = 'form-control'

        # self.fields['user'].queryset = self.request.user

        self.fields['name'].widget.attrs['value'] = d.first_name
        self.fields['name'].widget.attrs['disabled'] = True

        self.fields['email'].widget.attrs['value'] = d.email
        self.fields['email'].widget.attrs['disabled'] = True
        # self.fields['email'].widget.attrs['required'] = False

        if d.wechat_id:
            self.fields['wechat_id'].initial = d.wechat_id
        else:
            self.fields['wechat_id'].widget.attrs['placeholder'] = 'Enter Your Wechat ID'

        if d.phone_number:
            self.fields['phone_number'].initial = d.phone_number
        else:
            self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter Your Whatsapp Number'

        if d.job_types:
            self.fields['job_types'].initial = d.job_types
            # self.fields['interested_job_types'].widget.attrs['class'] = 'mb-3'

        if d.city:
            self.fields['city'].initial = d.city
        else:
            self.fields['city'].widget.attrs['placeholder'] = 'Enter Your Current City'

        if d.country:
            self.fields['country'].initial = d.country
        self.fields['country'].widget.attrs['class'] = 'form-select'

        if d.intro:
            self.fields['intro'].initial = d.intro
        else:
            self.fields['intro'].widget.attrs['placeholder'] = 'Type in your info here...'

        if d.candidate.cv:
            self.fields['cv'].widget.attrs['value'] = d.candidate.cv

        if d.candidate.dob:
            self.fields['dob'].initial = d.candidate.dob

        if d.candidate.sex:
            self.fields['sex'].initial = 'M'
        else:
            self.fields['sex'].initial = 'F'
        self.fields['sex'].widget.attrs['class'] = 'form-select'
           
    class Meta:
        model = SiteUser
        # exclude = ['password','username','date_joined','first_name','user_type','profile_pic','is_active']
        exclude = ['password','username','date_joined','first_name','user_type','is_active',
                  'last_login','is_superuser','groups','user_permissions','last_name','is_staff']



    def clean(self):
        cleaned_data = super().clean()
    # Change the gender back to a boolean
        cleaned_data['sex'] = True if cleaned_data['sex'] == 'M' else False
        return cleaned_data
    
    
    def clean_dob(self):
        dob = self.cleaned_data['dob']

        if dob:
            time_gap = date.today().year - dob.year
            # Check they weren't born in the future and they're not too young or too old
            if time_gap < 0:
                raise ValidationError(
                    _(f"Whooaa time traveller, you sure you were born in the year {dob.year}?"),
                )

            if time_gap < 14:
                raise ValidationError(
                    mark_safe(_(f"Hang on, you sure you're just <span style=\"font-size:18px;font-weight:700;\">{time_gap}</span> years old?"))
                )
            
            if time_gap >= 80:
                raise ValidationError(
                    mark_safe(_(f"Whoooa, you sure you should be working in China at <span style=\"font-size:18px;font-weight:700;\">{time_gap}</span> years of age or did you make a mistake?"))
                )

        return dob
    

    
    
    


        
class EmployerForm(SiteUserMixin,forms.ModelForm):

    name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    job_types = forms.MultipleChoiceField(
        choices=JOB_TYPES[1:],
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    website = forms.CharField(required=False)
    company_size = forms.ChoiceField(
        required=False,
        choices=NUM_EMPLOYEES
    )

    phone_number = PhoneNumberField(required=False)
    phone_number.error_messages['invalid'] = 'Enter a correct number with an international dialling code like +86 136 5109 0846'


    def __init__(self, *args, **kwargs):
        d = kwargs.pop('user', None)
        self.old_wechat_id = d.wechat_id

        super(EmployerForm, self).__init__(*args, **kwargs)

        for f in self.fields:
            # print(f'FIELD: {f}')
            if f != 'job_types':
                self.fields[f].widget.attrs['class'] = 'form-control'

        
        self.fields['name'].widget.attrs['value'] = d.first_name
        self.fields['name'].widget.attrs['disabled'] = True

        self.fields['email'].widget.attrs['value'] = d.email
        self.fields['email'].widget.attrs['disabled'] = True

        if d.country:
            self.fields['country'].initial = d.country
        self.fields['country'].widget.attrs['class'] = 'form-select'
        
        if d.intro:
            self.fields['intro'].initial = d.intro
        else:
            self.fields['intro'].widget.attrs['placeholder'] = 'Type in your info here...'

        if d.employer.website:
            self.fields['website'].initial = d.employer.website
        else:
            self.fields['website'].widget.attrs['placeholder'] = 'Add your website here...'

        if d.employer.company_size:
            self.fields['company_size'].initial = d.employer.company_size
            self.fields['company_size'].widget.attrs['class'] = 'form-select'

        if d.wechat_id:
            self.fields['wechat_id'].initial = d.wechat_id
        else:
            self.fields['wechat_id'].widget.attrs['placeholder'] = 'Enter Your Wechat ID'

        if d.job_types:
            self.fields['job_types'].initial = d.job_types
        
        if d.city:
            self.fields['city'].initial = d.city
        else:
            self.fields['city'].widget.attrs['placeholder'] = 'Enter Your City'

        if d.country:
            self.fields['country'].initial = d.country


    class Meta:
        model = SiteUser
        exclude = ['password','username','date_joined','first_name','user_type','profile_pic','is_active',
                  'last_login','is_superuser','groups','user_permissions','last_name','is_staff']

    
    def clean_website(self):
        website = self.cleaned_data['website']
        if website:
        # Make sure it looks like some sort of domain
            website = re.sub(r'^https?://', '', self.cleaned_data['website'])
            regex = r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$'

            if not re.search(regex, website):
                raise ValidationError(
                    mark_safe(_("Whoooa partner, you sure that's an actual domain?"))
                )
        return website
    











class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class FileFieldForm(forms.Form):
    file_field = MultipleFileField()





class PasswordResetEmail(PasswordResetForm):

    email = forms.EmailField(
    # Same as orginal
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            # Add these styles
            "placeholder": "Enter Your Email Address",
            "class": "form-control"
        })
    )



class PasswordValidator(object):

    def __init__(self, old_password):
        self.old_password = old_password

    def __call__(self, new_password):
        # True if they match    
        if check_password(new_password, self.old_password):
            raise ValidationError(
                _("You can't use the same password as your old one. Please choose a different one."),
                code='password_recently_used',
                # params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _(
            "You can't use the same password as your old one. Please choose a different one."
        )



class PasswordResetPass(SetPasswordForm):

    def __init__(self, *args, **kwargs):
      
        super(PasswordResetPass, self).__init__(*args, **kwargs)
    
        self.fields['new_password1'] = forms.CharField(
            label=_("New password"),
            widget=forms.PasswordInput(attrs={
                "autocomplete": "new-password",
                "placeholder": "Enter A New Password",
                "class": "form-control"
                }),
            strip=False,
            help_text=password_validation.password_validators_help_text_html(),
        )
        self.fields['new_password2'] = forms.CharField(
            label=_("New password confirmation"),
            strip=False,
            widget=forms.PasswordInput(attrs={
                "autocomplete": "new-password",
                "placeholder": "Enter The Same Password Again",
                "class": "form-control"
                }),
            validators=[PasswordValidator(self.user.password)]
        )


class ChangePasswordInProfileForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
      
        super(ChangePasswordInProfileForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        
        self.fields['old_password'].widget.attrs['placeholder']  = 'Enter Your Old Password'
        self.fields['new_password1'].widget.attrs['placeholder']  = 'Enter Your New Password'
        self.fields['new_password2'].widget.attrs['placeholder']  = 'Enter Your New Password Again'

    #     self.fields['old_password'] = forms.CharField(
    #         label=_("Old Password"),
    #         strip=False,
    #         widget=forms.PasswordInput(attrs={
    #             "autocomplete": "old-password",
    #             "placeholder": "Enter Your Old Password",
    #             "class": "form-control"
    #             }),
    #         validators=[PasswordValidator(self.request.user.password)]
    #     )

    
    # def clean_old_password(self):
    #     password = self.cleaned_data.get('password', None)
    #     if not self.user.check_password(password):
    #         raise ValidationError('Invalid password')



class ContactForm(forms.Form):

    subject = forms.CharField(      
        required=False,     
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter a subject',
            'class': 'form-control mb-3',
    }))

    message = forms.CharField(
        label='Message',
        max_length=2000,             
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter your message',
            'class': 'form-control mb-3',
    }))


class CustomCaptchaTextInput(CaptchaTextInput):
    template_name = 'jobsboard/contact/captcha.html'


class ExternalContactForm(ContactForm):

    name = forms.CharField(          
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your name',
            'class': 'form-control mb-3',
    }))

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            'placeholder': 'Enter your email address',
            'class': 'form-control mb-3',
    }))

    wechat = forms.CharField(          
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your Wechat ID',
            'class': 'form-control mb-3',
    }))

    captcha = CaptchaField(widget=CustomCaptchaTextInput)

# Honeypot field
    surname = forms.CharField(  
            required=False,        
            widget=forms.TextInput(attrs={
            'placeholder': 'Enter your Surname',
            'class': 'surname',
    }))