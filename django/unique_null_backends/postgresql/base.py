from django.db.backends.postgresql.base import *
import django.db.models.options as options
from .schema import SchemaEditor, DatabaseIntrospection


class DatabaseWrapper(DatabaseWrapper):
    SchemaEditorClass = SchemaEditor
    introspection_class = DatabaseIntrospection

