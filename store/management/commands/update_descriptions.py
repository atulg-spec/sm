from django.core.management.base import BaseCommand
from store.models import Product


class Command(BaseCommand):
    help = 'Update product descriptions with beautiful markdown formatting'

    def handle(self, *args, **options):
        products = Product.objects.filter(price=0)  # Only free products (Gutenberg books)
        updated_count = 0
        
        for product in products:
            # Extract author from the name (format: "Book Title - Author Name")
            name_parts = product.name.rsplit(' - ', 1) if ' - ' in product.name else [product.name, 'Unknown']
            title = name_parts[0] if len(name_parts) > 1 else product.name
            author = name_parts[1] if len(name_parts) > 1 else 'Unknown'
            
            # Get category name
            category = product.category.name if product.category else "Literature"
            
            # Get file extension
            file_ext = "EPUB" if product.digital_file and str(product.digital_file).endswith('.epub') else "Digital Format"
            
            # Create beautiful markdown description
            markdown_desc = f"""## {title}
*by {author}*

A timeless classic of literature, now free in the public domain for everyone to enjoy.

---

### 📖 Book Details

| Feature | Details |
|---------|---------|
| **Author** | {author} |
| **Category** | {category} |
| **Format** | {file_ext} (Universal e-reader format) |
| **License** | Public Domain - 100% Free |

---

### ✨ Why Download?

- **Completely Free** - No hidden costs, ever
- **Legal & Safe** - Public domain classic
- **Instant Access** - Download immediately
- **Universal Format** - Works on all devices

---

### 📜 Public Domain Notice

This book is in the **public domain** worldwide. You are free to read, share, and enjoy this literary classic without any restrictions.

---

*Source: Project Gutenberg - Free ebooks since 1971*
"""
            
            product.description = markdown_desc
            product.save()
            updated_count += 1
            self.stdout.write(f"Updated: {product.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully updated {updated_count} product descriptions!')
        )
