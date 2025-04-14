from celery import Celery

app = Celery('zima')

@app.task
def clean_expired_cart_items():
    from orders.tasks import delete_expired_cart_items
    delete_expired_cart_items()