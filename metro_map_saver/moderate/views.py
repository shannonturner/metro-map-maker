from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from django.contrib.auth.models import User

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .models import ActivityLog

class ActivityLogList(ListView):

    """ Display ActivityLog entries in a tabular format
    """

    model = ActivityLog
    paginate_by = 100

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if request.user.id != int(self.kwargs.get('user_id') or 0) and not request.user.is_superuser:
            # You can view your own ActivityLog,
            # but not someone else's if you aren't a superuser
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        self.queryset = ActivityLog.objects.all()
        if self.kwargs.get('user_id'):
            self.user = get_object_or_404(User, id=self.kwargs['user_id'])
            self.queryset = self.queryset.filter(user=self.user)
        return self.queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.user:
            context['activity_user'] = self.user
        return context
