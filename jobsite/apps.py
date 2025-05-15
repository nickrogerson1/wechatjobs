from django.apps import AppConfig
import posthog
import os

class MainAppConfig(AppConfig):
    name = 'jobsite'
    def ready(self):
        posthog.api_key = os.getenv('POSTHOG_API_KEY')
        posthog.host = 'https://eu.i.posthog.com'