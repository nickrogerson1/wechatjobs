# Generated by Django 4.2 on 2024-06-18 17:15

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_countries.fields
import jobsboard.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('first_name', models.CharField(max_length=150, verbose_name='first name')),
                ('email', models.EmailField(error_messages={'unique': 'That email address has already been registered. Please use another one.'}, max_length=254, unique=True, validators=[django.core.validators.EmailValidator()], verbose_name='email address')),
                ('user_type', models.CharField(choices=[(None, ''), ('candidate', 'candidate'), ('employer', 'employer')])),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'All User',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sex', models.BooleanField(null=True)),
                ('wechat_id', models.CharField(blank=True)),
                ('current_city', models.CharField(blank=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2)),
                ('dob', models.DateField(blank=True, max_length=8, null=True)),
                ('intro', models.TextField(blank=True)),
                ('interested_job_types', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, null=True, size=None)),
                ('cv', models.FileField(blank=True, null=True, upload_to='cvs')),
                ('cover_letter', models.FileField(blank=True, null=True, upload_to='')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='candidate', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Employer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(blank=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2)),
                ('wechat_id', models.CharField(blank=True)),
                ('website', models.CharField(blank=True)),
                ('intro', models.TextField(blank=True)),
                ('profile_pic', models.ImageField(blank=True, upload_to='employer-profile-pics')),
                ('job_types_covered', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, null=True, size=None)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('is_draft', models.BooleanField(default=False)),
                ('is_job', models.BooleanField(default=True)),
                ('wx_handle', models.CharField(blank=True, max_length=60)),
                ('wxid', models.CharField(blank=True, max_length=60)),
                ('wx_alias', models.CharField(blank=True, max_length=60, null=True)),
                ('group_name', models.CharField(blank=True, max_length=100, null=True)),
                ('cities', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, null=True, size=None)),
                ('job_types', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, default=jobsboard.models.empty_list, null=True, size=None)),
                ('subjects', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, default=jobsboard.models.empty_list, null=True, size=None)),
                ('job_description', models.TextField(unique=True)),
                ('job_title', models.CharField(blank=True, max_length=200, null=True)),
                ('years_experience', models.CharField(blank=True, choices=[(None, 'Enter a period of time'), ('0', 'No experience'), ('6', 'At least 6 months'), ('12', 'At least 1 year'), ('24', 'At least 2 years'), ('36', 'At least 3 years'), ('60', 'At least 5 years'), ('120', 'At least 10 years'), ('121', 'More than 10 years')], null=True)),
                ('employment_type', models.CharField(blank=True, choices=[(None, 'Enter an employment type'), ('full', 'Full Time'), ('part', 'Part Time'), ('remote', 'Remote'), ('intern', 'Internship'), ('contract', 'Contract'), ('training', 'Training')], null=True)),
                ('salary_lower_range', models.PositiveIntegerField(blank=True, null=True)),
                ('salary_upper_range', models.PositiveIntegerField(blank=True, null=True)),
                ('employer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jobsboard.employer')),
            ],
            options={
                'verbose_name_plural': 'Jobs',
            },
        ),
        migrations.CreateModel(
            name='WxidAlias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wxid', models.CharField(max_length=60)),
                ('wx_alias', models.CharField(max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='JobApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('revoked', 'Revoked')], default='pending')),
                ('employer_removed', models.BooleanField(default=False)),
                ('candidate_removed', models.BooleanField(default=False)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='jobsboard.candidate')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='jobsboard.job')),
            ],
        ),
        migrations.CreateModel(
            name='FavouriteJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favourites', to='jobsboard.candidate')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favourites', to='jobsboard.job')),
            ],
        ),
        migrations.CreateModel(
            name='CandidateVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video', models.FileField(upload_to='videos')),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='jobsboard.candidate')),
            ],
        ),
        migrations.CreateModel(
            name='CandidateImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='images')),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='jobsboard.candidate')),
            ],
        ),
        migrations.AddConstraint(
            model_name='jobapplication',
            constraint=models.UniqueConstraint(fields=('candidate', 'job'), name='unique_apps'),
        ),
        migrations.AddConstraint(
            model_name='favouritejob',
            constraint=models.UniqueConstraint(fields=('candidate', 'job'), name='unique_favs'),
        ),
    ]
