from datetime import timezone as dt_timezone

from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline

from .f1_importer import import_f1_session_results
from .models import GrandPrix, Season, Session, SessionResult


class UTCSessionAdminMixin:
    """قفل کردن کامل منطقه زمانی روی UTC در تمام مراحل پردازش و رندر قالب‌های ادمین."""

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        with timezone.override(dt_timezone.utc):
            response = super().changeform_view(request, object_id, form_url, extra_context)
            if hasattr(response, "render") and callable(response.render):
                response.render()
            return response

    def changelist_view(self, request, extra_context=None):
        with timezone.override(dt_timezone.utc):
            response = super().changelist_view(request, extra_context)
            if hasattr(response, "render") and callable(response.render):
                response.render()
            return response


class UTCSessionBaseForm(forms.ModelForm):
    """تضمین نمایش و ذخیره فیلد start_time به صورت دقیق بر مبنای UTC."""

    def __init__(self, *args, **kwargs):
        with timezone.override(dt_timezone.utc):
            super().__init__(*args, **kwargs)
            if self.instance and self.instance.pk and self.instance.start_time:
                utc_dt = self.instance.start_time.astimezone(dt_timezone.utc)
                self.initial["start_time"] = utc_dt.replace(tzinfo=None)

    def clean_start_time(self):
        val = self.cleaned_data.get("start_time")
        if val:
            if timezone.is_aware(val):
                return val.replace(tzinfo=dt_timezone.utc)
            return timezone.make_aware(val, dt_timezone.utc)
        return val

    class Meta:
        model = Session
        fields = "__all__"


class SessionAdminForm(UTCSessionBaseForm):
    f1_official_url = forms.URLField(
        required=False,
        label="روش اول: ایمپورت از لینک Formula1.com",
        help_text="لینک صفحه نتیجه این سشن در سایت رسمی formula1.com را وارد کرده و ذخیره را بزنید.",
        widget=forms.URLInput(attrs={"placeholder": "https://www.formula1.com/en/results/2026/races/..."}),
    )
    f1_raw_html = forms.CharField(
        required=False,
        label="روش دوم (پشتیبان): پیست کردن سورس HTML صفحه",
        help_text="اگر سایت F1 به سرور خطای SSL داد، در مرورگر خود صفحه نتیجه را باز کنید، کلید Ctrl+U را بزنید، کل متن را کپی (Ctrl+A سپس Ctrl+C) و اینجا Paste کنید.",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "کد HTML صفحه نتایج formula1.com را اینجا Paste کنید..."}),
    )

    class Meta(UTCSessionBaseForm.Meta):
        pass


class SessionInline(TabularInline):
    model = Session
    form = UTCSessionBaseForm
    extra = 0
    show_change_link = True
    tab = True


class SessionResultInline(TabularInline):
    model = SessionResult
    extra = 0
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
        f1_html = form.cleaned_data.get("f1_raw_html")
        if f1_url or f1_html:
            try:
                count, warnings = import_f1_session_results(obj, url=f1_url, raw_html=f1_html)
                messages.success(request, f"✅ تعداد {count} نتیجه با موفقیت استخراج و ثبت شد.")
                for w in warnings:
                    messages.warning(request, w)
            except Exception as exc:
                messages.error(request, f"❌ خطا در دریافت نتایج: {exc}")


@admin.register(Season)
class SeasonAdmin(ModelAdmin):
    list_display = ('year', 'is_current')
    list_editable = ('is_current',)
    ordering = ('-year',)