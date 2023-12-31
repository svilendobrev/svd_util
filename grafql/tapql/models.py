from django.db import models
from svd_util.django.models import null_and_blank
from svd_util.django.models import Link as LinkTo
from django.contrib.auth import get_user_model
User = get_user_model()

class WrongInputError( RuntimeError): pass
def assert_correct_input( check, msg):
    if not check: raise WrongInputError( msg)

class aRole( models.Model):
    class Meta:
        app_label = 'tapql'
        db_table  = 'rrll'
    user    = LinkTo( User,     related_name= 'roles', )
    type    = models.CharField( max_length=20, default ='')
    level   = models.IntegerField( **null_and_blank)
Role = aRole

# vim:ts=4:sw=4:expandtab
