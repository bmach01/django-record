from .models import Report


def pending_reports(request):
    if request.user.is_authenticated and request.user.role in ('admin', 'moderator'):
        count = Report.objects.filter(status='pending').count()
        return {'pending_reports_count': count}
    return {'pending_reports_count': 0}
