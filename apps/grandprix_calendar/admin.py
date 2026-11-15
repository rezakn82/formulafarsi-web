from datetime import timezone as dt_timezone

from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline

from .f1_importer import import_f1_session_results
from .models import GrandPrix, Season, Session, SessionResult

class UTCSessionAdminMixin:
    """تفسیر و نمایش فیلد زمان شروع سشن‌ها در پنل ادمین بر اساس ساعت جهانی (UTC)."""

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        with timezone.override(dt_timezone.utc):
            return super().changeform_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        with timezone.override(dt_timezone.utc):
            return super().changelist_view(request, extra_context)

class SessionAdminForm(forms.ModelForm):
    f1_official_url = forms.URLField(
        required=False,
        label="ایمپورت خودکار از لینک Formula1.com",
        help_text="لینک صفحه نتیجه این سشن در سایت رسمی formula1.com را وارد کرده و ذخیره را بزنید تا جدول نتایج خودکار پر شود.",
        widget=forms.URLInput(attrs={"placeholder": "https://www.formula1.com/en/results/2026/races/..."}),
    )

    class Meta:
        model = Session
        fields = "__all__"

class SessionInline(TabularInline):
    model = Session
    extra = 5
    show_change_link = True
    tab = True

class SessionResultInline(TabularInline):
    model = SessionResult
    extra = 22  # باز کردن ۲۰ ردیف آماده برای ۲۰ راننده فرمول یک
    autocomplete_fields = ('driver', 'team')
    fields = (
        'position',
        'driver',
        'team',
        'status',
        'grid_position',
        'laps',
        'time_or_gap',
        'q1_time',
        'q2_time',
        'q3_time',
        'points',
        'fastest_lap',
    )


@admin.register(GrandPrix)
class GrandPrixAdmin(UTCSessionAdminMixin, ModelAdmin):
    list_display = ('name', 'season', 'round_number', 'start_date', 'end_date', 'previous_winner')
    list_filter = ('season',)
    inlines = [SessionInline]


@admin.register(Session)
class SessionAdmin(UTCSessionAdminMixin, ModelAdmin):
    form = SessionAdminForm
    list_display = ('grand_prix', 'session_type', 'start_time')
    list_filter = ('grand_prix__season', 'session_type', 'grand_prix')
    search_fields = ('grand_prix__name',)
    inlines = [SessionResultInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        f1_url = form.cleaned_data.get("f1_official_url")
        if f1_url:
            try:
                count, warnings = import_f1_session_results(obj, url=f1_url)
                messages.success(request, f"✅ تعداد {count} نتیجه با موفقیت از سایت Formula1.com استخراج و ثبت شد.")
                for w in warnings:
                    messages.warning(request, w)
            except Exception as exc:
                messages.error(request, f"❌ خطا در دریافت نتایج از سایت فرمول یک: {exc}")


@admin.register(Season)
class SeasonAdmin(ModelAdmin):
    list_display = ('year', 'is_current')
    list_editable = ('is_current',)
    ordering = ('-year',)