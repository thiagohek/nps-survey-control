from django.contrib.auth.mixins import UserPassesTestMixin


class DirectorRequiredMixin(UserPassesTestMixin):
    """Acesso apenas para diretores."""
    def test_func(self):
        return self.request.user.is_director()


class ResearcherOrDirectorMixin(UserPassesTestMixin):
    """Acesso para pesquisadores e diretores."""
    def test_func(self):
        user = self.request.user
        return user.is_researcher() or user.is_director()


class AllRolesMixin(UserPassesTestMixin):
    """Acesso para todos os perfis logados (gerente vê só suas filiais)."""
    def test_func(self):
        return self.request.user.is_authenticated

    def get_queryset_for_user(self, queryset):
        """Filtra queryset por filiais do gerente, se aplicável."""
        user = self.request.user
        if user.is_manager():
            return queryset.filter(branch__in=user.branch.all())
        return queryset
