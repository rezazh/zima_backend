from django.core.management.base import BaseCommand
from users.models import CustomUser
from products.models import Category, Product


class Command(BaseCommand):
    help = 'Creates initial data for the project'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating initial data...')

        # ایجاد دسته‌بندی‌ها
        cat1 = Category.objects.create(name='لباس مردانه', slug='mens-clothing')
        cat2 = Category.objects.create(name='لباس زنانه', slug='womens-clothing')

        # ایجاد محصولات
        Product.objects.create(
            name='تیشرت مردانه',
            slug='mens-tshirt',
            category=cat1,
            brand='برند نمونه',
            gender='men',
            description='توضیحات محصول',
            price=150000,
            stock=10
        )

        Product.objects.create(
            name='بلوز زنانه',
            slug='womens-blouse',
            category=cat2,
            brand='برند نمونه',
            gender='women',
            description='توضیحات محصول',
            price=180000,
            stock=8
        )

        self.stdout.write(self.style.SUCCESS('Initial data created successfully!'))