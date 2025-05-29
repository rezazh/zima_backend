import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('zima.requests')


class RequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000  # به میلی‌ثانیه

            # اطلاعات درخواست و پاسخ
            log_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'user': str(request.user),
                'duration': duration
            }

            # لاگ کردن با سطح مناسب بر اساس کد وضعیت
            if 200 <= response.status_code < 300:
                logger.info(f"REQUEST_SUCCESS: {json.dumps(log_data)}")
            elif 300 <= response.status_code < 400:
                logger.info(f"REQUEST_REDIRECT: {json.dumps(log_data)}")
            elif 400 <= response.status_code < 500:
                logger.warning(f"REQUEST_CLIENT_ERROR: {json.dumps(log_data)}")
            else:
                logger.error(f"REQUEST_SERVER_ERROR: {json.dumps(log_data)}")

        return response