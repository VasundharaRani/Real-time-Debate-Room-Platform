from django.contrib import admin
from .models import DebateRoom, RoomParticipant
from users.admin import custom_admin_site  
# Register your models here.
@admin.register(DebateRoom, site=custom_admin_site)
class DebateRoomAdmin(admin.ModelAdmin):
    list_display = ('title','topic','created_by','is_live','is_private','is_featured','format','created_at')
    list_filter = ('is_live','is_private','format')
    search_fields = ('title','topic','created_by__username')
    list_editable = ('is_featured',)

@admin.register(RoomParticipant,site=custom_admin_site)
class RoomParticipantAdmin(admin.ModelAdmin):
    list_display = ('user','room','role','is_muted','is_kicked','joined_at')
    list_filter = ('role','is_muted','is_kicked')
    search_fields = ('user__username','room__title')

# @admin.register(DebateRound)
# class DebateRoundAdmin(admin.ModelAdmin):
#     list_display = ('room','round_number','start_time','end_time','current_speaker','is_active')
#     list_filter = ('is_active',)
#     search_fields = ('room_title',)