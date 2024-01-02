from django.apps import apps
from django.contrib import admin

for model in apps.get_app_config("ninja_simple_jwt").models.values():
    admin.site.register(model)
