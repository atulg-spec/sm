"""
Django management command to import Chinese books from Archive.org.
Uses external download URLs instead of downloading files locally.

Usage:
    python manage.py import_archive_chinese_books --count 100
"""
import requests
import time
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from store.models import Product, Category

# Category mappings based on Archive.org subjects
CATEGORY_MAPPINGS = {
    'fiction': 'Chinese Fiction',
    'novel': 'Chinese Fiction',
    'poetry': 'Chinese Poetry',
    'poem': 'Chinese Poetry',
    'history': 'Chinese History',
    'philosophy': 'Chinese Philosophy',
    'religion': 'Chinese Religion',
    'buddhism': 'Chinese Religion',
    'taoism': 'Chinese Religion',
    'confucianism': 'Chinese Philosophy',
    'literature': 'Chinese Literature',
    'drama': 'Chinese Drama',
    'essay': 'Chinese Essays',
    'biography': 'Chinese Biography',
    'children': 'Chinese Children\'s Books',
    'science': 'Chinese Science',
    'medicine': 'Chinese Medicine',
    'art': 'Chinese Art',
    'music': 'Chinese Music',
    'cooking': 'Chinese Cooking',
}


class Command(BaseCommand):
    help = 'Import Chinese books from Archive.org using external download URLs'

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
            '--start-page',
            type=int,
            default=1,
            help='Start from this page (50 books per page)'
        )
        parser.add_argument(
            '--category',
            type=str,
            default=None,
            help='Override category for all books'
        )

    def handle(self, *args, **options):
        count = options['count']
        skip_existing = options['skip_existing']
        start_page = options['start_page']
        override_category = options['category']
        
        self.stdout.write(self.style.SUCCESS(f'📚 Fetching {count} Chinese books from Archive.org...'))
        self.stdout.write('')
        
        imported = 0
        skipped = 0
        errors = 0
        page = start_page
        
        while imported + skipped < count:
            # Fetch books from Archive.org API
            books = self.fetch_archive_books(page)
            
            if not books:
                self.stdout.write(self.style.WARNING(f'No more books found on page {page}'))
                break
            
            for book in books:
                if imported + skipped >= count:
                    break
                
                try:
                    result = self.import_book(book, skip_existing, override_category)
                    if result == 'imported':
                        imported += 1
                        title = book.get('title', 'Unknown')[:50]
                        self.stdout.write(self.style.SUCCESS(
                            f'[{imported + skipped}/{count}] ✓ {title}...'
                        ))
                    elif result == 'skipped':
                        skipped += 1
                        title = book.get('title', 'Unknown')[:50]
                        self.stdout.write(self.style.WARNING(
                            f'[{imported + skipped}/{count}] ⊘ {title}... (exists)'
                        ))
                    
                    # Be nice to the servers
                    time.sleep(0.5)
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(
                        f'[{imported + skipped + errors}/{count}] ✗ Error: {str(e)[:80]}'
                    ))
            
            page += 1
            time.sleep(2)  # Rate limiting between pages
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'═══════════════════════════════════════'))
        self.stdout.write(self.style.SUCCESS(f'📊 Import Complete!'))
        self.stdout.write(f'   • Imported: {imported}')
        self.stdout.write(f'   • Skipped: {skipped}')
        if errors:
            self.stdout.write(self.style.ERROR(f'   • Errors: {errors}'))

    def fetch_archive_books(self, page=1):
        """Fetch Chinese books from Archive.org Advanced Search API"""
        # Archive.org Advanced Search API
        # Search for Chinese language texts
        url = "https://archive.org/advancedsearch.php"
        params = {
            'q': 'language:(Chinese OR zh OR chi) AND mediatype:texts',
            'fl[]': ['identifier', 'title', 'creator', 'description', 'subject', 'date', 'language'],
            'sort[]': 'downloads desc',  # Most popular first
            'rows': 50,
            'page': page,
            'output': 'json'
        }
        
        try:
            headers = {
                'User-Agent': 'StartMarket/1.0 (https://startmarket.in)'
            }
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                return docs
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'API Error: {str(e)}'))
        
        return []

    def import_book(self, book_data, skip_existing, override_category):
        """Import a single book from Archive.org API response"""
        identifier = book_data.get('identifier', '')
        title = book_data.get('title', 'Unknown Title')
        
        # Handle title if it's a list
        if isinstance(title, list):
            title = title[0] if title else 'Unknown Title'
        
        # Get creator/author
        creator = book_data.get('creator', 'Unknown Author')
        if isinstance(creator, list):
            creator = creator[0] if creator else 'Unknown Author'
        
        # Get subjects
        subjects = book_data.get('subject', [])
        if isinstance(subjects, str):
            subjects = [subjects]
        
        # Get description
        description_raw = book_data.get('description', '')
        if isinstance(description_raw, list):
            description_raw = description_raw[0] if description_raw else ''
        
        # Create slug
        slug = slugify(f"{title[:100]}-{identifier}")[:200]
        
        # Check if already exists
        if skip_existing and Product.objects.filter(slug=slug).exists():
            return 'skipped'
        
        # Determine category
        if override_category:
            category_name = override_category
        else:
            category_name = self.determine_category(subjects)
        
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'slug': slugify(category_name)}
        )
        
        # Create external download URL
        external_url = f"https://archive.org/download/{identifier}"
        
        # Get cover image URL
        cover_url = f"https://archive.org/services/img/{identifier}"
        
        # Download cover image
        cover_content = self.download_file(cover_url)
        
        # Create product
        product = Product(
            name=title[:200],
            slug=slug,
            description=self.generate_description(title, creator, category_name, subjects, description_raw, identifier),
            short_description=f"Chinese book from Archive.org. Free to download and enjoy forever."[:300],
            price=0,  # All books are free
            category=category,
            external_download_url=external_url,
            featured=False,
            active=True,
        )
        product.save()
        
        # Attach cover image
        if cover_content and len(cover_content) > 1000:
            image_filename = f"{slug[:100]}-cover.jpg"
            product.image.save(image_filename, ContentFile(cover_content))
        
        product.save()
        return 'imported'

    def determine_category(self, subjects):
        """Determine the best category based on subjects"""
        if not subjects:
            return 'Chinese Literature'
        
        subjects_lower = ' '.join(subjects).lower()
        
        for keyword, category in CATEGORY_MAPPINGS.items():
            if keyword in subjects_lower:
                return category
        
        return 'Chinese Literature'

    def download_file(self, url):
        """Download a file from URL"""
        if not url:
            return None
        
        try:
            headers = {
                'User-Agent': 'StartMarket/1.0 (https://startmarket.in)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None

    def generate_description(self, title, creator, category, subjects, description_raw, identifier):
        """Generate a rich product description"""
        subjects_text = ', '.join(subjects[:5]) if subjects else category
        
        # Clean description
        description_clean = description_raw[:500] if description_raw else "A classic Chinese book from Archive.org's collection."
        
        return f"""## {title}
*by {creator}*

{description_clean}

---

### 📖 Book Details

| Feature | Details |
|---------|---------|
| **Author** | {creator} |
| **Category** | {category} |
| **Source** | Archive.org |
| **License** | Public Domain / Open Access |
| **Topics** | {subjects_text[:150]} |
| **Archive ID** | {identifier} |

---

### ✨ Why Download?

- **Completely Free** - No hidden costs, ever
- **Legal & Safe** - From Archive.org's trusted collection
- **Instant Access** - Download immediately
- **Preserve Culture** - Help preserve Chinese literary heritage

---

### 📜 About Archive.org

This book is hosted on **Archive.org** (Internet Archive), a non-profit library of millions of free books, movies, music, and more. By downloading this book, you're supporting digital preservation efforts.

---

### 🔗 Download Options

Click the download button to visit Archive.org's download page where you can choose from multiple formats including:
- PDF
- EPUB
- Kindle
- Plain Text
- And more!

---

*Source: Internet Archive - Universal Access to All Knowledge*
"""
