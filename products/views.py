from re import search

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import perform_import
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django.shortcuts import get_object_or_404
from .models import Product, Review, Category
from .serializers import ProductSerializer, ReviewSerializer, CategorySerializer, ProductDetailSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from io import BytesIO
import os



class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user and request.user.is_staff



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": "Failed to create category"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": "Failed to update category"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductViewSet(viewsets.ModelViewSet):
    print("sdsd")
    permission_classes = [IsAdminOrReadOnly]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['category', 'price', 'stock']
    ordering_fields = ['price', 'created_at']
    search_fields = ['name', 'description']
    pagination_class = ProductPagination

    def get_queryset(self):
        queryset = Product.objects.all()
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

    def perform_create(self, serializer):
        if 'image' in self.request.FILES:
            image = self.process_image(self.request.FILES['image'])
            serializer.save(image=image)
        else:
            serializer.save()

    def perform_update(self, serializer):
        if 'image' in self.request.FILES:
            image = self.process_image(self.request.FILES['image'])
            serializer.save(image=image)
        else:
            serializer.save()

    def process_image(self, image):
        """پردازش و بهینه‌سازی تصویر"""
        if isinstance(image, InMemoryUploadedFile):
            img = Image.open(image)

            # تبدیل تصاویر RGBA به RGB
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background

            # محدود کردن اندازه تصویر
            max_size = (1920, 1920)
            img.thumbnail(max_size, Image.LANCZOS)

            # ذخیره با کیفیت مناسب
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)

            return InMemoryUploadedFile(
                output,
                'ImageField',
                f"{os.path.splitext(image.name)[0]}.jpg",
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
        return image
@api_view(['GET'])
def featured_products(request):
    try:
        paginator = ProductPagination()
        featured = Product.objects.filter(is_featured=True)
        result_page = paginator.paginate_queryset(featured, request)
        serializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        return Response(
            {"error": "Failed to fetch featured products"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def similar_products(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        similar = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:5]
        serializer = ProductSerializer(similar, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {"error": "Failed to fetch similar products"},
            status=status.HTTP_400_BAD_REQUEST
        )


class ReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        try:
            product = get_object_or_404(Product, id=product_id)

            if Review.objects.filter(user=request.user, product=product).exists():
                raise ValidationError("You have already reviewed this product")

            serializer = ReviewSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user, product=product)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Failed to create review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, product_id):
        try:
            product = get_object_or_404(Product, id=product_id)
            reviews = Review.objects.filter(product_id=product_id)
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": "Failed to fetch reviews"},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([IsAdminUser]) 
def add_product(request):
    """
    API برای افزودن محصول جدید توسط ادمین
    """
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Product added successfully!", "product": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_Category(request):
    """
    API برای افزودن دسته بندی جدید توسط ادمین
    """
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Category added successfully!", "Category": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def latest_products(request):
    try:
        products = Product.objects.all().order_by('-created_at')[:10]
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in latest_products: {str(e)}")
        return Response(
            {"error": f"Failed to fetch latest products: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def men_products(request):
    print("Start fetching men's products...")
    print(f"Request parameters: {request.GET}")

    try:
        print("Fetching men's products...")

        categories = Category.objects.filter(name__icontains='مردانه')
        print(f"Found categories: {categories}")

        if not categories.exists():
            print("No men categories found")
            # اگر دسته‌بندی مردانه پیدا نشد، همه محصولات را برگردان
            queryset = Product.objects.all()
        else:
            queryset = Product.objects.filter(category__in=categories)

        print(f"Initial product count: {queryset.count()}")

        # دریافت پارامترهای فیلتر
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        size = request.GET.get('size')
        color = request.GET.get('color')
        sort = request.GET.get('sort', '-created_at')
        page = int(request.GET.get('page', 1))
        brand = request.GET.get('brand')
        search = request.GET.get('search')

        # شروع با محصولات دسته مردانه
        queryset = Product.objects.filter(category__in=categories)

        # اعمال فیلترها
        if price_min and price_min.strip():
            queryset = queryset.filter(price__gte=float(price_min))
        if price_max and price_max.strip():
            queryset = queryset.filter(price__lte=float(price_max))
        if size and size.strip():
            queryset = queryset.filter(sizes__contains=size)
        if color and color.strip():
            queryset = queryset.filter(colors__contains=color)
        if brand and brand.strip():
            queryset = queryset.filter(brand__icontains=brand)
        if search and search.strip():
            queryset = queryset.filter(name__icontains=search)

        # مرتب‌سازی
        if sort:
            if sort == 'newest':
                queryset = queryset.order_by('-created_at')
            elif sort == 'price_low':
                queryset = queryset.order_by('price')
            elif sort == 'price_high':
                queryset = queryset.order_by('-price')
            elif sort == 'popular':
                queryset = queryset.order_by('-is_featured', '-created_at')

        # صفحه‌بندی
        paginator = PageNumberPagination()
        paginator.page_size = 12
        result_page = paginator.paginate_queryset(queryset, request)

        # اضافه کردن request به context
        serializer = ProductSerializer(result_page, many=True, context={'request': request})

        # لاگ کردن داده نمونه
        if serializer.data:
            print(f"Sample product data: {serializer.data[0]}")
        else:
            print("No products found after filtering")

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    except Exception as e:
        import traceback
        print(f"Error in men_products: {str(e)}")
        traceback.print_exc()
        return Response(
            {"error": f"خطا در دریافت محصولات: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_filter_options(request):
    products = Product.objects.all()

    # تبدیل رشته‌های سایز و رنگ به لیست
    sizes = set()
    colors = set()
    for product in products:
        if product.sizes:
            sizes.update(product.sizes.split(','))
        if product.colors:
            colors.update(product.colors.split(','))

    # دریافت برندهای یکتا
    brands = set(products.exclude(brand__isnull=True)
                 .exclude(brand='')
                 .values_list('brand', flat=True))

    return Response({
        'sizes': sorted(list(sizes)),
        'colors': sorted(list(colors)),
        'brands': sorted(list(brands))
    })


@api_view(['GET'])
def product_detail(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        serializer = ProductDetailSerializer(product)

        # Get similar products
        similar_products = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:10]
        # Get recommended products (based on stock)
        recommended_products = Product.objects.order_by('-stock')[:10]
        return Response({
            'product': serializer.data,
            'similar_products': ProductSerializer(similar_products, many=True).data,
            'recommended_products': ProductSerializer(recommended_products, many=True).data
        })
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def women_underwear_products(request):
    try:
        # اول تلاش برای پیدا کردن دسته‌بندی 'لباس زیر زنانه'
        category = Category.objects.filter(name__icontains='زیر زنانه').first()

        if not category:
            return Response(
                {"error": "Category 'لباس زیر زنانه' not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        products = Product.objects.filter(category=category).order_by('-created_at')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in women_underwear_products: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def men_underwear_products(request):
    try:
        # اول تلاش برای پیدا کردن دسته‌بندی 'لباس زیر مردانه'
        category = Category.objects.filter(name__icontains='زیر مردانه').first()

        if not category:
            return Response(
                {"error": "Category 'لباس زیر مردانه' not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        products = Product.objects.filter(category=category).order_by('-created_at')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in men_underwear_products: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )