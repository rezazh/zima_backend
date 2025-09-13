# import os
#
# EXCLUDED_FILENAMES = {
#     '.gitignore', '.DS_Store','all_code'
# }
# EXCLUDED_EXTENSIONS = {
#     '.pyc', '.log', '.sqlite3',
# }
# EXCLUDED_DIRS = {
#     '__pycache__', '.git', '.venv', 'env', 'venv', 'migrations', 'static', 'media',
# }
#
# output_file = 'project_dump.txt'
#
# with open(output_file, 'w', encoding='utf-8') as out:
#     for root, dirs, files in os.walk('.'):
#         dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]
#
#         for file in files:
#             filepath = os.path.join(root, file)
#             filename = os.path.basename(filepath)
#
#             if filename in EXCLUDED_FILENAMES:
#                 continue
#             if os.path.splitext(filename)[1] in EXCLUDED_EXTENSIONS:
#                 continue
#             if filename.startswith('.'):
#                 continue
#
#             try:
#                 with open(filepath, 'r', encoding='utf-8') as f:
#                     content = f.read()
#             except Exception as e:
#                 print(f"⚠️ Skipped: {filepath} - {e}")
#                 continue
#
#             out.write(f"\n\n====== FILE: {filepath} ======\n\n")
#             out.write(content)







#v2
import os

# مسیرهایی که می‌خواهی در فایل نهایی باشند
INCLUDED_PATHS = [
    # 'users',
    # 'cart',
    # 'chat',
    # 'middleware',
    # 'orders',
    # 'pages',
    'products/models.py',
    'products/views.py',
    'products/urls.py',
    'products/templatetags/my_custom_filters.py',
    'static/css/pages/home.css',
    'static/css/pages/product_detail.css',
    'static/css/pages/quick-view.css',
    'static/css/main.css',
    # 'static/css/products.css',
    'static/js/main.js',
    'static/js/zima_theme_v2.js',
    'templates/base/base.html',
    'templates/pages/home.html',
    'templates/products/product_detail.html',
    'templates/products/quick_view_modal_content.html',
]

# مسیر خروجی
output_file = 'custom_export.txt'

def write_file(filepath, out):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        out.write(f"\n\n====== FILE: {filepath} ======\n\n")
        out.write(content)
    except Exception as e:
        print(f"⚠️ Skipped: {filepath} - {e}")

with open(output_file, 'w', encoding='utf-8') as out:
    for path in INCLUDED_PATHS:
        if os.path.isdir(path):
            # اگر مسیر یک پوشه بود، همه فایل‌های درون آن را پردازش کن
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    write_file(full_path, out)
        elif os.path.isfile(path):
            # اگر مسیر یک فایل تکی بود
            write_file(path, out)
        else:
            print(f"❗ مسیر یافت نشد: {path}")
