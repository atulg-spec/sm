"""
Django management command to import Cosplay books from Archive.org.
Uses external download URLs instead of downloading files locally.

Usage:
    python manage.py import_cosplay_books --count 100
"""
import requests
import time
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from store.models import Product, Category

# Category mappings based on Archive.org subjects
CATEGORY_MAPPINGS = {
    'sewing': 'Cosplay Sewing',
    'costume': 'Cosplay Costume Making',
    'armor': 'Cosplay Armor',
    'prop': 'Cosplay Props',
    'makeup': 'Cosplay Makeup',
    'hair': 'Cosplay Wigs & Hair',
    'wig': 'Cosplay Wigs & Hair',
    'photography': 'Cosplay Photography',
    'pattern': 'Cosplay Patterns',
    'fashion': 'Cosplay Fashion',
    'design': 'Cosplay Design',
    'art': 'Cosplay Art',
    'craft': 'Cosplay Crafting',
    'tutorial': 'Cosplay Tutorials',
    'reference': 'Cosplay Reference',
}


class Command(BaseCommand):
    help = 'Import Cosplay books from Archive.org using external download URLs'

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
        
        self.stdout.write(self.style.SUCCESS(f'🎭 Fetching {count} Cosplay books from Archive.org...'))
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
        """Fetch Cosplay books from Archive.org Advanced Search API"""
        # Archive.org Advanced Search API
        url = "https://archive.org/advancedsearch.php"
        # Search for cosplay related texts
        query = '(subject:cosplay OR title:cosplay OR subject:"costume design" OR subject:"costume making") AND mediatype:texts'
        
        params = {
            'q': query,
            'fl[]': ['identifier', 'title', 'creator', 'description', 'subject', 'date', 'language'],
            'sort[]': 'downloads desc',  # Trending/Most read
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
            category_name = self.determine_category(subjects, title)
        
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
            short_description=f"Cosplay and costume making resource from Archive.org. Free to download."[:300],
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

    def determine_category(self, subjects, title):
        """Determine the best category based on subjects"""
        # Default category
        default = 'Cosplay Guides'
        
        # Combine title and subjects for better matching
        search_text = (title + ' ' + ' '.join(subjects if subjects else [])).lower()
        
        for keyword, category in CATEGORY_MAPPINGS.items():
            if keyword in search_text:
                return category
        
        return default

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
        description_clean = description_raw[:800] if description_raw else "A comprehensive resource for cosplayers from Archive.org's collection."
        
        return f"""## {title}
*by {creator}*

{description_clean}

---

### 🎭 Book Details

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
- **Level Up Your Cosplay** - Learn new techniques and skills
- **Instant Access** - Download immediately
- **Community Driven** - Part of the global maker community

---

### 📜 About Archive.org

This book is hosted on **Archive.org** (Internet Archive), a non-profit library of millions of free books, movies, music, and more.

---

### 🔗 Download Options

Click the download button to visit Archive.org's download page where you can choose from multiple formats including:
- PDF
- EPUB
- Kindle
- Plain Text

---

*Source: Internet Archive - Universal Access to All Knowledge*
"""
