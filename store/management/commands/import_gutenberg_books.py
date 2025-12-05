"""
Django management command to import 200+ public domain books from Project Gutenberg.
Fetches books dynamically from Gutenberg API with covers and EPUB files.

Usage:
    python manage.py import_gutenberg_books --count 200
"""
import requests
import time
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from store.models import Product, Category

# Category mappings based on Gutenberg subjects
CATEGORY_MAPPINGS = {
    'fiction': 'Fiction',
    'fantasy': 'Fantasy',
    'science fiction': 'Science Fiction',
    'horror': 'Horror',
    'mystery': 'Mystery',
    'detective': 'Mystery',
    'romance': 'Romance',
    'adventure': 'Adventure',
    'poetry': 'Poetry',
    'drama': 'Drama',
    'philosophy': 'Philosophy',
    'history': 'History',
    'biography': 'Biography',
    'children': "Children's Books",
    'juvenile': "Children's Books",
    'humor': 'Humor',
    'satire': 'Satire',
    'short stories': 'Short Stories',
    'essays': 'Essays',
    'letters': 'Letters',
    'travel': 'Travel',
    'religion': 'Religion',
    'mythology': 'Mythology',
    'fairy tales': 'Fairy Tales',
    'gothic': 'Gothic Fiction',
    'war': 'War & Military',
    'western': 'Western',
    'love': 'Romance',
}


class Command(BaseCommand):
    help = 'Import 200+ public domain books from Project Gutenberg API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of books to import (max 500)'
        )
        parser.add_argument(
            '--free',
            action='store_true',
            default=True,
            help='Set all books as free'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help='Skip books that already exist'
        )
        parser.add_argument(
            '--start-page',
            type=int,
            default=1,
            help='Start from this page (32 books per page)'
        )

    def handle(self, *args, **options):
        count = min(options['count'], 500)
        is_free = options['free']
        skip_existing = options['skip_existing']
        start_page = options['start_page']
        
        self.stdout.write(self.style.SUCCESS(f'📚 Fetching {count} public domain books from Gutenberg API...'))
        self.stdout.write('')
        
        imported = 0
        skipped = 0
        errors = 0
        page = start_page
        
        while imported + skipped < count:
            # Fetch books from Gutenberg API
            books = self.fetch_gutenberg_books(page)
            
            if not books:
                self.stdout.write(self.style.WARNING(f'No more books found on page {page}'))
                break
            
            for book in books:
                if imported + skipped >= count:
                    break
                
                try:
                    result = self.import_book(book, is_free, skip_existing)
                    if result == 'imported':
                        imported += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'[{imported + skipped}/{count}] ✓ {book["title"][:50]}...'
                        ))
                    elif result == 'skipped':
                        skipped += 1
                        self.stdout.write(self.style.WARNING(
                            f'[{imported + skipped}/{count}] ⊘ {book["title"][:50]}... (exists)'
                        ))
                    
                    # Be nice to the servers
                    time.sleep(0.3)
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(
                        f'[{imported + skipped + errors}/{count}] ✗ Error: {str(e)[:50]}'
                    ))
            
            page += 1
            time.sleep(1)  # Rate limiting between pages
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'═══════════════════════════════════════'))
        self.stdout.write(self.style.SUCCESS(f'📊 Import Complete!'))
        self.stdout.write(f'   • Imported: {imported}')
        self.stdout.write(f'   • Skipped: {skipped}')
        if errors:
            self.stdout.write(self.style.ERROR(f'   • Errors: {errors}'))

    def fetch_gutenberg_books(self, page=1):
        """Fetch popular books from Gutenberg API"""
        # Gutenberg API - fetches most popular books in English
        url = f"https://gutendex.com/books/?languages=en&page={page}"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'API Error: {str(e)}'))
        
        return []

    def import_book(self, book_data, is_free, skip_existing):
        """Import a single book from Gutenberg API response"""
        gutenberg_id = book_data.get('id')
        title = book_data.get('title', 'Unknown Title')
        authors = book_data.get('authors', [])
        subjects = book_data.get('subjects', [])
        formats = book_data.get('formats', {})
        
        # Get author name
        author = authors[0].get('name', 'Unknown Author') if authors else 'Unknown Author'
        # Clean author name (remove dates like "Dickens, Charles, 1812-1870")
        if ',' in author:
            parts = author.split(',')
            if len(parts) >= 2:
                author = f"{parts[1].strip().split()[0]} {parts[0].strip()}"
        
        # Create slug
        slug = slugify(f"{title[:100]}-{author[:50]}")[:200]
        
        # Check if already exists
        if skip_existing and Product.objects.filter(slug=slug).exists():
            return 'skipped'
        
        # Determine category
        category_name = self.determine_category(subjects)
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'slug': slugify(category_name)}
        )
        
        # Get download URL (prefer EPUB)
        download_url, file_ext = self.get_best_format(formats)
        if not download_url:
            raise Exception("No downloadable format available")
        
        # Download ebook
        ebook_content = self.download_file(download_url)
        if not ebook_content:
            raise Exception("Failed to download ebook")
        
        # Download cover image
        cover_url = formats.get('image/jpeg', '')
        cover_content = self.download_file(cover_url) if cover_url else None
        
        # Create product
        product = Product(
            name=title[:200],
            slug=slug,
            description=self.generate_description(title, author, category_name, subjects, file_ext),
            short_description=f"Classic public domain book by {author}. Free to download and enjoy forever."[:300],
            price=0 if is_free else 49,
            category=category,
            featured=False,
            active=True,
        )
        product.save()
        
        # Attach digital file
        filename = f"{slug[:100]}.{file_ext}"
        product.digital_file.save(filename, ContentFile(ebook_content))
        
        # Attach cover image
        if cover_content and len(cover_content) > 1000:
            image_filename = f"{slug[:100]}-cover.jpg"
            product.image.save(image_filename, ContentFile(cover_content))
        
        product.save()
        return 'imported'

    def determine_category(self, subjects):
        """Determine the best category based on subjects"""
        subjects_lower = ' '.join(subjects).lower()
        
        for keyword, category in CATEGORY_MAPPINGS.items():
            if keyword in subjects_lower:
                return category
        
        return 'Classic Literature'

    def get_best_format(self, formats):
        """Get the best downloadable format"""
        format_priority = [
            ('application/epub+zip', 'epub'),
            ('application/x-mobipocket-ebook', 'mobi'),
            ('text/plain; charset=utf-8', 'txt'),
            ('text/plain; charset=us-ascii', 'txt'),
            ('text/plain', 'txt'),
        ]
        
        for mime_type, ext in format_priority:
            if mime_type in formats:
                return formats[mime_type], ext
        
        return None, None

    def download_file(self, url):
        """Download a file from URL"""
        if not url:
            return None
        
        try:
            headers = {
                'User-Agent': 'StartMarket/1.0 (https://startmarket.in)'
            }
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None

    def generate_description(self, title, author, category, subjects, file_format):
        """Generate a rich product description"""
        subjects_text = ', '.join(subjects[:5]) if subjects else category
        format_name = {
            'epub': 'EPUB (Universal e-reader format)',
            'mobi': 'MOBI (Kindle format)',
            'txt': 'Plain Text',
        }.get(file_format, file_format.upper())
        
        return f"""## {title}
*by {author}*

A timeless classic of literature, now free in the public domain for everyone to enjoy.

---

### 📖 Book Details

| Feature | Details |
|---------|---------|
| **Author** | {author} |
| **Category** | {category} |
| **Format** | {format_name} |
| **License** | Public Domain - 100% Free |
| **Topics** | {subjects_text[:100]} |

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
