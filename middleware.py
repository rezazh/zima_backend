# در فایل middleware.py
import logging
import time
import json

logger = logging.getLogger('zima')


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # لاگ کردن درخواست ورودی
        if not request.path.startswith('/admin/') and not request.path.startswith('/static/'):
            request_data = {
                'method': request.method,
                'path': request.path,
                'user': str(request.user),
                'GET': dict(request.GET),
            }

            # لاگ کردن داده‌های POST (با حذف اطلاعات حساس)
            if request.method == 'POST' and hasattr(request, 'body'):
                try:
                    body = json.loads(request.body.decode('utf-8'))
                    # حذف اطلاعات حساس
                    if 'password' in body:
                        body['password'] = '********'
                    request_data['POST'] = body
                except:
                    request_data['POST'] = 'Unable to parse POST data'

            logger.info(f"Request received: {json.dumps(request_data)}")

        response = self.get_response(request)

        # لاگ کردن پاسخ
        if not request.path.startswith('/admin/') and not request.path.startswith('/static/'):
            duration = time.time() - start_time
            response_data = {
                'path': request.path,
                'status_code': response.status_code,
                'duration': f"{duration:.2f}s",
            }
            logger.info(f"Response sent: {json.dumps(response_data)}")

        return response