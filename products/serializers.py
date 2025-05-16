# serializers.py
from rest_framework import serializers
# serializers.pyfrom rest_framework import serializers
from .models import Product, Review, Category, ProductImage

# ==========================================
#  Supporting Serializers
# ==========================================

class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews."""
    # اضافه کردن نام کاربر (اگر مدل User شما فیلد مناسبی دارد)
    # user_name = serializers.CharField(source='user.get_full_name', read_only=True) # مثال    class Meta:
    model = Review
    fields = [
        'id', 'user', #'user_name',
        'product', 'rating', 'comment', 'created_at'
    ]
    read_only_fields = ['user', 'created_at', 'product'] # معمولا product هم read_only است


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories."""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'created_at']
        # Slug معمولا خودکار ساخته می‌شود یا اختیاری است
        extra_kwargs = {
            'slug': {'required': False, 'read_only': True} # اگر خودکار ساخته می‌شود
        }


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'is_primary', 'image'] # image اصلی را هم نگه می‌داریم (برای مدیریت شاید)
        read_only_fields = ['id', 'image_url']

    def get_image_url(self, obj):
        """Builds the absolute URL for the gallery image."""
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url') and request:
            # استفاده از obj.image.url برای دریافت مسیر نسبی
            # و سپس ساخت URL کامل
            return request.build_absolute_uri(obj.image.url)
        # اگر تصویری نیست یا درخواستی وجود ندارد، null برگردان
        return None

# ==========================================
#  Main Product Serializers
# ==========================================

class BaseProductSerializer(serializers.ModelSerializer):
    """
    Base serializer containing common methods for handling
    colors, sizes, stock, discount price, and image URLs.
    """
    # --- Serializer Method Fields for calculated/formatted data ---
    colors = serializers.SerializerMethodField(method_name='get_colors_list')
    sizes = serializers.SerializerMethodField(method_name='get_sizes_list')
    discount_price = serializers.SerializerMethodField(read_only=True)
    in_stock = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(method_name='get_main_image_url') # برای URL تصویر اصلی

    # --- Helper Methods (used by SerializerMethodFields) ---
    def get_colors_list(self, obj):
        """Converts comma-separated string 'colors' field to a list of strings."""
        if obj.colors and isinstance(obj.colors, str):
            # حذف فضای خالی و موارد خالی بعد از split
            return [color.strip() for color in obj.colors.split(',') if color.strip()]
            return [] # Return empty list if no colors or not a string

    def get_sizes_list(self, obj):
        """Converts comma-separated string 'sizes' field to a list of strings."""
        if obj.sizes and isinstance(obj.sizes, str):
            return [size.strip() for size in obj.sizes.split(',') if size.strip()]
        return []

    def get_discount_price(self, obj):
        """        Calculates the final price after applying the discount.
        Returns the original price if no valid discount exists.
        Ensures the output is always a float.
        """
        try:
            # اطمینان از اینکه قیمت‌ها عددی هستند قبل از محاسبه
            original_price = float(obj.price) if obj.price is not None else 0.0
            # فرض: obj.discount مقدار تخفیف است (نه درصد)
            discount_amount = float(obj.discount) if obj.discount is not None else 0.0

            # اعمال تخفیف فقط اگر معتبر باشد
            if 0 < discount_amount < original_price:
                return original_price - discount_amount
            # در غیر این صورت، قیمت اصلی را برگردان
            return original_price
        except (ValueError, TypeError):
            # اگر تبدیل نوع یا محاسبه با خطا مواجه شد، قیمت اصلی را برگردان
            return float(obj.price) if obj.price is not None else 0.0

    def get_in_stock(self, obj):
        """Checks if the product stock is greater than 0."""
        return obj.stock is not None and obj.stock > 0

    def get_main_image_url(self, obj):
        """Builds the absolute URL for the main product image."""
        request = self.context.get('request')
        # بررسی وجود تصویر و داشتن attribute 'url' (برای FileField/ImageField)
        if obj.image and hasattr(obj.image, 'url') and request:
            return request.build_absolute_uri(obj.image.url)
        return None # یا URL تصویر پیش‌فرض: return request.build_absolute_uri('/static/placeholder.png')

    # --- Representation Override for final type checks ---
    def to_representation(self, instance):
        """Ensures price fields are floats in the final output."""
        representation = super().to_representation(instance)

        # اطمینان از اینکه قیمت اصلی به float تبدیل شده
        if representation.get('price') is not None:
            try:
                representation['price'] = float(representation['price'])
            except (ValueError, TypeError):
                 # اگر قیمت اصلی نامعتبر است، آن را 0 یا None قرار بده
                representation['price'] = 0.0
        else:
             representation['price'] = 0.0 # یا None

        # discount_price قبلاً در get_discount_price به float تبدیل شده،
        # اما برای اطمینان اگر None بود، برابر قیمت اصلی قرار می‌دهیم
        if representation.get('discount_price') is None:             representation['discount_price'] = representation['price']

        # اگر فیلد 'discount' (مقدار تخفیف) را هم ارسال می‌کنید:
        if 'discount' in representation and representation.get('discount') is not None:
             try:
                 representation['discount'] = float(representation['discount'])
             except (ValueError, TypeError):
                 representation['discount'] = 0.0
        elif 'discount' in representation:
             representation['discount'] = 0.0 # یا None

        return representation


class ProductSerializer(BaseProductSerializer):
     """
     Serializer for the Product LIST view.
     Sends only the fields needed by ProductCard.js.
     Inherits common methods from BaseProductSerializer.
     """
     # فیلد مستقیم از مدل (فقط خواندنی برای لیست)
     category_name = serializers.CharField(source='category.name', read_only=True) # تعریف فیلد

     class Meta:
         model = Product
         # لیست دقیق فیلدهایی که ProductCard.js نیاز دارد:
         fields = [
         'id', # Number (برای لینک و key)
         'name', # String
         'brand', # String (اختیاری)
         'image_url', # String (URL کامل تصویر اصلی)
         'price', # Number (قیمت اصلی)
         'discount_price', # Number (قیمت نهایی با تخفیف)
         'colors', # Array of Strings (لیست نام رنگ‌ها)
         'sizes', # Array of Strings (لیست نام سایزها)
         'in_stock', # Boolean
         'category_name', # <<<--- اضافه شد / از کامنت خارج شد
         ]
         # read_only_fields = fields # این خط اختیاری است، چون همه فیلدها در fields هستند

class ProductDetailSerializer(BaseProductSerializer):
    """
    Serializer for the Product DETAIL view.
    Includes more fields like description, gallery, reviews, etc.
    Inherits common methods from BaseProductSerializer.
    """    # فیلدهای مرتبط با استفاده از سریالایزرهای دیگر
    # برای گالری، از source استفاده می‌کنیم که به related_name یا نام فیلد در مدل اشاره دارد
    # فرض می‌کنیم related_name در ProductImage ForeignKey به Product، برابر 'gallery_images' است
    gallery = ProductImageSerializer(many=True, read_only=True, source='gallery_images') # <<< نام source را با مدل خود تطبیق دهید
    reviews = ReviewSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        # لیست فیلدها برای صفحه جزئیات محصول
        fields = [
            'id',
            'category', # ID دسته بندی اصلی
            'category_name',
            'name',
            'description',      # توضیحات کامل محصول
            'price',            # قیمت اصلی (Number)
            'discount',         # مقدار تخفیف (Number - اختیاری، اگر می‌خواهید نمایش دهید)
            'discount_price',   # قیمت نهایی (Number)
            'stock',            # تعداد موجودی (Number)
            'in_stock',         # وضعیت موجودی (Boolean)
            'brand',
            'image_url',        # URL تصویر اصلی
            'gallery',          # لیست تصاویر گالری (از ProductImageSerializer)
            'attributes',       # اگر فیلد JSON یا مشابه دارید
            'is_featured',            'created_at',
            'updated_at',
            'colors',           # لیست رنگ‌ها (Array of Strings)
            'sizes',            # لیست سایزها (Array of Strings)
            'reviews'           # لیست نظرات
        ]        # read_only_fields = [...] # در صورت نیاز فیلدهای فقط خواندنی را مشخص کنید

    # نیازی به بازنویسی to_representation نیست چون از BaseProductSerializer ارث‌بری می‌شود
    # و متدهای get_... هم ارث‌بری می‌شوند.