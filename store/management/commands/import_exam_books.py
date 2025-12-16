"""
Django management command to import Indian competitive exam preparation books from Archive.org.
Supports SSC, NEET, JEE, B.Ed, and other competitive exams.

Usage:
    python manage.py import_exam_books --exam ssc --count 50
    python manage.py import_exam_books --exam neet --count 30
    python manage.py import_exam_books --exam jee --count 40
    python manage.py import_exam_books --exam bed --count 20
    python manage.py import_exam_books --exam all --count 200
"""
import requests
import time
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from store.models import Product, Category

# Exam-specific search queries and categories
EXAM_CONFIGS = {
    'ssc': {
        'queries': [
            'SSC CGL',
            'SSC CHSL',
            'SSC MTS',
            'SSC CPO',
            'Staff Selection Commission',
        ],
        'category': 'SSC Exam Preparation',
        'description': 'Staff Selection Commission (SSC) exam preparation materials'
    },
    'neet': {
        'queries': [
            'NEET',
            'NEET UG',
            'NEET medical entrance',
            'medical entrance exam',
            'biology entrance exam',
        ],
        'category': 'NEET Exam Preparation',
        'description': 'National Eligibility cum Entrance Test (NEET) preparation materials'
    },
    'jee': {
        'queries': [
            'JEE Main',
            'JEE Advanced',
            'IIT JEE',
            'engineering entrance',
            'JEE preparation',
        ],
        'category': 'JEE Exam Preparation',
        'description': 'Joint Entrance Examination (JEE) preparation materials for engineering'
    },
    'bed': {
        'queries': [
            'B.Ed',
            'BED entrance',
            'Bachelor of Education',
            'teaching entrance exam',
            'education entrance',
        ],
        'category': 'B.Ed Exam Preparation',
        'description': 'Bachelor of Education (B.Ed) entrance exam preparation materials'
    },
    'upsc': {
        'queries': [
            'UPSC',
            'IAS',
            'IPS',
            'civil services',
            'UPSC preparation',
        ],
        'category': 'UPSC Exam Preparation',
        'description': 'Union Public Service Commission (UPSC) civil services exam preparation'
    },
    'gate': {
        'queries': [
            'GATE',
            'Graduate Aptitude Test',
            'GATE preparation',
        ],
        'category': 'GATE Exam Preparation',
        'description': 'Graduate Aptitude Test in Engineering (GATE) preparation materials'
    },
    'cat': {
        'queries': [
            'CAT MBA',
            'Common Admission Test',
            'CAT preparation',
            'MBA entrance',
        ],
        'category': 'CAT Exam Preparation',
        'description': 'Common Admission Test (CAT) for MBA entrance preparation'
    },
}


class Command(BaseCommand):
    help = 'Import Indian competitive exam preparation books from Archive.org'

    def add_arguments(self, parser):
        parser.add_argument(
            '--exam',
            type=str,
            default='all',
            choices=['ssc', 'neet', 'jee', 'bed', 'upsc', 'gate', 'cat', 'all'],
            help='Type of exam books to import'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of books to import per exam type'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help='Skip books that already exist'
        )

    def handle(self, *args, **options):
        exam_type = options['exam']
        count_per_exam = options['count']
        skip_existing = options['skip_existing']
        
        if exam_type == 'all':
            exams_to_import = list(EXAM_CONFIGS.keys())
        else:
            exams_to_import = [exam_type]
        
        total_imported = 0
        total_skipped = 0
        total_errors = 0
        
        for exam in exams_to_import:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'📚 Importing {exam.upper()} Exam Books...'))
            self.stdout.write('─' * 60)
            
            imported, skipped, errors = self.import_exam_books(
                exam, 
                count_per_exam, 
                skip_existing
            )
            
            total_imported += imported
            total_skipped += skipped
            total_errors += errors
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ {exam.upper()}: {imported} imported, {skipped} skipped, {errors} errors'
            ))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS('📊 Overall Import Summary'))
        self.stdout.write(f'   • Total Imported: {total_imported}')
        self.stdout.write(f'   • Total Skipped: {total_skipped}')
        if total_errors:
            self.stdout.write(self.style.ERROR(f'   • Total Errors: {total_errors}'))

    def import_exam_books(self, exam_type, count, skip_existing):
        """Import books for a specific exam type"""
        config = EXAM_CONFIGS[exam_type]
        imported = 0
        skipped = 0
        errors = 0
        
        # Try each query until we get enough books
        for query in config['queries']:
            if imported + skipped >= count:
                break
            
            books = self.search_archive_books(query, exam_type)
            
            for book in books:
                if imported + skipped >= count:
                    break
                
                try:
                    result = self.import_book(book, config, skip_existing)
                    if result == 'imported':
                        imported += 1
                        title = book.get('title', 'Unknown')
                        if isinstance(title, list):
                            title = title[0]
                        self.stdout.write(self.style.SUCCESS(
                            f'  [{imported + skipped}/{count}] ✓ {title[:60]}...'
                        ))
                    elif result == 'skipped':
                        skipped += 1
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ Error: {str(e)[:80]}'
                    ))
            
            time.sleep(1)
        
        return imported, skipped, errors

    def search_archive_books(self, query, exam_type):
        """Search Archive.org for exam preparation books"""
        url = "https://archive.org/advancedsearch.php"
        
        # Build search query
        search_query = f'({query}) AND (mediatype:texts OR mediatype:collection)'
        
        params = {
            'q': search_query,
            'fl[]': ['identifier', 'title', 'creator', 'description', 'subject', 'date', 'language'],
            'sort[]': 'downloads desc',
            'rows': 30,
            'page': 1,
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

    def import_book(self, book_data, config, skip_existing):
        """Import a single exam preparation book"""
        identifier = book_data.get('identifier', '')
        title = book_data.get('title', 'Unknown Title')
        
        if isinstance(title, list):
            title = title[0] if title else 'Unknown Title'
        
        creator = book_data.get('creator', 'Various Authors')
        if isinstance(creator, list):
            creator = creator[0] if creator else 'Various Authors'
        
        subjects = book_data.get('subject', [])
        if isinstance(subjects, str):
            subjects = [subjects]
        
        description_raw = book_data.get('description', '')
        if isinstance(description_raw, list):
            description_raw = description_raw[0] if description_raw else ''
        
        # Create slug
        slug = slugify(f"{title[:100]}-{identifier}")[:200]
        
        # Check if already exists
        if skip_existing and Product.objects.filter(slug=slug).exists():
            return 'skipped'
        
        # Get or create category
        category, _ = Category.objects.get_or_create(
            name=config['category'],
            defaults={'slug': slugify(config['category'])}
        )
        
        # Create external download URL
        external_url = f"https://archive.org/download/{identifier}"
        
        # Get cover image URL
        cover_url = f"https://archive.org/services/img/{identifier}"
        cover_content = self.download_file(cover_url)
        
        # Generate description
        description = self.generate_description(
            title, 
            creator, 
            config['category'],
            config['description'],
            subjects, 
            description_raw, 
            identifier
        )
        
        # Create product
        product = Product(
            name=title[:200],
            slug=slug,
            description=description,
            short_description=f"{config['description']}. Free study material from Archive.org."[:300],
            price=0,  # All exam books are free
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

    def generate_description(self, title, creator, category, exam_desc, subjects, description_raw, identifier):
        """Generate a rich product description for exam books"""
        subjects_text = ', '.join(subjects[:5]) if subjects else 'Exam Preparation'
        description_clean = description_raw[:400] if description_raw else f"Comprehensive study material for {category}."
        
        return f"""## {title}
*by {creator}*

{description_clean}

---

### 📚 Exam Preparation Resource

This is a valuable resource for **{exam_desc}**. Access free study materials, practice questions, and comprehensive guides to help you succeed in your exams.

---

### 📖 Resource Details

| Feature | Details |
|---------|---------|
| **Category** | {category} |
| **Author/Publisher** | {creator} |
| **Source** | Archive.org |
| **License** | Free Educational Resource |
| **Topics** | {subjects_text[:150]} |
| **Archive ID** | {identifier} |

---

### ✨ Why Download?

- **Completely Free** - No hidden costs, ever
- **Trusted Source** - From Archive.org's educational collection
- **Instant Access** - Download immediately
- **Multiple Formats** - PDF, EPUB, and more
- **Offline Study** - Download once, study anywhere

---

### 🎯 Perfect For

- Exam preparation and revision
- Self-study and practice
- Understanding key concepts
- Mock tests and practice questions
- Reference material

---

### 🔗 Download Options

Click the download button to visit Archive.org's download page where you can choose from multiple formats:
- **PDF** - For reading on any device
- **EPUB** - For e-readers
- **Kindle** - For Kindle devices
- **Text** - Plain text format
- And more!

---

### 📜 Educational Resource Notice

This material is provided for educational purposes. All content is hosted on Archive.org, a trusted non-profit digital library dedicated to universal access to knowledge.

---

*Source: Internet Archive - Free Educational Resources*
"""
