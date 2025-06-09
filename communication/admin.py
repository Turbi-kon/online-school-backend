from django.contrib import admin
from .models import Channel, Message

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'max_participants', 'created_at')
    filter_horizontal = ('participants', 'groups_allowed')
    readonly_fields = ('created_by',)
    search_fields = ('name',)
    list_filter = ('created_at',)

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()
