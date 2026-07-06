from django.db import models

from .context import get_current_company


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    company_code = models.SlugField(max_length=50, unique=True)
    created_on = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TenantManager(models.Manager):
    """Default manager for every tenant-scoped model.

    Automatically filters every query to the current request's company.
    Fails closed: with no company context set, returns no rows rather than
    every company's rows, so a missing middleware/context is a visible bug
    (empty pages) rather than a silent cross-tenant data leak.
    """

    def get_queryset(self):
        company = get_current_company()
        if company is None:
            return super().get_queryset().none()
        return super().get_queryset().filter(company=company)


class TenantModel(models.Model):
    """Abstract base for every company-scoped model.

    `objects` (the default manager) is tenant-scoped automatically.
    `all_objects` is the explicit escape hatch for signup (no company
    context exists yet) and admin tooling.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.company_id is None:
            self.company = get_current_company()
        super().save(*args, **kwargs)
