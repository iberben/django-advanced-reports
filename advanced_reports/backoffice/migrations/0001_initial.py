# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SearchIndex'
        db.create_table(u'backoffice_searchindex', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('backoffice_instance', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('model_slug', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('model_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('to_index', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('search_index', self.gf('djorm_pgfulltext.fields.VectorField')(default='', null=True, db_index=True)),
        ))
        db.send_create_signal(u'backoffice', ['SearchIndex'])


    def backwards(self, orm):
        # Deleting model 'SearchIndex'
        db.delete_table(u'backoffice_searchindex')


    models = {
        u'backoffice.searchindex': {
            'Meta': {'object_name': 'SearchIndex'},
            'backoffice_instance': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'model_slug': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'search_index': ('djorm_pgfulltext.fields.VectorField', [], {'default': "''", 'null': 'True', 'db_index': 'True'}),
            'to_index': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['backoffice']