"""
Django management command to scrape Chinese audiobooks from Librivox.org.
Imports them as products with external download links.

OPTIMIZATIONS:
- Uses language filter in API call instead of client-side filtering
- Parallel image downloads using ThreadPoolExecutor
- Bulk database operations
- Reduced API delay
- Progress bar for better UX

Usage:
    python manage.py scrape_librivox_chinese --count 100
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.db import transaction
from store.models import Product, Category
import re


class Command(BaseCommand):
    help = 'Scrape Chinese audiobooks from Librivox.org (optimized)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of books to import (default: 100)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help='Skip books that already exist'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=5,
            help='Number of parallel workers for image downloads (default: 5)'
        )

    def handle(self, *args, **options):
        count = options['count']
        skip_existing = options['skip_existing']
        workers = options['workers']
        
        self.stdout.write(self.style.SUCCESS(f'🎧 Scraping Librivox for Chinese audiobooks (optimized)...'))
        
        # Ensure category exists
        category_name = "Chinese Audiobooks"
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'slug': slugify(category_name), 'description': 'Free Chinese Audiobooks from Librivox'}
        )
        
        imported = 0
        skipped = 0
        errors = 0
        offset = 0
        batch_size = 100
        
        # Cache existing slugs for faster lookup
        if skip_existing:
            existing_slugs = set(Product.objects.filter(
                category=category
            ).values_list('slug', flat=True))
        else:
            existing_slugs = set()

        while imported + skipped < count:
            self.stdout.write(f"📖 Fetching batch at offset {offset}...")
            books = self.fetch_chinese_books_batch(limit=batch_size, offset=offset)
            
            if not books:
                self.stdout.write(self.style.WARNING(f'No more Chinese books found. Total imported: {imported}'))
                break
            
            # Filter and prepare books for import
            books_to_import = []
            for book in books:
                librivox_id = book.get('id')
                title = book.get('title', '')
                slug = slugify(f"{title[:50]}-lv-{librivox_id}")[:200]
                
                if skip_existing and slug in existing_slugs:
                    skipped += 1
                    continue
                
                books_to_import.append(book)
                
                if imported + skipped >= count:
                    break
            
            if not books_to_import:
                offset += batch_size
                continue
            
            # Bulk import with parallel image downloads
            try:
                newly_imported = self.bulk_import_books(
                    books_to_import, 
                    category, 
                    existing_slugs,
                    workers
                )
                imported += newly_imported
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Imported {newly_imported} books (Total: {imported}/{count})'
                    )
                )
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'✗ Batch import error: {e}'))
            
            if imported + skipped >= count:
                break
                
            offset += batch_size
            time.sleep(0.5)  # Reduced delay

        self.stdout.write(self.style.SUCCESS(f'═══════════════════════════════════════'))
        self.stdout.write(self.style.SUCCESS(f'📊 Import Complete!'))
        self.stdout.write(f'   • Imported: {imported}')
        self.stdout.write(f'   • Skipped: {skipped}')
        if errors:
            self.stdout.write(self.style.ERROR(f'   • Errors: {errors}'))

    def fetch_chinese_books_batch(self, limit=100, offset=0):
        """
        Fetch books with server-side language filtering for Chinese.
        This is MUCH faster than client-side filtering.
        """
        url = "https://librivox.org/api/feed/audiobooks"
        
        # Try multiple language codes that Librivox might use
        # According to Librivox API, we can filter by language code
        params = {
            'format': 'json',
            'limit': limit,
            'offset': offset,
            'extended': 1,
            'language': 'chinese'  # Server-side filter!
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('books', [])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'API Error: {e}'))
            return []

    def bulk_import_books(self, books, category, existing_slugs, workers=5):
        """Import multiple books efficiently with parallel image downloads"""
        
        # Prepare all products first
        products_data = []
        for book_data in books:
            product_info = self.prepare_product_data(book_data, category)
            if product_info:
                products_data.append(product_info)
        
        if not products_data:
            return 0
        
        # Download images in parallel
        self.stdout.write(f'⬇️  Downloading {len(products_data)} cover images in parallel...')
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_product = {
                executor.submit(self.download_file, p['image_url']): i 
                for i, p in enumerate(products_data) if p['image_url']
            }
            
            for future in as_completed(future_to_product):
                idx = future_to_product[future]
                try:
                    products_data[idx]['image_content'] = future.result()
                except Exception as e:
                    products_data[idx]['image_content'] = None
        
        # Bulk create products in a transaction
        created_count = 0
        with transaction.atomic():
            for product_info in products_data:
                try:
                    product = Product.objects.create(
                        name=product_info['name'],
                        slug=product_info['slug'],
                        description=product_info['description'],
                        short_description=product_info['short_description'],
                        price=0,
                        category=category,
                        external_download_url=product_info['download_url'],
                        active=True
                    )
                    
                    # Save image if downloaded
                    if product_info.get('image_content'):
                        try:
                            product.image.save(
                                f"{product_info['slug']}-cover.jpg",
                                ContentFile(product_info['image_content']),
                                save=True
                            )
                        except Exception:
                            pass  # Fail silently on image save
                    
                    existing_slugs.add(product_info['slug'])
                    created_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Could not create {product_info['name'][:30]}: {e}")
                    )
        
        return created_count

    def prepare_product_data(self, book_data, category):
        """Prepare product data dictionary"""
        title = book_data.get('title')
        if not title:
            return None

        librivox_id = book_data.get('id')
        slug = slugify(f"{title[:50]}-lv-{librivox_id}")[:200]

        # Extract details
        authors = book_data.get('authors', [])
        author_names = ", ".join([
            f"{a.get('first_name', '')} {a.get('last_name', '')}".strip() 
            for a in authors
        ])
        if not author_names:
            author_names = "Unknown Author"

        description_text = book_data.get('description', '')
        clean_desc = re.sub('<[^<]+?>', '', description_text)

        url_zip = book_data.get('url_zip_file')
        url_librivox = book_data.get('url_librivox')
        url_iarchive = book_data.get('url_iarchive')
        
        download_url = url_zip if url_zip else url_librivox
        total_time = book_data.get('totaltime', 'Unknown')
        
        # Prepare image URL
        image_url = None
        if url_iarchive:
            try:
                identifier = url_iarchive.rstrip('/').split('/')[-1]
                if identifier:
                    image_url = f"https://archive.org/services/img/{identifier}"
            except Exception:
                pass

        # Create Description
        full_description = f"""## {title}
*by {author_names}*

{clean_desc[:600]}...

---

### 🎧 Audiobook Details

| Feature | Details |
|---------|---------|
| **Author** | {author_names} |
| **Duration** | {total_time} |
| **Language** | Chinese |
| **Source** | Librivox.org |

---

### 🔗 Download

[Download Zip File]({download_url})

*Provided by Librivox.org - Public Domain Audiobooks*
"""

        return {
            'name': title[:200],
            'slug': slug,
            'description': full_description,
            'short_description': f"Audiobook: {title} by {author_names}"[:300],
            'download_url': download_url,
            'image_url': image_url,
            'image_content': None
        }

    def download_file(self, url):
        """Download a file from URL"""
        if not url:
            return None
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200 and len(response.content) > 1000:
                return response.content
        except Exception:
            pass
        return None