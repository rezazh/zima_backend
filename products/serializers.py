from rest_framework import serializers
from .models import Product, Review, Category, ProductImage

# ReviewSerializer و CategorySerializer بدون تغییر باقی می‌مانند
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'created_at']
        extra_kwargs = {            'slug': {'required': False}
        }

# ProductSerializer اصلاح شده
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    # --- تغییر 1: نام SerializerMethodField ها را به colors و sizes تغییر می‌دهیم ---
    colors = serializers.SerializerMethodField(method_name='get_colors_list')
    sizes = serializers.SerializerMethodField(method_name='get_sizes_list')
    discount_price = serializers.SerializerMethodField(read_only=True)
    in_stock = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        # --- تغییر 2: فقط نام‌های جدید (colors, sizes) را در فیلدها قرار می‌دهیم ---
        fields = [
            'id', 'name', 'price', 'discount_price',
            'colors',  # حالا این فیلد حاوی لیست رنگ‌ها خواهد بود
            'sizes',   # حالا این فیلد حاوی لیست سایزها خواهد بود
            'image', 'in_stock', 'category',            'category_name', 'created_at', 'is_featured', 'stock', 'brand'
        ]
        # فیلدهای اضافی که ممکن است بخواهید اضافه کنید (اختیاری):
        # 'description', 'discount', 'gallery', 'attributes', 'updated_at'

    # --- تغییر 3: نام توابع get را مطابق method_name بالا نگه می‌داریم ---
    def get_colors_list(self, obj):
        if obj.colors:
            # اضافه کردن strip() برای حذف فضای خالی احتمالی دور کاما
            return [color.strip() for color in obj.colors.split(',') if color.strip()]
        return []

    def get_sizes_list(self, obj):
        if obj.sizes:
            # اضافه کردن strip() برای حذف فضای خالی احتمالی دور کاما
            return [size.strip() for size in obj.sizes.split(',') if size.strip()]
        return []

    def get_discount_price(self, obj):
        # محاسبه قیمت با تخفیف - مطمئن شوید فیلد discount در مدل Product وجود دارد
        if obj.discount is not None and obj.discount > 0:
             # تبدیل به float برای محاسبه صحیح (اگر DecimalField هستند مشکلی نیست)
            return float(obj.price) - float(obj.discount)        # اگر تخفیف وجود ندارد یا صفر است، همان قیمت اصلی را برگردان
        # یا اگر می‌خواهید در این حالت null برگردد: return None
        return float(obj.price)


    def get_in_stock(self, obj):
        return obj.stock > 0

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        # اطمینان از کامل بودن URL تصویر
        if request and representation.get('image') and not representation['image'].startswith(('http', '/media')):
             # اگر از /media/ شروع نشود، کاملش کن
            if not representation['image'].startswith('/'):
                 representation['image'] = '/' + representation['image']
            representation['image'] = request.build_absolute_uri(representation['image'])
        elif not representation.get('image'):
             # اگر تصویری وجود ندارد، یک مقدار پیش‌فرض یا خالی بگذارید
            representation['image'] = None # یا '/static/images/placeholder.png'

        # اطمینان از اینکه قیمت‌ها به صورت عدد ارسال می‌شوند (نه رشته)
        if representation.get('price'):
             representation['price'] = float(representation['price'])
        if representation.get('discount_price'):
             representation['discount_price'] = float(representation['discount_price'])

        return representation


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

    # اضافه کردن to_representation برای کامل کردن URL تصویر گالری
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and representation.get('image') and not representation['image'].startswith(('http', '/media')):
            if not representation['image'].startswith('/'):
                 representation['image'] = '/' + representation['image']
            representation['image'] = request.build_absolute_uri(representation['image'])
        elif not representation.get('image'):
            representation['image'] = None
        return representation


# ProductDetailSerializer اصلاح شده (برای هماهنگی)
class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True) # استفاده از سریالایزر تصویر
    # --- تغییر 1: نام SerializerMethodField ها را به colors و sizes تغییر می‌دهیم ---
    colors = serializers.SerializerMethodField(method_name='get_colors_list')
    sizes = serializers.SerializerMethodField(method_name='get_sizes_list')
    discount_price = serializers.SerializerMethodField(read_only=True)
    in_stock = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    # اضافه کردن سریالایزر برای نظرات
    reviews = ReviewSerializer(many=True, read_only=True)


    class Meta:
        model = Product
        # --- تغییر 2: فیلدها را به صورت صریح لیست می‌کنیم تا مطمئن شویم فیلدهای رشته‌ای اصلی colors/sizes نمی‌آیند ---
        fields = [
            'id', 'category', 'category_name', 'name', 'description',
            'price', 'discount', 'discount_price', # discount هم اضافه شد اگر لازم است نمایش داده شود
            'stock', 'in_stock', 'brand', 'image',
            'gallery', # فیلد گالری مدل
            'images', # فیلد تصاویر مرتبط از ProductImageSerializer
            'attributes', 'is_featured',
            'created_at', 'updated_at',
            'colors',  # لیست رنگ‌ها
            'sizes',   # لیست سایزها
            'reviews' # اضافه کردن نظرات
        ]    # --- تغییر 3: توابع get را مانند ProductSerializer نگه می‌داریم ---
    def get_colors_list(self, obj):
        if obj.colors:
            return [color.strip() for color in obj.colors.split(',') if color.strip()]
        return []

    def get_sizes_list(self, obj):
        if obj.sizes:
            return [size.strip() for size in obj.sizes.split(',') if size.strip()]
        return []
    def get_discount_price(self, obj):
        if obj.discount is not None and obj.discount > 0:
            return float(obj.price) - float(obj.discount)
        return float(obj.price)


    def get_in_stock(self, obj):
        return obj.stock > 0

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        # کامل کردن URL تصویر اصلی
        if request and representation.get('image') and not representation['image'].startswith(('http', '/media')):
            if not representation['image'].startswith('/'):
                 representation['image'] = '/' + representation['image']
            representation['image'] = request.build_absolute_uri(representation['image'])
        elif not representation.get('image'):
             representation['image'] = None

         # اطمینان از اینکه قیمت‌ها به صورت عدد ارسال می‌شوند
        if representation.get('price'):
             representation['price'] = float(representation['price'])
        if representation.get('discount_price'):
             representation['discount_price'] = float(representation['discount_price'])
        if representation.get('discount'): # اگر فیلد discount را هم نمایش می‌دهید
             representation['discount'] = float(representation['discount'])


        # پردازش گالری (اگر gallery یک JSON از URL هاست)
        # این بخش بستگی به ساختار JSON شما در فیلد gallery دارد
        # مثال: اگر gallery لیستی از رشته‌های مسیر تصویر است:
        if isinstance(representation.get('gallery'), list):
            full_urls = []
            if request:
                for img_path in representation['gallery']:
                    if isinstance(img_path, str) and not img_path.startswith(('http', '/media')):
                         if not img_path.startswith('/'):
                             img_path = '/' + img_path
                         full_urls.append(request.build_absolute_uri(img_path))
                    else:
                        full_urls.append(img_path) # یا مدیریت موارد دیگر
                representation['gallery'] = full_urls
        # اگر ساختار دیگری دارد، این بخش را متناسب با آن تنظیم کنید        return representation