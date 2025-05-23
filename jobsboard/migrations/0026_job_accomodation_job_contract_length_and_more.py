# Generated by Django 4.2 on 2024-08-12 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobsboard', '0025_employer_company_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='accomodation',
            field=models.CharField(blank=True, choices=[(None, 'Enter accomodation type 输入住房种类'), ('shared', 'Shared Flat 合租'), ('independent', 'Independent flat 独立'), ('allowance', 'Housing Allowance 住房补贴'), ('none', 'None Provided 无')], null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='contract_length',
            field=models.CharField(blank=True, choices=[(None, 'Enter contract length 输入合同长度'), ('one_off', 'One Off 一次性'), ('1_day', '1 Day 一天'), ('1_week', '1 Week 一周'), ('1_month', '1 Month 一月'), ('3_months', '3 Months 三月'), ('6_months', '6 Months 六月'), ('1_year', '1 Year 一年'), ('2_years', '2 Years 两年'), ('5_years', '5 Years 五年'), ('on-going', 'On-going 不限日期')], null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='pay_settlement_date',
            field=models.CharField(blank=True, choices=[(None, 'Enter when they will get paid 输入什么时候发工资'), ('same_day', 'Same Day 当天'), ('after_job_completion', 'After Job Completion 完成工作'), ('weekly', 'Weekly 每周性'), ('monthly', 'Monthly 每月性')], null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='start_date',
            field=models.DateField(blank=True, max_length=8, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='employment_type',
            field=models.CharField(blank=True, choices=[(None, 'Enter an employment type 输入工作种类'), ('full', 'Full Time 全职'), ('part', 'Part Time 兼职'), ('remote', 'Remote  远程'), ('intern', 'Internship 实习生'), ('contract', 'Contract 合同'), ('training', 'Training 培训')], null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='years_experience',
            field=models.CharField(blank=True, choices=[(None, 'Enter a period of time 输入经验时间'), ('0', 'No experience 无经验'), ('6', 'At least 6 months 至少6个月'), ('12', 'At least 1 year 至少一年'), ('24', 'At least 2 years 至少两年'), ('36', 'At least 3 years 至少三年'), ('60', 'At least 5 years 至少五年'), ('120', 'At least 10 years 至少十年'), ('121', 'More than 10 years 多于十年')], null=True),
        ),
    ]
