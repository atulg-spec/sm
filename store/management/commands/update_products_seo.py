import os
import json
import pathlib
from django.core.management.base import BaseCommand
from store.models import Product
from django.conf import settings
from google import genai
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Update product SEO fields (title, description, short_description) using Gemini with batching and state tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of products to process (legacy argument, overrides batch-size if smaller)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of products to process in this run (default: 5)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Do not save changes to the database',
        )
        parser.add_argument(
            '--reset-tracking',
            action='store_true',
            help='Reset the tracking file to process all products again',
        )

    def handle(self, *args, **options):
        # Load environment variables
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            self.stdout.write(self.style.ERROR("GOOGLE_API_KEY not found in environment variables."))
            return

        try:
            client = genai.Client(api_key=api_key)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to initialize Gemini client: {e}"))
            return

        # Tracking file path
        tracker_file = pathlib.Path("seo_processed_products.json")
        processed_ids = []

        if options['reset_tracking']:
            if tracker_file.exists():
                tracker_file.unlink()
            self.stdout.write(self.style.SUCCESS("Tracking file reset."))
        
        if tracker_file.exists():
            try:
                with open(tracker_file, 'r') as f:
                    processed_ids = json.load(f)
            except json.JSONDecodeError:
                processed_ids = []

        self.stdout.write(f"Found {len(processed_ids)} previously processed products.")

        # Filter out processed products
        products = Product.objects.exclude(id__in=processed_ids)
        
        # Apply batch size / limit
        batch_size = options['batch_size']
        if options['limit']:
             batch_size = min(options['limit'], batch_size)
        
        products = products[:batch_size]
        
        if not products.exists():
            self.stdout.write(self.style.SUCCESS("No new products to process (all pending products processed or database empty)."))
            return

        self.stdout.write(f"Starting batch of {products.count()} products...")

        for product in products:
            self.stdout.write(self.style.NOTICE(f"Processing product: {product.name} ({product.id})"))

            prompt = f"""
            You are an SEO expert. Please optimize the following product details for Google AdSense compliance and better SEO ranking.
            
            Current Title: {product.name}
            Current Short Description: {product.short_description}
            Current Description (Markdown): 
            {product.description}

            Instructions:
            1. Create a more SEO-friendly Title.
            2. specific rules:
               - The Description is in Markdown. output the new description in Markdown.
               - Make the Short Description catchy and AdSense compliant (no prohibited content, clear, concise).
            3. Return the response in this specific format with separators:
            
            ---TITLE---
            (New Title Content)
            ---SHORT_DESC---
            (New Short Description Content)
            ---DESC---
            (New Description Content in Markdown)
            """

            try:
                # Primary attempt with user-requested model
                response = client.models.generate_content(
                    model="gemini-3-flash-preview", 
                    contents=prompt
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"gemini-3-flash-preview failed ({e}), trying gemini-2.0-flash-exp..."))
                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=prompt
                    )
                except Exception as e2:
                     self.stdout.write(self.style.WARNING(f"gemini-2.0-flash-exp failed ({e2}), trying gemini-1.5-flash..."))
                     response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt
                     )

            text = response.text
            
            # Parse output
            new_title = ""
            new_short_desc = ""
            new_desc = ""

            if "---TITLE---" in text:
                parts = text.split("---TITLE---")[1].split("---SHORT_DESC---")
                new_title = parts[0].strip()
                if len(parts) > 1:
                    parts2 = parts[1].split("---DESC---")
                    new_short_desc = parts2[0].strip()
                    if len(parts2) > 1:
                        new_desc = parts2[1].strip()

            if new_title and new_desc:
                self.stdout.write("--- OLD VERSION ---")
                self.stdout.write(f"Title: {product.name}")
                self.stdout.write(f"Short Desc: {product.short_description}")
                
                self.stdout.write("--- NEW VERSION ---")
                self.stdout.write(f"Title: {new_title}")
                self.stdout.write(f"Short Desc: {new_short_desc}")

                if not options['dry_run']:
                    product.name = new_title
                    product.short_description = new_short_desc
                    product.description = new_desc
                    product.save()
                    
                    # Update tracking
                    processed_ids.append(str(product.id))
                    with open(tracker_file, 'w') as f:
                        json.dump(processed_ids, f)
                        
                    self.stdout.write(self.style.SUCCESS(f"Updated product: {product.name}"))
                else:
                    self.stdout.write(self.style.WARNING("Dry run: Changes not saved."))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to parse response for {product.name}"))
                self.stdout.write(f"Raw Response: {text[:200]}...")

