# پیچیده و سخت‌فهم
def process_data(data, type=None, filter_by=None, sort=False, limit=None):
    result = []
    if type:
        data = [item for item in data if item.get('type') == type]
    if filter_by:
        for key, value in filter_by.items():
            data = [item for item in data if item.get(key) == value]
    if sort:
        data = sorted(data, key=lambda x: x.get('date', 0))
    if limit:
        data = data[:limit]
    for item in data:
        result.append(process_item(item))
    return result


# ساده‌تر و واضح‌تر
def filter_by_type(data, type_value):
    return [item for item in data if item.get('type') == type_value]


def filter_by_criteria(data, criteria):
    for key, value in criteria.items():
        data = [item for item in data if item.get(key) == value]
    return data


def sort_by_date(data):
    return sorted(data, key=lambda x: x.get('date', 0))


def limit_results(data, limit):
    return data[:limit]


def process_data_improved(data, type=None, filter_by=None, sort=False, limit=None):
    if type:
        data = filter_by_type(data, type)
    if filter_by:
        data = filter_by_criteria(data, filter_by)
    if sort:
        data = sort_by_date(data)
    if limit:
        data = limit_results(data, limit)

    return [process_item(item) for item in data]