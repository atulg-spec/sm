from django.core.management.base import BaseCommand
from store.models import Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Creates dummy products and categories for the ecommerce site'

    def handle(self, *args, **options):
        self.stdout.write('Creating dummy categories and products...')

        # Create Categories
        categories_data = [
            {'name': 'E-Books', 'slug': 'e-books', 'description': 'Digital books and guides'},
            {'name': 'Templates', 'slug': 'templates', 'description': 'Website and design templates'},
            {'name': 'Software', 'slug': 'software', 'description': 'Digital software and tools'},
            {'name': 'Courses', 'slug': 'courses', 'description': 'Online courses and tutorials'},
            {'name': 'Graphics', 'slug': 'graphics', 'description': 'Digital graphics and assets'},
            {'name': 'Music', 'slug': 'music', 'description': 'Digital music and audio files'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))

        # Create Products
        products_data = [
            {
                'name': 'Complete Web Development Guide',
                'slug': 'complete-web-development-guide',
                'short_description': 'Master web development with this comprehensive guide covering HTML, CSS, JavaScript, and modern frameworks.',
                'description': 'This comprehensive guide covers everything you need to know about web development. From HTML and CSS basics to advanced JavaScript frameworks, React, Vue.js, and Node.js. Includes practical examples, code snippets, and real-world projects. Perfect for beginners and intermediate developers looking to level up their skills.',
                'price': Decimal('29.99'),
                'category': categories['e-books'],
                'featured': True,
            },
            {
                'name': 'Premium WordPress Theme Bundle',
                'slug': 'premium-wordpress-theme-bundle',
                'short_description': 'Get 10 premium WordPress themes with lifetime updates and support.',
                'description': 'A collection of 10 professionally designed WordPress themes perfect for any business. All themes are fully responsive, SEO optimized, and include premium plugins. Lifetime updates and support included. Themes cover ecommerce, portfolio, blog, corporate, and more.',
                'price': Decimal('79.99'),
                'category': categories['templates'],
                'featured': True,
            },
            {
                'name': 'Advanced Photo Editing Software',
                'slug': 'advanced-photo-editing-software',
                'short_description': 'Professional photo editing software with AI-powered features and unlimited exports.',
                'description': 'Professional-grade photo editing software with AI-powered features. Includes advanced filters, retouching tools, batch processing, and cloud storage. Perfect for photographers and designers. Works on Windows, Mac, and Linux. Lifetime license included.',
                'price': Decimal('149.99'),
                'category': categories['software'],
                'featured': True,
            },
            {
                'name': 'Python Mastery Course',
                'slug': 'python-mastery-course',
                'short_description': 'Learn Python from scratch to advanced level with hands-on projects and certifications.',
                'description': 'Complete Python programming course covering basics to advanced topics. Includes 50+ hours of video content, coding exercises, real-world projects, and a certificate of completion. Learn data science, web development, automation, and more with Python.',
                'price': Decimal('99.99'),
                'category': categories['courses'],
                'featured': True,
            },
            {
                'name': 'Premium Icon Pack - 1000 Icons',
                'slug': 'premium-icon-pack-1000',
                'short_description': 'Professional icon set with 1000+ customizable icons in multiple formats.',
                'description': 'A collection of 1000+ professionally designed icons perfect for web and mobile applications. Available in SVG, PNG, and AI formats. Multiple styles included: outline, filled, and colored. Fully customizable and royalty-free for commercial use.',
                'price': Decimal('19.99'),
                'category': categories['graphics'],
            },
            {
                'name': 'Digital Marketing Playbook',
                'slug': 'digital-marketing-playbook',
                'short_description': 'Complete guide to digital marketing strategies, SEO, social media, and advertising.',
                'description': 'Comprehensive digital marketing guide covering SEO, social media marketing, email campaigns, PPC advertising, content marketing, and analytics. Includes templates, checklists, and case studies from successful campaigns. Perfect for marketers and business owners.',
                'price': Decimal('39.99'),
                'category': categories['e-books'],
            },
            {
                'name': 'React Dashboard Template',
                'slug': 'react-dashboard-template',
                'short_description': 'Modern React dashboard template with TypeScript, Tailwind CSS, and 20+ components.',
                'description': 'Professional React dashboard template built with TypeScript and Tailwind CSS. Includes 20+ pre-built components, dark mode, responsive design, authentication system, and comprehensive documentation. Perfect for SaaS applications and admin panels.',
                'price': Decimal('49.99'),
                'category': categories['templates'],
            },
            {
                'name': 'Productivity Suite Pro',
                'slug': 'productivity-suite-pro',
                'short_description': 'All-in-one productivity software with task management, calendar, notes, and time tracking.',
                'description': 'Complete productivity suite featuring task management, calendar integration, note-taking, time tracking, and team collaboration tools. Syncs across all devices. Perfect for individuals and teams looking to boost productivity and organization.',
                'price': Decimal('59.99'),
                'category': categories['software'],
            },
            {
                'name': 'UI/UX Design Fundamentals',
                'slug': 'ui-ux-design-fundamentals',
                'short_description': 'Learn UI/UX design principles, tools, and best practices from industry experts.',
                'description': 'Comprehensive UI/UX design course covering design principles, user research, wireframing, prototyping, and usability testing. Learn to use Figma, Adobe XD, and Sketch. Includes portfolio projects and design system templates.',
                'price': Decimal('89.99'),
                'category': categories['courses'],
            },
            {
                'name': 'Royalty-Free Music Library',
                'slug': 'royalty-free-music-library',
                'short_description': 'Collection of 500+ royalty-free music tracks for videos, podcasts, and projects.',
                'description': 'Extensive library of 500+ high-quality royalty-free music tracks. Perfect for YouTube videos, podcasts, commercials, and other projects. Multiple genres included: ambient, corporate, cinematic, electronic, and more. Commercial license included.',
                'price': Decimal('34.99'),
                'category': categories['music'],
            },
            {
                'name': 'Data Science with Python',
                'slug': 'data-science-with-python',
                'short_description': 'Complete data science course covering pandas, numpy, matplotlib, and machine learning.',
                'description': 'Learn data science from scratch using Python. Covers data analysis, visualization, statistical modeling, and machine learning. Includes real-world datasets, Jupyter notebooks, and hands-on projects. Perfect for aspiring data scientists.',
                'price': Decimal('119.99'),
                'category': categories['courses'],
            },
            {
                'name': 'Premium Logo Design Pack',
                'slug': 'premium-logo-design-pack',
                'short_description': '100+ professional logo templates in various styles and industries.',
                'description': 'Collection of 100+ professionally designed logo templates. Covers various industries and styles: modern, minimalist, vintage, and corporate. All files in vector format (AI, EPS, SVG) and fully editable. Perfect for startups and businesses.',
                'price': Decimal('24.99'),
                'category': categories['graphics'],
            },
        ]

        # Create Free Products
        free_products_data = [
            {
                'name': 'Free Starter Template Pack',
                'slug': 'free-starter-template-pack',
                'short_description': 'Get started with 5 professional website templates - completely free!',
                'description': 'A collection of 5 beautifully designed website templates perfect for beginners. Includes HTML, CSS, and JavaScript files. Responsive design, modern UI, and easy to customize. Great for learning web development or starting your first project.',
                'price': Decimal('0.00'),
                'category': categories['templates'],
                'featured': True,
            },
            {
                'name': 'Free Icon Set - 50 Icons',
                'slug': 'free-icon-set-50',
                'short_description': '50 high-quality icons in multiple formats - free download!',
                'description': 'A curated set of 50 professional icons perfect for web and mobile projects. Available in SVG and PNG formats. Multiple styles included. Completely free for personal and commercial use. No attribution required.',
                'price': Decimal('0.00'),
                'category': categories['graphics'],
            },
            {
                'name': 'Free E-Book: Getting Started with Web Development',
                'slug': 'free-ebook-web-development',
                'short_description': 'Complete beginner guide to web development - absolutely free!',
                'description': 'A comprehensive guide covering HTML, CSS, and JavaScript basics. Perfect for absolute beginners. Includes practical examples, exercises, and tips. Learn at your own pace with this free resource.',
                'price': Decimal('0.00'),
                'category': categories['e-books'],
            },
            {
                'name': 'Free UI Kit - Minimal Design',
                'slug': 'free-ui-kit-minimal',
                'short_description': 'Clean and minimal UI components for your next project.',
                'description': 'A collection of minimal UI components including buttons, forms, cards, and navigation elements. Perfect for modern web applications. Includes Figma and Sketch files. Free for personal and commercial use.',
                'price': Decimal('0.00'),
                'category': categories['templates'],
            },
            {
                'name': 'Free Stock Photos Pack',
                'slug': 'free-stock-photos-pack',
                'short_description': '20 high-resolution stock photos for your projects.',
                'description': 'A collection of 20 professional stock photos covering various themes: business, technology, nature, and lifestyle. All images are high-resolution and free to use for any purpose. Perfect for websites, presentations, and social media.',
                'price': Decimal('0.00'),
                'category': categories['graphics'],
            },
            {
                'name': 'Free Code Snippets Library',
                'slug': 'free-code-snippets-library',
                'short_description': 'Useful code snippets for common web development tasks.',
                'description': 'A library of 30+ ready-to-use code snippets for JavaScript, CSS, and HTML. Includes form validation, animations, responsive layouts, and more. Copy-paste ready code that saves you time. Free for all developers.',
                'price': Decimal('0.00'),
                'category': categories['software'],
            },
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                slug=product_data['slug'],
                defaults=product_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Product already exists: {product.name}'))

        # Create free products
        self.stdout.write('\nCreating free products...')
        for product_data in free_products_data:
            product, created = Product.objects.get_or_create(
                slug=product_data['slug'],
                defaults=product_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created free product: {product.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Free product already exists: {product.name}'))

        self.stdout.write(self.style.SUCCESS('\nSuccessfully created all products!'))

