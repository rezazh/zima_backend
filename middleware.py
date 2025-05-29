import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin

# لاگر مخصوص درخواست‌ها
request_logger = logging.getLogger('django.request')


class RequestLogMiddleware(MiddlewareMixin):
    """میدلور برای لاگ کردن درخواست‌ها و پاسخ‌ها"""

    def process_request(self, request):
        # ذخیره زمان شروع درخواست
        request.start_time = time.time()

        # لاگ کردن درخواست
        request_data = {
            'method': request.method,
            'path': request.path,
            'user': str(request.user),
            'ip': self.get_client_ip(request)
        }

        # لاگ کردن پارامترهای GET
        if request.GET:
            request_data['GET'] = dict(request.GET)

        # لاگ کردن پارامترهای POST (بدون اطلاعات حساس)
        if request.method == 'POST' and not request.path.startswith('/admin/'):
            try:
                body = request.POST.dict()
                # حذف اطلاعات حساس
                if 'password' in body:
                    body['password'] = '********'
                request_data['POST'] = body
            except:
                pass

        # لاگ کردن با سطح INFO
        request_logger.info(f"REQUEST_RECEIVED: {json.dumps(request_data)}")
        return None

    def process_response(self, request, response):
        # محاسبه زمان پردازش
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            # اطلاعات پاسخ
            response_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration': f"{duration:.3f}s",
                'user': str(request.user)
            }

            # لاگ کردن با سطح مناسب بر اساس کد وضعیت
            if 200 <= response.status_code < 300:
                request_logger.info(f"RESPONSE_SUCCESS: {json.dumps(response_data)}")
            elif 300 <= response.status_code < 400:
                request_logger.info(f"RESPONSE_REDIRECT: {json.dumps(response_data)}")
            elif 400 <= response.status_code < 500:
                request_logger.warning(f"RESPONSE_CLIENT_ERROR: {json.dumps(response_data)}")
            else:
                request_logger.error(f"RESPONSE_SERVER_ERROR: {json.dumps(response_data)}")

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip