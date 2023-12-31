from __future__ import print_function #,unicode_literals
import datetime
from django.db.backends.postgresql import schema, introspection
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist

from django.db.migrations import operations, migration

#class AlterUniqueTogether( operations.AlterUniqueTogether):    too late for this
if 1:
    def database_forwards(self, app_label, schema_editor, from_state, to_state, backwards =False):
        DBG = 0
        new_model = to_state.apps.get_model(app_label, self.name)
        if self.allow_migrate_model(schema_editor.connection.alias, new_model):
            old_model = from_state.apps.get_model(app_label, self.name)
            try:
                if DBG: print( 5555, old_model._meta.get_field( 'ref_idn').null)
            except: pass
            try:
                initial_model = schema_editor._HACK_initial_state.apps.get_model(app_label, self.name)
                if DBG: print( 444, 'has initial_state')
                try:
                    if DBG: print( 6665, initial_model._meta.get_field( 'ref_idn').null)
                except: pass
            except: initial_model = old_model
            new_model._HACK_old_model = initial_model
            new_model._HACK_backwards = backwards
            schema_editor.alter_unique_together(
                new_model,
                getattr(old_model._meta, self.option_name, set()),
                getattr(new_model._meta, self.option_name, set()),
            )
    operations.AlterUniqueTogether.database_forwards = database_forwards
    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        return database_forwards( self, app_label, schema_editor, from_state, to_state, backwards= True)
    operations.AlterUniqueTogether.database_backwards = database_backwards

    _apply = migration.Migration.apply
    def apply(self, project_state, schema_editor, collect_sql=False):
        schema_editor._HACK_initial_state = project_state.clone()
        return _apply( self, project_state, schema_editor, collect_sql)
    migration.Migration.apply = apply

    _unapply = migration.Migration.unapply
    def unapply(self, project_state, schema_editor, collect_sql=False):
        schema_editor._HACK_initial_state = project_state.clone()
        return _unapply( self, project_state, schema_editor, collect_sql)
    migration.Migration.unapply = unapply

import re
class DatabaseIntrospection( introspection.DatabaseIntrospection):
    def get_constraints(self, cursor, table_name):
        constraints = super().get_constraints( cursor, table_name)
        for cc in constraints.values():
            definition = cc['definition']
            if not definition: continue
            if 'COALESCE' not in definition: continue
            #print( 888888, definition)
            collist = definition.split('USING')[1].split('(',1)[1]
            nc = re.sub( '\(COALESCE\(\s*(\S+?),.*?\)\)', r'\1', collist, )
            nc = nc.replace( '(', '')
            nc = nc.replace( ')', '')
            nc = nc.replace( '"', '')
            nc = [ c.strip() for c in nc.split(',')]
            #print( 888888, index, nc)
            if nc: cc['columns'] = nc

        return constraints


class SchemaEditor( schema.DatabaseSchemaEditor):
    sql_create_unique_index = "CREATE UNIQUE INDEX %(name)s ON %(table)s (%(columns)s)"
    coalesce_value = '--==(None)==--'
    coalesce_values = dict(
        integer= -1987654321,
        bigint = -1987654321,
        date   = datetime.date( year=1010,month=10, day=10)
        #...
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = getattr(settings, 'UNIQUE_NULLS_CONFIG', {})
        self.dont_coalesce_fields = config.get('DONT_COALESCE', {})

    def _delete_composed_index(self, model, fields, constraint_kwargs, sql):
        DBG = 0 #'Tr' in str(model)
        if DBG: print( 22222222222, model, fields, constraint_kwargs)
        columns = []
        old_model = model._HACK_old_model
        has_none = 0
        for name in fields:
            f = model._meta.get_field(name)
            if DBG: print( 'new', f, f.null)
            try:
                f = old_model._meta.get_field(name)
                if DBG: print( 'old', f, f.null)
            except FieldDoesNotExist: pass
            columns.append( f.column)
            has_none += bool(f.null)
        if has_none:#None in columns:
            constraint_kwargs['index'] = True
            sql = self.sql_delete_index
        if DBG: print( columns, fields, constraint_kwargs)
        constraint_names = self._constraint_names(model, columns, **constraint_kwargs)
        if len(constraint_names) != 1:
            raise ValueError("Found wrong number (%s) of constraints for %s(%s)" % (
                len(constraint_names),
                model._meta.db_table,
                ", ".join(str(c) for c in columns),
            ))
        self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))

    def _create_unique_sql(self, model, columns):
        DBG = 'Tr' in str(model)
        old_model = getattr( model, '_HACK_backwards', False) and getattr( model, '_HACK_old_model', None)
        dont_coalesce = self.dont_coalesce_fields.get(model._meta.label_lower, ())
        index_columns = []
        create_index = False
        for name in columns:
            f = model._meta.get_field(name)
            if DBG: print( 'cnew', f, f.null)
            if old_model:
                try:
                    f = old_model._meta.get_field(name)
                    if DBG: print( 'cold', f, f.null)
                except FieldDoesNotExist: pass

            col = self.quote_name(name)
            if f.null and name not in dont_coalesce:
                db_type = f.db_type(connection=self.connection)
                value = self.coalesce_values.get( db_type, self.coalesce_value)
                value = f.get_db_prep_save( value, self.connection)
                col = "COALESCE(%(name)s, %(special)s)" % dict(
                    name= col,
                    special= self.quote_value( value )
                )
                create_index = True
            index_columns.append( col)

        if DBG: print( 3333333333, model, columns, index_columns)
        if not create_index:
            return super()._create_unique_sql(model, columns)

        return self.sql_create_unique_index % {
            "table": self.quote_name(model._meta.db_table),
            "name": self.quote_name(self._create_index_name(model, columns, suffix="_uniq")),
            "columns": ", ".join( index_columns),    #!
        }


#XXX most of the above .old_model/initial_model will not be needed if
# AlterUniqueTogether is in separate migration - but no much luck
# operation._auto_deps cannot help, used for inter-app deps and topological_sort
#instead, this works but cannot be injected:
#in MigrationAutodetector._build_migration_list()
#inside: for operation in ...
#needs:     if isinstance( operation, operations.AlterUniqueTogether) and chopped: break

# vim:ts=4:sw=4:expandtab
