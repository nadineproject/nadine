from datetime import datetime

from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from django.shortcuts import get_object_or_404, redirect
from django.views import generic

from django.forms import ValidationError
from .forms import ExepForm, RecuForm
from .models.elocky_cred import ElockyCred


@method_decorator(staff_member_required, name='dispatch')
class IndexView(generic.ListView):
    model = ElockyCred

    template_name = 'elocky/index.html'
    context_object_name = 'elocky_user_list'

    def get_queryset(self):
        """Return elocky user."""
        ElockyCred.sync_elocky_invite()
        return ElockyCred.objects.order_by('username')


@method_decorator(staff_member_required, name='dispatch')
class DetailView(generic.DetailView):
    model = ElockyCred
    template_name = 'elocky/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        elockycred_access = self.object.get_acces()
        context['access_recu'] = elockycred_access.get('access_recu')
        context['access_exep'] = elockycred_access.get('access_exep')
        context['recu_form'] = RecuForm()
        context['exep_form'] = ExepForm()
        return context


@staff_member_required
def delete_recu(request, pk, access_id):
    elockycred = get_object_or_404(ElockyCred, pk=pk)

    elockycred.remove_recu(access_id)

    return redirect('elocky:detail', pk=pk)


@staff_member_required
def delete_exep(request, pk, access_id):
    elockycred = get_object_or_404(ElockyCred, pk=pk)

    elockycred.remove_exep(access_id)

    return redirect('elocky:detail', pk=pk)


@staff_member_required
def create_recu(request, pk):
    elockycred = get_object_or_404(ElockyCred, pk=pk)

    if request.method == 'POST':
        form = RecuForm(request.POST)
        if form.is_valid():
            time_min = form.cleaned_data['time_min']
            time_max = form.cleaned_data['time_max']
            day = form.cleaned_data['day']
            if time_min > time_max:
                raise ValidationError('Wrong Date')
            elockycred.recurent_access(time_min.isoformat(), time_max.isoformat(), day)
    return redirect('elocky:detail', pk=pk)


@staff_member_required
def create_exep(request, pk):
    elockycred = get_object_or_404(ElockyCred, pk=pk)

    if request.method == 'POST':
        form = ExepForm(request.POST)
        if form.is_valid():
            date_min = form.cleaned_data['date_min']
            date_max = form.cleaned_data['date_max']
            if date_min > date_max:
                raise ValidationError('Wrong Date')
            elockycred.exep_access(date_min.isoformat(), date_max.isoformat())
    return redirect('elocky:detail', pk=pk)

