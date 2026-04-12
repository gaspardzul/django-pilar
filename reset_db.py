import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

print("Limpiando base de datos PostgreSQL...")

with connection.cursor() as cursor:
    # Drop all schemas except system ones
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
    """)
    schemas = cursor.fetchall()
    
    for (schema,) in schemas:
        print(f"  Eliminando schema: {schema}")
        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    
    # Recreate public schema
    print("  Recreando schema public...")
    cursor.execute('DROP SCHEMA IF EXISTS public CASCADE')
    cursor.execute('CREATE SCHEMA public')

print("✓ Base de datos limpiada exitosamente")
