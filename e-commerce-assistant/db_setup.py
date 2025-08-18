#!/usr/bin/env python3
"""
E-commerce Assistant Database Setup
Creates mock database with products, orders, customers, and related data for testing.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
import ssl
from faker import Faker
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Faker for generating realistic data
fake = Faker()

class EcommerceDBSetup:
    def __init__(self):
        """Initialize database setup with MongoDB."""
        self.mongo_uri = os.getenv('MONGO_DB_URI', 'mongodb://localhost:27017')
        self.db_name = os.getenv('MONGODB_DATABASE', 'ecommerce_assistant')
        self.client = None
        self.db = None
        
    def connect(self):
        """Connect to MongoDB database."""
        try:
            # For MongoDB Atlas, use default SSL settings
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=10000
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.info(f"Connected to MongoDB: {self.db_name}")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def drop_collections(self):
        """Drop all collections to start fresh."""
        try:
            collections = [
                'categories', 'products', 'customers', 'customer_addresses',
                'orders', 'product_reviews', 'coupons', 'shopping_cart', 'wishlist'
            ]
            
            for collection_name in collections:
                self.db[collection_name].drop()
            
            logger.info("All collections dropped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop collections: {e}")
            return False
    
    def create_collections(self):
        """Create all necessary collections and indexes for e-commerce system."""
        try:
            # Create collections with validation schemas
            
            # Categories collection
            self.db.create_collection('categories')
            self.db.categories.create_index('name', unique=True)
            self.db.categories.create_index('parent_id')
            
            # Products collection
            self.db.create_collection('products')
            self.db.products.create_index('sku', unique=True)
            self.db.products.create_index('category_id')
            self.db.products.create_index('brand')
            self.db.products.create_index('price')
            self.db.products.create_index('featured')
            self.db.products.create_index('is_active')
            self.db.products.create_index([('name', 'text'), ('description', 'text')])
            
            # Product images collection
            self.db.create_collection('product_images')
            self.db.product_images.create_index('product_id')
            self.db.product_images.create_index('is_primary')
            
            # Customers collection
            self.db.create_collection('customers')
            self.db.customers.create_index('email', unique=True)
            self.db.customers.create_index('is_active')
            
            # Customer addresses collection
            self.db.create_collection('customer_addresses')
            self.db.customer_addresses.create_index('customer_id')
            self.db.customer_addresses.create_index('is_default')
            
            # Orders collection
            self.db.create_collection('orders')
            self.db.orders.create_index('order_number', unique=True)
            self.db.orders.create_index('customer_id')
            self.db.orders.create_index('status')
            self.db.orders.create_index('created_at')
            self.db.orders.create_index('payment_status')
            
            # Order items collection
            self.db.create_collection('order_items')
            self.db.order_items.create_index('order_id')
            self.db.order_items.create_index('product_id')
            
            # Shopping cart collection
            self.db.create_collection('shopping_cart')
            self.db.shopping_cart.create_index([('customer_id', 1), ('product_id', 1)], unique=True)
            
            # Wishlist collection
            self.db.create_collection('wishlist')
            self.db.wishlist.create_index([('customer_id', 1), ('product_id', 1)], unique=True)
            
            # Product reviews collection
            self.db.create_collection('product_reviews')
            self.db.product_reviews.create_index('product_id')
            self.db.product_reviews.create_index('customer_id')
            self.db.product_reviews.create_index('rating')
            self.db.product_reviews.create_index('is_verified_purchase')
            
            # Coupons collection
            self.db.create_collection('coupons')
            self.db.coupons.create_index('code', unique=True)
            self.db.coupons.create_index('is_active')
            self.db.coupons.create_index('valid_from')
            self.db.coupons.create_index('valid_until')
            
            logger.info("All collections and indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collections: {e}")
            return False
    
    def insert_categories(self):
        """Insert product categories."""
        categories = [
            # Main categories
            {'name': 'Electronics', 'description': 'Electronic devices and accessories', 'parent_id': None, 'created_at': datetime.now()},
            {'name': 'Clothing', 'description': 'Fashion and apparel', 'parent_id': None, 'created_at': datetime.now()},
            {'name': 'Home & Garden', 'description': 'Home improvement and garden supplies', 'parent_id': None, 'created_at': datetime.now()},
            {'name': 'Sports & Outdoors', 'description': 'Sports equipment and outdoor gear', 'parent_id': None, 'created_at': datetime.now()},
            {'name': 'Books', 'description': 'Books and educational materials', 'parent_id': None, 'created_at': datetime.now()},
            {'name': 'Beauty & Health', 'description': 'Beauty products and health items', 'parent_id': None, 'created_at': datetime.now()},
            {'name': 'Toys & Games', 'description': 'Toys, games, and entertainment', 'parent_id': None, 'created_at': datetime.now()},
            {'name': 'Automotive', 'description': 'Car parts and accessories', 'parent_id': None, 'created_at': datetime.now()},
        ]
        
        try:
            # Insert main categories
            result = self.db.categories.insert_many(categories)
            main_category_ids = result.inserted_ids
            
            # Get Electronics category ID for sub-categories
            electronics_category = self.db.categories.find_one({'name': 'Electronics'})
            electronics_id = electronics_category['_id']
            
            # Sub-categories for Electronics
            sub_categories = [
                {'name': 'Smartphones', 'description': 'Mobile phones and accessories', 'parent_id': electronics_id, 'created_at': datetime.now()},
                {'name': 'Laptops', 'description': 'Laptops and notebooks', 'parent_id': electronics_id, 'created_at': datetime.now()},
                {'name': 'Headphones', 'description': 'Audio devices and headphones', 'parent_id': electronics_id, 'created_at': datetime.now()},
                {'name': 'Gaming', 'description': 'Gaming consoles and accessories', 'parent_id': electronics_id, 'created_at': datetime.now()},
            ]
            
            # Insert sub-categories
            self.db.categories.insert_many(sub_categories)
            
            logger.info(f"Inserted {len(categories) + len(sub_categories)} categories successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert categories: {e}")
            return False
    
    def insert_products(self):
        """Insert sample products."""
        try:
            # Get category IDs for reference
            smartphones_category = self.db.categories.find_one({'name': 'Smartphones'})
            laptops_category = self.db.categories.find_one({'name': 'Laptops'})
            headphones_category = self.db.categories.find_one({'name': 'Headphones'})
            clothing_category = self.db.categories.find_one({'name': 'Clothing'})
            home_category = self.db.categories.find_one({'name': 'Home & Garden'})
            sports_category = self.db.categories.find_one({'name': 'Sports & Outdoors'})
            books_category = self.db.categories.find_one({'name': 'Books'})
            beauty_category = self.db.categories.find_one({'name': 'Beauty & Health'})
            toys_category = self.db.categories.find_one({'name': 'Toys & Games'})
            
            products = [
                # Electronics - Smartphones
                {
                    'name': 'iPhone 15 Pro Max',
                    'description': 'Latest flagship iPhone with A17 Pro chip, titanium design, and advanced camera system',
                    'category_id': smartphones_category['_id'],
                    'price': 1199.99,
                    'original_price': 1299.99,
                    'stock_quantity': 50,
                    'sku': 'IPHONE15PM-256GB',
                    'brand': 'Apple',
                    'color': 'Natural Titanium',
                    'size': '256GB',
                    'weight': 0.22,
                    'is_active': True,
                    'featured': True,
                    'rating': 4.8,
                    'review_count': 245,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                {
                    'name': 'Samsung Galaxy S24 Ultra',
                    'description': 'Premium Android smartphone with S Pen, 200MP camera, and AI features',
                    'category_id': smartphones_category['_id'],
                    'price': 1099.99,
                    'original_price': 1199.99,
                    'stock_quantity': 35,
                    'sku': 'GALAXY-S24U-512GB',
                    'brand': 'Samsung',
                    'color': 'Phantom Black',
                    'size': '512GB',
                    'weight': 0.23,
                    'is_active': True,
                    'featured': True,
                    'rating': 4.6,
                    'review_count': 189,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                
                # Electronics - Laptops
                {
                    'name': 'MacBook Air M3',
                    'description': '13-inch laptop with M3 chip, all-day battery life, and stunning Liquid Retina display',
                    'category_id': laptops_category['_id'],
                    'price': 1299.99,
                    'original_price': 1399.99,
                    'stock_quantity': 25,
                    'sku': 'MBA-M3-13-512GB',
                    'brand': 'Apple',
                    'color': 'Space Gray',
                    'size': '13-inch',
                    'weight': 1.24,
                    'is_active': True,
                    'featured': True,
                    'rating': 4.7,
                    'review_count': 156,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                {
                    'name': 'Dell XPS 13 Plus',
                    'description': 'Ultra-thin laptop with Intel 12th Gen processors and InfinityEdge display',
                    'category_id': laptops_category['_id'],
                    'price': 999.99,
                    'original_price': 1199.99,
                    'stock_quantity': 18,
                    'sku': 'DELL-XPS13P-16GB',
                    'brand': 'Dell',
                    'color': 'Platinum Silver',
                    'size': '13.4-inch',
                    'weight': 1.26,
                    'is_active': True,
                    'featured': False,
                    'rating': 4.4,
                    'review_count': 89,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                
                # Electronics - Headphones
                {
                    'name': 'Sony WH-1000XM5',
                    'description': 'Industry-leading noise canceling wireless headphones with 30-hour battery',
                    'category_id': headphones_category['_id'],
                    'price': 349.99,
                    'original_price': 399.99,
                    'stock_quantity': 75,
                    'sku': 'SONY-WH1000XM5-BLK',
                    'brand': 'Sony',
                    'color': 'Black',
                    'weight': 0.25,
                    'is_active': True,
                    'featured': True,
                    'rating': 4.5,
                    'review_count': 312,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                {
                    'name': 'AirPods Pro (2nd Gen)',
                    'description': 'Active Noise Cancellation, Adaptive Transparency, and spatial audio',
                    'category_id': headphones_category['_id'],
                    'price': 229.99,
                    'original_price': 249.99,
                    'stock_quantity': 120,
                    'sku': 'AIRPODS-PRO-2ND-GEN',
                    'brand': 'Apple',
                    'color': 'White',
                    'weight': 0.05,
                    'is_active': True,
                    'featured': False,
                    'rating': 4.6,
                    'review_count': 445,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                
                # Clothing
                {
                    'name': 'Levi\'s 501 Original Jeans',
                    'description': 'Classic straight-leg jeans with original fit and timeless style',
                    'category_id': clothing_category['_id'],
                    'price': 79.99,
                    'original_price': 89.99,
                    'stock_quantity': 200,
                    'sku': 'LEVIS-501-34W-32L',
                    'brand': 'Levi\'s',
                    'color': 'Dark Blue',
                    'size': '34W x 32L',
                    'material': '100% Cotton',
                    'is_active': True,
                    'featured': False,
                    'rating': 4.3,
                    'review_count': 167,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                {
                    'name': 'Nike Air Max 90',
                    'description': 'Iconic running shoes with visible Max Air unit and classic design',
                    'category_id': clothing_category['_id'],
                    'price': 119.99,
                    'stock_quantity': 85,
                    'sku': 'NIKE-AM90-WHITE-10',
                    'brand': 'Nike',
                    'color': 'White',
                    'size': '10',
                    'material': 'Leather/Synthetic',
                    'is_active': True,
                    'featured': False,
                    'rating': 4.4,
                    'review_count': 234,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                
                # Home & Garden
                {
                    'name': 'Dyson V15 Detect',
                    'description': 'Cordless vacuum with laser dust detection and powerful suction',
                    'category_id': home_category['_id'],
                    'price': 649.99,
                    'original_price': 749.99,
                    'stock_quantity': 30,
                    'sku': 'DYSON-V15-DETECT',
                    'brand': 'Dyson',
                    'color': 'Yellow/Nickel',
                    'weight': 3.1,
                    'is_active': True,
                    'featured': True,
                    'rating': 4.7,
                    'review_count': 178,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                {
                    'name': 'Instant Pot Duo 7-in-1',
                    'description': 'Electric pressure cooker that replaces 7 kitchen appliances',
                    'category_id': home_category['_id'],
                    'price': 79.99,
                    'original_price': 99.99,
                    'stock_quantity': 45,
                    'sku': 'INSTANTPOT-DUO-6QT',
                    'brand': 'Instant Pot',
                    'color': 'Stainless Steel',
                    'size': '6 Quart',
                    'weight': 5.3,
                    'is_active': True,
                    'featured': False,
                    'rating': 4.5,
                    'review_count': 523,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                
                # Sports & Outdoors
                {
                    'name': 'Peloton Bike+',
                    'description': 'Interactive exercise bike with rotating HD touchscreen and live classes',
                    'category_id': sports_category['_id'],
                    'price': 2495.00,
                    'stock_quantity': 8,
                    'sku': 'PELOTON-BIKEPLUS',
                    'brand': 'Peloton',
                    'color': 'Black',
                    'weight': 59.0,
                    'is_active': True,
                    'featured': True,
                    'rating': 4.8,
                    'review_count': 89,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                {
                    'name': 'Yeti Rambler 30oz',
                    'description': 'Insulated stainless steel tumbler with MagSlider lid',
                    'category_id': sports_category['_id'],
                    'price': 39.99,
                    'stock_quantity': 150,
                    'sku': 'YETI-RAMBLER-30OZ',
                    'brand': 'Yeti',
                    'color': 'Navy',
                    'size': '30oz',
                    'material': 'Stainless Steel',
                    'is_active': True,
                    'featured': False,
                    'rating': 4.6,
                    'review_count': 278,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                
                # Books
                {
                    'name': 'The Psychology of Money',
                    'description': 'Timeless lessons on wealth, greed, and happiness by Morgan Housel',
                    'category_id': books_category['_id'],
                    'price': 16.99,
                    'original_price': 19.99,
                    'stock_quantity': 95,
                    'sku': 'BOOK-PSYCH-MONEY',
                    'brand': 'Harriman House',
                    'material': 'Paperback',
                    'is_active': True,
                    'featured': False,
                    'rating': 4.7,
                    'review_count': 1456,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                
                # Beauty & Health
                {
                    'name': 'Cetaphil Gentle Skin Cleanser',
                    'description': 'Fragrance-free cleanser for sensitive skin, dermatologist recommended',
                    'category_id': beauty_category['_id'],
                    'price': 12.99,
                    'stock_quantity': 200,
                    'sku': 'CETAPHIL-CLEANSER-16OZ',
                    'brand': 'Cetaphil',
                    'size': '16oz',
                    'is_active': True,
                    'featured': False,
                    'rating': 4.4,
                    'review_count': 2341,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                },
                
                # Toys & Games
                {
                    'name': 'LEGO Creator 3-in-1 Deep Sea Creatures',
                    'description': 'Build a shark, squid, or angler fish with this versatile LEGO set',
                    'category_id': toys_category['_id'],
                    'price': 79.99,
                    'stock_quantity': 40,
                    'sku': 'LEGO-31088-DEEPSEA',
                    'brand': 'LEGO',
                    'color': 'Multi',
                    'is_active': True,
                    'featured': False,
                    'rating': 4.8,
                    'review_count': 124,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            ]
            
            result = self.db.products.insert_many(products)
            logger.info(f"Inserted {len(products)} products successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert products: {e}")
            return False
    
    def insert_customers(self):
        """Insert sample customers."""
        customers = []
        
        # Generate 50 realistic customers
        for i in range(50):
            customers.append({
                'email': fake.email(),
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'phone': fake.phone_number(),
                'date_of_birth': datetime.combine(fake.date_of_birth(minimum_age=18, maximum_age=80), datetime.min.time()),
                'gender': random.choice(['M', 'F', 'Other']),
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        
        try:
            result = self.db.customers.insert_many(customers)
            logger.info(f"Inserted {len(customers)} customers successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert customers: {e}")
            return False
    
    def insert_customer_addresses(self):
        """Insert addresses for customers."""
        try:
            # Get all customer IDs
            customers = list(self.db.customers.find({}, {'_id': 1}))
            customer_ids = [customer['_id'] for customer in customers]
            
            addresses = []
            for customer_id in customer_ids:
                # Each customer gets 1-2 addresses
                num_addresses = random.randint(1, 2)
                
                for i in range(num_addresses):
                    addresses.append({
                        'customer_id': customer_id,
                        'address_type': 'shipping' if i == 0 else random.choice(['billing', 'shipping']),
                        'street_address': fake.street_address(),
                        'city': fake.city(),
                        'state': fake.state_abbr(),
                        'postal_code': fake.zipcode(),
                        'country': 'US',
                        'is_default': i == 0,  # First address is default
                        'created_at': datetime.now()
                    })
            
            result = self.db.customer_addresses.insert_many(addresses)
            logger.info(f"Inserted {len(addresses)} customer addresses successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert customer addresses: {e}")
            return False
    
    def insert_orders(self):
        """Insert sample orders with order items."""
        try:
            # Get customer and product data
            customers = list(self.db.customers.find({}, {'_id': 1}))
            customer_ids = [customer['_id'] for customer in customers]
            
            products = list(self.db.products.find({}, {'_id': 1, 'price': 1}))
            product_data = [(product['_id'], product['price']) for product in products]
            
            # Get default addresses for customers
            default_addresses = {}
            addresses = self.db.customer_addresses.find({'is_default': True})
            for address in addresses:
                default_addresses[address['customer_id']] = address['_id']
            
            # Order statuses and payment methods
            order_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
            payment_methods = ['credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay']
            payment_statuses = ['pending', 'paid', 'failed', 'refunded']
            
            orders = []
            order_items_to_insert = []
            
            # Generate 100 orders over the last 6 months
            for i in range(100):
                customer_id = random.choice(customer_ids)
                order_date = fake.date_time_between(start_date='-6M', end_date='now')
                
                # Generate order number
                order_number = f"ORD-{order_date.strftime('%Y%m%d')}-{i+1:04d}"
                
                # Select random products for this order (1-5 items)
                num_items = random.randint(1, 5)
                selected_products = random.sample(product_data, min(num_items, len(product_data)))
                
                subtotal = 0
                order_item_data = []
                
                for product_id, price in selected_products:
                    quantity = random.randint(1, 3)
                    total_price = float(price) * quantity
                    subtotal += total_price
                    
                    order_item_data.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'unit_price': float(price),
                        'total_price': total_price
                    })
                
                # Calculate totals
                tax_rate = 0.08  # 8% tax
                tax_amount = subtotal * tax_rate
                shipping_amount = 0 if subtotal > 50 else 9.99  # Free shipping over $50
                discount_amount = random.choice([0, 0, 0, 5, 10, 15])  # Occasional discounts
                total_amount = subtotal + tax_amount + shipping_amount - discount_amount
                
                status = random.choice(order_statuses)
                payment_method = random.choice(payment_methods)
                payment_status = 'paid' if status in ['processing', 'shipped', 'delivered'] else random.choice(payment_statuses)
                
                # Set shipping and delivery dates based on status
                shipped_at = None
                delivered_at = None
                if status == 'shipped':
                    shipped_at = order_date + timedelta(days=random.randint(1, 3))
                elif status == 'delivered':
                    shipped_at = order_date + timedelta(days=random.randint(1, 3))
                    delivered_at = shipped_at + timedelta(days=random.randint(1, 7))
                
                order = {
                    'order_number': order_number,
                    'customer_id': customer_id,
                    'status': status,
                    'total_amount': round(total_amount, 2),
                    'subtotal': round(subtotal, 2),
                    'tax_amount': round(tax_amount, 2),
                    'shipping_amount': shipping_amount,
                    'discount_amount': discount_amount,
                    'payment_method': payment_method,
                    'payment_status': payment_status,
                    'shipping_address_id': default_addresses.get(customer_id),
                    'billing_address_id': default_addresses.get(customer_id),
                    'created_at': order_date,
                    'updated_at': order_date,
                    'shipped_at': shipped_at,
                    'delivered_at': delivered_at,
                    'order_items': order_item_data
                }
                
                orders.append(order)
            
            # Insert orders
            for order in orders:
                order_items = order.pop('order_items')  # Remove order_items from order doc
                result = self.db.orders.insert_one(order)
                order_id = result.inserted_id
                
                # Prepare order items with the order_id
                for item in order_items:
                    item['order_id'] = order_id
                    item['created_at'] = datetime.now()
                    order_items_to_insert.append(item)
            
            # Insert all order items
            if order_items_to_insert:
                self.db.order_items.insert_many(order_items_to_insert)
            
            logger.info(f"Inserted {len(orders)} orders and {len(order_items_to_insert)} order items successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert orders: {e}")
            return False
    
    def insert_product_reviews(self):
        """Insert product reviews from customers."""
        try:
            # Get customers who have made purchases using aggregation
            pipeline = [
                {
                    '$lookup': {
                        'from': 'order_items',
                        'localField': '_id',
                        'foreignField': 'order_id',
                        'as': 'items'
                    }
                },
                {
                    '$match': {
                        'status': 'delivered',
                        'items': {'$exists': True, '$ne': []}
                    }
                },
                {
                    '$unwind': '$items'
                },
                {
                    '$project': {
                        'customer_id': 1,
                        'product_id': '$items.product_id'
                    }
                }
            ]
            
            purchase_data = list(self.db.orders.aggregate(pipeline))
            
            reviews = []
            review_templates = [
                {"rating": 5, "title": "Excellent product!", "text": "Love this product! Exactly as described and great quality."},
                {"rating": 4, "title": "Good value", "text": "Good product for the price. Would recommend."},
                {"rating": 3, "title": "Okay", "text": "Average product. Does what it's supposed to do."},
                {"rating": 2, "title": "Not impressed", "text": "Product quality could be better for the price."},
                {"rating": 1, "title": "Disappointed", "text": "Product did not meet expectations. Would not buy again."},
                {"rating": 5, "title": "Amazing!", "text": "Fantastic product! Exceeded my expectations in every way."},
                {"rating": 4, "title": "Solid choice", "text": "Well-made product with good features. Happy with purchase."},
            ]
            
            # Generate reviews for about 30% of purchases
            sample_size = len(purchase_data) // 3 if purchase_data else 0
            if sample_size > 0:
                for purchase in random.sample(purchase_data, sample_size):
                    template = random.choice(review_templates)
                    review_date = fake.date_time_between(start_date='-3M', end_date='now')
                    
                    reviews.append({
                        'product_id': purchase['product_id'],
                        'customer_id': purchase['customer_id'],
                        'rating': template['rating'],
                        'title': template['title'],
                        'review_text': template['text'],
                        'is_verified_purchase': True,
                        'helpful_count': random.randint(0, 25),
                        'created_at': review_date
                    })
            
            if reviews:
                result = self.db.product_reviews.insert_many(reviews)
                logger.info(f"Inserted {len(reviews)} product reviews successfully")
            else:
                logger.info("No reviews to insert")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert product reviews: {e}")
            return False
    
    def insert_coupons(self):
        """Insert sample coupons and discount codes."""
        coupons = [
            {
                'code': 'SAVE10',
                'description': '10% off your entire order',
                'discount_type': 'percentage',
                'discount_value': 10.00,
                'minimum_order_amount': 50.00,
                'max_uses': 1000,
                'used_count': 0,
                'valid_from': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=30),
                'is_active': True,
                'created_at': datetime.now()
            },
            {
                'code': 'FREESHIP',
                'description': 'Free shipping on orders over $25',
                'discount_type': 'fixed',
                'discount_value': 9.99,
                'minimum_order_amount': 25.00,
                'max_uses': 500,
                'used_count': 0,
                'valid_from': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=60),
                'is_active': True,
                'created_at': datetime.now()
            },
            {
                'code': 'NEWCUSTOMER20',
                'description': '$20 off for new customers',
                'discount_type': 'fixed',
                'discount_value': 20.00,
                'minimum_order_amount': 100.00,
                'max_uses': 100,
                'used_count': 0,
                'valid_from': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=90),
                'is_active': True,
                'created_at': datetime.now()
            },
            {
                'code': 'ELECTRONICS15',
                'description': '15% off electronics',
                'discount_type': 'percentage',
                'discount_value': 15.00,
                'minimum_order_amount': 200.00,
                'max_uses': 200,
                'used_count': 0,
                'valid_from': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=45),
                'is_active': True,
                'created_at': datetime.now()
            },
            {
                'code': 'CLEARANCE25',
                'description': '25% off clearance items',
                'discount_type': 'percentage',
                'discount_value': 25.00,
                'minimum_order_amount': 0.00,
                'max_uses': 50,
                'used_count': 0,
                'valid_from': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=14),
                'is_active': True,
                'created_at': datetime.now()
            }
        ]
        
        try:
            result = self.db.coupons.insert_many(coupons)
            logger.info(f"Inserted {len(coupons)} coupons successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert coupons: {e}")
            return False
    
    def insert_product_images(self):
        """Insert sample product image URLs."""
        try:
            # Get all products with their names
            products = list(self.db.products.find({}, {'_id': 1, 'name': 1}))
            
            if not products:
                logger.warning("No products found to add images to")
                return False
            
            images = []
            for product in products:
                # Each product gets 2-4 images
                num_images = random.randint(2, 4)
                
                for i in range(num_images):
                    images.append({
                        'product_id': product['_id'],
                        'image_url': f"https://example.com/images/product_{product['_id']}_{i+1}.jpg",
                        'alt_text': f"{product['name']} - Image {i+1}",
                        'is_primary': i == 0,  # First image is primary
                        'sort_order': i + 1,
                        'created_at': datetime.now()
                    })
            
            result = self.db.product_images.insert_many(images)
            logger.info(f"Inserted {len(images)} product images successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert product images: {e}")
            return False
    
    def setup_database(self):
        """Complete database setup with all mock data."""
        logger.info("🚀 Starting E-commerce Database Setup...")
        
        if not self.connect():
            return False
        
        try:
            # Create all collections and indexes
            if not self.create_collections():
                return False
            
            # Insert all mock data
            if not self.insert_categories():
                return False
                
            if not self.insert_products():
                return False
                
            if not self.insert_product_images():
                return False
                
            if not self.insert_customers():
                return False
                
            if not self.insert_customer_addresses():
                return False
                
            if not self.insert_orders():
                return False
                
            if not self.insert_product_reviews():
                return False
                
            if not self.insert_coupons():
                return False
            
            # Print summary
            self.print_database_summary()
            
            logger.info("✅ E-commerce database setup completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False
    
    def print_database_summary(self):
        """Print a summary of the database contents."""
        collections = [
            'categories', 'products', 'product_images', 'customers', 
            'customer_addresses', 'orders', 'order_items', 'product_reviews', 'coupons'
        ]
        
        logger.info("\n📊 Database Summary:")
        logger.info("=" * 50)
        
        for collection_name in collections:
            collection = self.db[collection_name]
            count = collection.count_documents({})
            logger.info(f"{collection_name.title().replace('_', ' '):<20}: {count:>6} records")
        
        # Additional statistics
        # Total revenue from non-cancelled orders
        revenue_pipeline = [
            {"$match": {"status": {"$ne": "cancelled"}}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        revenue_result = list(self.db.orders.aggregate(revenue_pipeline))
        total_revenue = revenue_result[0]['total'] if revenue_result else 0
        
        # Average product rating
        rating_pipeline = [
            {"$match": {"review_count": {"$gt": 0}}},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
        ]
        rating_result = list(self.db.products.aggregate(rating_pipeline))
        avg_rating = rating_result[0]['avg_rating'] if rating_result else 0
        
        # In-stock products count
        in_stock_products = self.db.products.count_documents({"stock_quantity": {"$gt": 0}})
        
        logger.info("=" * 50)
        logger.info(f"Total Revenue      : ${total_revenue:,.2f}")
        logger.info(f"Average Rating     : {avg_rating:.2f}/5.0")
        logger.info(f"In-Stock Products  : {in_stock_products}")
        logger.info("=" * 50)

def main():
    """Main function to run the database setup."""
    db_setup = EcommerceDBSetup()
    
    # Check if we can connect to database
    if not db_setup.connect():
        print("❌ Cannot connect to MongoDB. Please check your connection settings.")
        return
    
    try:
        # Check if database has any collections
        collection_names = db_setup.db.list_collection_names()
        
        if collection_names:
            print(f"⚠️  Database '{db_setup.db_name}' already has collections: {', '.join(collection_names)}")
            response = input("Do you want to recreate it? (y/N): ").lower().strip()
            if response == 'y':
                # Drop all collections
                for collection_name in collection_names:
                    db_setup.db[collection_name].drop()
                print("🗑️  Existing collections deleted.")
            else:
                print("❌ Database setup cancelled.")
                return
        
        # Setup database
        success = db_setup.setup_database()
        
        if success:
            print(f"\n🎉 E-commerce MongoDB database setup completed successfully!")
            print(f"Database: {db_setup.db_name}")
            print("\n📋 You can now use this database for:")
            print("   • Product catalog management")
            print("   • Order processing system")
            print("   • Customer relationship management")
            print("   • Analytics and reporting")
            print("   • E-commerce assistant training")
        else:
            print("❌ Database setup failed. Check the logs for details.")
            
    except Exception as e:
        print(f"❌ Error during database setup: {e}")
        logger.error(f"Database setup error: {e}")
    
    finally:
        db_setup.close()

if __name__ == "__main__":
    main()