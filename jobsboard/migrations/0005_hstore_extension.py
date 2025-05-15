from django.db import models, migrations
from django.contrib.postgres.operations import HStoreExtension, UnaccentExtension

class Migration(migrations.Migration):

    dependencies = [
        ('jobsboard', '0004_alter_wxidalias_options'),
    ]

    operations = [
        HStoreExtension(),
        UnaccentExtension()
    ]