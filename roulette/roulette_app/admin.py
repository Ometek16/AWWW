from django.contrib import admin
from .models import RollResult

@admin.register(RollResult)
class RollResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'number', 'timestamp')
    list_filter = ('number', 'timestamp')
    search_fields = ('user__username',)
    readonly_fields = ('timestamp',) # Timestamp is auto_now_add, so it's read-only