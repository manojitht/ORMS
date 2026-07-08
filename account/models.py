from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from department.models import Department
from team.models import Team
from employees.models import Employee

from companies.models import TenantModel

# Account is both the auth user model (needs unrestricted lookups for
# login/password-reset, which happen before any company context exists)
# and a tenant-scoped resource once authenticated. Rather than auto-scope
# reads like TenantManager does for every other model (which would break
# authentication), `objects` here stays unscoped and every authenticated
# view that queries Account explicitly filters by `company=` itself.
class MyManagerAccount(BaseUserManager):
    def create_user(self, peoplesoft_id, first_name, last_name, email, department, team, ini_pas, company, password=None):
        if not peoplesoft_id:
            raise ValueError('User should have a peoplesoft id')

        if not email:
            raise ValueError('User should have an email address')

        user = self.model(
            peoplesoft_id = peoplesoft_id,
            first_name = first_name,
            last_name = last_name,
            email = self.normalize_email(email), #the normalize email makes the caps letter into small letter
            department = department,
            team = team,
            ini_pas = ini_pas,
            company = company,
        )
        user.set_password(password)
        user.save(using=self._db) #saving details on database
        return user

    def create_manager(self, peoplesoft_id, first_name, last_name, email, department, team, ini_pas, company, password=None):
        if not peoplesoft_id:
            raise ValueError('User should have a peoplesoft id')

        if not email:
            raise ValueError('User should have an email address')

        user = self.model(
            peoplesoft_id = peoplesoft_id,
            first_name = first_name,
            last_name = last_name,
            email = self.normalize_email(email), #the normalize email makes the caps letter into small letter
            department = department,
            team = team,
            ini_pas = ini_pas,
            company = company,
        )
        user.is_manager = True
        user.is_active = False
        user.set_password(password)
        user.save(using=self._db) #saving details on database
        return user

    def create_IT_admin(self, peoplesoft_id, first_name, last_name, email, department, team, ini_pas, company, password=None):
        if not peoplesoft_id:
            raise ValueError('User should have a peoplesoft id')

        if not email:
            raise ValueError('User should have an email address')

        user = self.model(
            peoplesoft_id = peoplesoft_id,
            first_name = first_name,
            last_name = last_name,
            email = self.normalize_email(email), #the normalize email makes the caps letter into small letter
            department = department,
            team = team,
            ini_pas = ini_pas,
            company = company,
        )
        user.is_it_admin = True
        user.is_active = False
        user.set_password(password)
        user.save(using=self._db) #saving details on database
        return user

    def create_employee(self, peoplesoft_id, first_name, last_name, email, department, team, ini_pas, company, employee, password=None):
        if not peoplesoft_id:
            raise ValueError('User should have a peoplesoft id')

        if not email:
            raise ValueError('User should have an email address')

        user = self.model(
            peoplesoft_id = peoplesoft_id,
            first_name = first_name,
            last_name = last_name,
            email = self.normalize_email(email),
            department = department,
            team = team,
            ini_pas = ini_pas,
            company = company,
            employee_profile = employee,
        )
        user.is_employee = True
        user.is_active = False
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, peoplesoft_id, first_name, last_name, email, department, team, ini_pas, company, password):
        user = self.create_user(
            peoplesoft_id = peoplesoft_id,
            first_name = first_name,
            last_name = last_name,
            email = self.normalize_email(email),
            department = department,
            team = team,
            password = password,
            ini_pas = ini_pas,
            company = company,
        )
        user.is_superadmin = True
        user.is_staff = True
        user.save(using=self._db) #saving details on database
        return user

class Account(AbstractBaseUser, TenantModel):
    # peoplesoft_id stays globally unique (not per-company): Django hard-requires
    # USERNAME_FIELD to be globally unique (auth.E003), so login is peoplesoft_id +
    # password exactly as before — no company selector needed, since peoplesoft_id
    # alone already disambiguates which company an account belongs to.
    peoplesoft_id = models.CharField(max_length=8, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    ini_pas = models.CharField(max_length=100)

    date_joined = models.DateField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_superadmin = models.BooleanField('Is Superadmin',default=False)
    is_it_admin = models.BooleanField('Is IT Admin',default=False)
    is_manager = models.BooleanField('Is Manager',default=False)
    is_employee = models.BooleanField('Is Employee', default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    # Links a self-service Employee login back to their Employee record.
    # Nullable/SET_NULL since only employees granted portal access have one --
    # every other role leaves this blank. Account owns the link (not the
    # reverse) since Account is the actor/auth model; `related_name='account'`
    # lets templates check `employee.account` for "has portal access".
    employee_profile = models.OneToOneField(
        Employee, null=True, blank=True, on_delete=models.SET_NULL, related_name='account')

    USERNAME_FIELD = 'peoplesoft_id'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'department', 'team', 'ini_pas', 'company']

    objects = MyManagerAccount()

    class Meta:
        unique_together = ('company', 'email')

    def __str__(self):
        return self.peoplesoft_id

    # Why this matters: several models (Ticket.created_ps_id/assigned_to,
    # Employee.manager_peoplesoft_id, ResourceTaken.manager_peoplesoft_id...)
    # store "which account" as a plain peoplesoft_id CharField instead of a
    # ForeignKey. Passing an Account instance straight into a filter/get on
    # one of those fields (e.g. `Ticket.objects.filter(created_ps_id=account)`)
    # still works, because Django's CharField comparison calls `str()` on
    # the right-hand side, and str(account) is exactly this method. It reads
    # like a FK lookup but isn't one -- there's no real foreign key, no
    # on_delete behavior, and no join; it's a string equality match that
    # happens to line up. Keep that in mind before "simplifying" one of
    # these comparisons, and before renaming/reformatting peoplesoft_id.

    @property
    def role(self):
        """Computed from the boolean flags rather than stored separately --
        a stored role string that had to be kept in sync by hand was a real
        drift risk (an unvalidated write could set the label without the
        matching permission, or vice versa). This makes the booleans the
        single source of truth.
        """
        if self.is_superadmin:
            return 'Superadmin'
        if self.is_it_admin:
            return 'IT Administrator'
        if self.is_manager:
            return 'Manager'
        if self.is_employee:
            return 'Employee'
        return ''

    def has_perm(self, perm, obj=None):
        return self.is_superadmin

    def has_module_perms(self, add_label):
        return True

class AccountProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    home_address = models.CharField(blank=True, max_length=200)
    contact_number = models.CharField(blank=True, max_length=20)
    profile_image = models.ImageField(blank=True, upload_to='photos/profilepics')

    def __str__(self):
        return self.user.peoplesoft_id
