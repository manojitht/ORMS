from datetime import datetime
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from department.models import Department
from team.models import Team

# Create your models here.

class MyManagerAccount(BaseUserManager): #the MyManagerAccount extracts from the BaseUserManager class
    def create_user(self, peoplesoft_id, first_name, last_name, email, department, team, role, ini_pas, password=None):
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
            role = role,
            ini_pas = ini_pas,
        )
        user.set_password(password)
        user.save(using=self._db) #saving details on database
        return user

    def create_manager(self, peoplesoft_id, first_name, last_name, email, department, team, role, ini_pas, password=None):
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
            role = role,
            ini_pas = ini_pas,
        )
        user.is_manager = True
        user.is_active = False
        user.set_password(password)
        user.save(using=self._db) #saving details on database
        return user

    def create_IT_admin(self, peoplesoft_id, first_name, last_name, email, department, team, role, ini_pas, password=None):
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
            role = role,
            ini_pas = ini_pas,
        )
        user.is_it_admin = True
        user.is_active = False
        user.set_password(password)
        user.save(using=self._db) #saving details on database
        return user

    def create_superuser(self, peoplesoft_id, first_name, last_name, email, department, team, role, ini_pas, password):
        user = self.create_user(
            peoplesoft_id = peoplesoft_id,
            first_name = first_name,
            last_name = last_name,
            email = self.normalize_email(email),
            department = department,
            team = team,
            password = password,
            role = role,
            ini_pas = ini_pas,
        )
        user.is_superadmin = True
        user.is_staff = True
        user.save(using=self._db) #saving details on database
        return user

class Account(AbstractBaseUser):
    peoplesoft_id = models.CharField(max_length=8, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100,unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    ini_pas = models.CharField(max_length=100)

    
    #must have fields
    date_joined = models.DateField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_superadmin = models.BooleanField('Is Superadmin',default=False)
    is_it_admin = models.BooleanField('Is IT Admin',default=False)
    is_manager = models.BooleanField('Is Manager',default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'peoplesoft_id'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'department', 'team', 'role', 'ini_pas']

    objects = MyManagerAccount()

    def __str__(self):
        return self.peoplesoft_id

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