"""
Quick setup script for the ecommerce project.
Run this after installing dependencies to set up the database and create dummy products.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    print("Setting up ecommerce project...")
    
    # Run migrations
    print("\n1. Running migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create dummy products
    print("\n2. Creating dummy products...")
    execute_from_command_line(['manage.py', 'create_dummy_products'])
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Build Tailwind CSS: npm run build-css")
    print("3. Run the server: python manage.py runserver")
    print("4. Visit http://127.0.0.1:8000")

