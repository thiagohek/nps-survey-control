from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, TemplateView

from accounts.mixins import DirectorRequiredMixin, ResearcherOrDirectorMixin
from organizations.models import Filial, Service
from surveys.models import Strength, Improvement
from .forms import UserCreateForm, UserUpdateForm, StrengthForm, ImprovementForm, ServiceForm, FilialForm

User = get_user_model()


class ConfigHomeView(ResearcherOrDirectorMixin, LoginRequiredMixin, TemplateView):
    template_name = 'configs/home.html'


# ── Usuários ──────────────────────────────────────────────────────────────────

class UserListView(DirectorRequiredMixin, LoginRequiredMixin, ListView):
    model = User
    template_name = 'configs/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('branch').order_by('first_name', 'last_name')
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = User.Role.choices
        return context


class UserCreateView(DirectorRequiredMixin, LoginRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'configs/user_form.html'
    success_url = reverse_lazy('configs:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Usuário criado com sucesso.')
        return super().form_valid(form)


class UserUpdateView(DirectorRequiredMixin, LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'configs/user_form.html'
    success_url = reverse_lazy('configs:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Usuário atualizado com sucesso.')
        return super().form_valid(form)


class UserDeactivateView(DirectorRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'Você não pode desativar sua própria conta.')
        else:
            user.is_active = not user.is_active
            user.save()
            status = 'ativado' if user.is_active else 'desativado'
            messages.success(request, f'Usuário {status} com sucesso.')
        return redirect('configs:user_list')


# ── Pontos Fortes ─────────────────────────────────────────────────────────────

class StrengthListView(ResearcherOrDirectorMixin, LoginRequiredMixin, ListView):
    model = Strength
    template_name = 'configs/strength_list.html'
    context_object_name = 'strengths'


class StrengthCreateView(ResearcherOrDirectorMixin, LoginRequiredMixin, CreateView):
    model = Strength
    form_class = StrengthForm
    template_name = 'configs/strength_form.html'
    success_url = reverse_lazy('configs:strength_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ponto forte criado com sucesso.')
        return super().form_valid(form)


class StrengthUpdateView(ResearcherOrDirectorMixin, LoginRequiredMixin, UpdateView):
    model = Strength
    form_class = StrengthForm
    template_name = 'configs/strength_form.html'
    success_url = reverse_lazy('configs:strength_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ponto forte atualizado com sucesso.')
        return super().form_valid(form)


# ── Pontos a Melhorar ─────────────────────────────────────────────────────────

class ImprovementListView(ResearcherOrDirectorMixin, LoginRequiredMixin, ListView):
    model = Improvement
    template_name = 'configs/improvement_list.html'
    context_object_name = 'improvements'


class ImprovementCreateView(ResearcherOrDirectorMixin, LoginRequiredMixin, CreateView):
    model = Improvement
    form_class = ImprovementForm
    template_name = 'configs/improvement_form.html'
    success_url = reverse_lazy('configs:improvement_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ponto a melhorar criado com sucesso.')
        return super().form_valid(form)


class ImprovementUpdateView(ResearcherOrDirectorMixin, LoginRequiredMixin, UpdateView):
    model = Improvement
    form_class = ImprovementForm
    template_name = 'configs/improvement_form.html'
    success_url = reverse_lazy('configs:improvement_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ponto a melhorar atualizado com sucesso.')
        return super().form_valid(form)


# ── Serviços ──────────────────────────────────────────────────────────────────

class ServiceListView(DirectorRequiredMixin, LoginRequiredMixin, ListView):
    model = Service
    template_name = 'configs/service_list.html'
    context_object_name = 'services'


class ServiceCreateView(DirectorRequiredMixin, LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'configs/service_form.html'
    success_url = reverse_lazy('configs:service_list')

    def form_valid(self, form):
        messages.success(self.request, 'Serviço criado com sucesso.')
        return super().form_valid(form)


class ServiceUpdateView(DirectorRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'configs/service_form.html'
    success_url = reverse_lazy('configs:service_list')

    def form_valid(self, form):
        messages.success(self.request, 'Serviço atualizado com sucesso.')
        return super().form_valid(form)


# ── Filiais ───────────────────────────────────────────────────────────────────

class FilialListView(DirectorRequiredMixin, LoginRequiredMixin, ListView):
    model = Filial
    template_name = 'configs/filial_list.html'
    context_object_name = 'filiais'


class FilialCreateView(DirectorRequiredMixin, LoginRequiredMixin, CreateView):
    model = Filial
    form_class = FilialForm
    template_name = 'configs/filial_form.html'
    success_url = reverse_lazy('configs:filial_list')

    def form_valid(self, form):
        messages.success(self.request, 'Filial criada com sucesso.')
        return super().form_valid(form)


class FilialUpdateView(DirectorRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Filial
    form_class = FilialForm
    template_name = 'configs/filial_form.html'
    success_url = reverse_lazy('configs:filial_list')

    def form_valid(self, form):
        messages.success(self.request, 'Filial atualizada com sucesso.')
        return super().form_valid(form)
