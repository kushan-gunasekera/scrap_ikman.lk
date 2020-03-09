"""Collect the number of advertisements from the following categories,
    - tvs
    - mobile-phones
    - computers-tablets
    - air-conditions-electrical-fittings
    - electronic-home-appliances(from selected item from electric_home_appliance)
"""

import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from openpyxl import Workbook

full_dict = {}
serp_url = 'https://ikman.lk/data/serp'
ad_url = 'https://ikman.lk/en/ad/'
tv_brands = 'samsung|sony|innovex|lg|panasonic|haier|toshiba|jvc|philips|' \
            'sharp|nec|sansui|hisense|abans'
mobile_brands = 'apple|samsung|huawei|xiaomi|nokia|oppo|sony|vivo|lg|htc|' \
                'oneplus|lenovo|microsoft|micromax|google|e-tel|blackberry|' \
                'china-mobile|greentel|asus|dialog|zigo|sony-ericsson|' \
                'motorola|sky|acer|alcatel|zte|ag-tel|ipro|q-mobile|palm|' \
                'i-mate|realme|panasonic|doogee|sharp|umidigi|ccit|energizer|' \
                'intex|docomo'
pc_brands = 'intel|hp|dell|samsung|asus|lenovo|acer|toshiba|microsoft|sony|' \
            'ibm|huawei'
electric_home_appliance = {
    'refrigerator': 'ref|free|fri',
    'washing_machine': 'wash',
    'microwave': 'micro|wave',
    'rice_cooker': 'rice-cooker|rice-steamer',
    'gas_cooker': 'gas-cooker|gas-stove',
    'kettle': 'kettle',
    'blender': 'blender',
    'oven': 'oven'
}

date_format = '%Y-%m-%d'
days_re_search = 'day'
bump_re_search = 'bump_up'
min_hour_re_search = 'minutes|minute|hours|hour|just now'


def validate_day_and_bump_up(timestamp: str, search: str) -> bool:
    """To validate both days and bump_up formats.

    Args:
        timestamp: String type timestamp.
        search: Search value for regex.

    Returns:
        The return value. True for success, False otherwise.
    """

    _search = re.search(search, timestamp)

    if _search and search == days_re_search:
        return True
    elif _search and search == bump_re_search:
        return True
    elif _search and search == min_hour_re_search:
        return True
    return False


def validate_day(timestamp: str) -> int:
    """This function helps for maintaining 3 types such as break, continue and
    pass inside the called function.

    Args:
        timestamp: String type timestamp.

    Returns:
        An integer value.

            0: pass
            1: break
            2: continue
    """

    timestamp_days = int(timestamp.split(' ')[0])
    days = (datetime.now() - entered_date).days
    if timestamp_days == days:
        return 0
    elif timestamp_days > days:
        return 1
    elif timestamp_days < days:
        return 2


def timedelta_func(**kwargs) -> bool:
    """Subtract hours or minutes from datetime object.

    Args:
        **kwargs: Arbitrary keyword arguments.

    Returns:
        The return value. True for success, False otherwise.
    """

    datetime_obj = datetime.now() - timedelta(**kwargs)
    return datetime_obj.date() == entered_date.date()


def validate_hours_minutes(timestamp) -> bool:
    """Validate when the timestamp with hours or minutes

    Args:
        timestamp: String type timestamp.

    Returns:
        The return value. True for success, False otherwise.
    """

    split_timestamp = int(timestamp.split(' ')[0])

    _search = re.search(min_hour_re_search, timestamp)
    if not _search:
        return False

    group = _search.group()
    if group in ['minutes', 'minute']:
        return timedelta_func(minutes=split_timestamp)
    elif group in ['hours', 'hour']:
        return timedelta_func(hours=split_timestamp)
    elif group == 'just now':
        return True
    return False


def get_query_params(sort='date', order='desc', category_slug='tvs', location_slug='sri-lanka', page=1) -> str:
    """Create the query params value for `serp_url`.

    Args:
        sort: The sort value such as date or price.
        order: Order value shoudl be desc or asc.
        category_slug: The category slug value.
        location_slug: The location slug
        page: Current page.

    Returns:
        The completed query params value.
    """

    sort = f'sort={sort}'
    order = f'order={order}'
    category_slug = f'categorySlug={category_slug}'
    location_slug = f'locationSlug={location_slug}'
    page = f'page={page}'

    return f'?{sort}&{order}&{category_slug}&{location_slug}&{page}'


def get_ads(category_slug: str, page: int) -> list:
    """Get the list of ads from `serp_url`.

    Args:
        category_slug: The category slug to query.
        page: Current page value.

    Returns:
        The list of ads.
    """

    query_params = get_query_params(category_slug=category_slug, page=page)
    response = requests.get(f'{serp_url}{query_params}')
    ads: list = response.json()['ads']
    return ads


def calculate_common(brands, category='tvs', brand_position=2, filtering=True) -> dict:
    """This function handled following categories commonly.
        - tvs
        - mobile-phones
        - computers-tablets
        - air-conditions-electrical-fittings

    Args:
        brands: Brand names which can be easily grab from category slug field.
        category: One of the category value listed above.
        brand_position: The positions Where we can find Brand.
        filtering: False mean just get the count without taking brand name.

    Returns:
        Number of collected brands with the dict.
    """

    page = 1
    data_dict = {}

    while True:
        ads: list = get_ads(category, page)
        status = True

        for i in ads:
            slug: str = i['slug']
            timestamp: str = i['timeStamp']

            if validate_day_and_bump_up(timestamp, bump_re_search):
                continue

            if validate_day_and_bump_up(timestamp, days_re_search):
                validated = validate_day(timestamp)
                if validated == 1:
                    status = False
                    break
                elif validated == 2:
                    continue

            if validate_day_and_bump_up(timestamp, min_hour_re_search):
                if not validate_hours_minutes(timestamp):
                    continue

            print('*' * 100)
            print(f'timestamp: {timestamp}\nslug: {slug}')
            brand_search = re.search(brands, slug)
            if not filtering:
                brand = 'no_brand'
                print('no_brand')
            elif brand_search:
                print(f'group: {brand_search.group()}')
                brand = brand_search.group()
            else:
                url = f'{ad_url}{slug}'
                content = requests.get(url).text
                soup = BeautifulSoup(content, 'html.parser')
                dd = soup.find_all('dd')
                if dd:
                    brand = dd[brand_position-1].text
                else:
                    brand = 'Other Brand'
                brand: str = brand.lower().replace(' ', '_')
                print(f'brand: {brand}')

            if brand not in data_dict.keys():
                data_dict[brand] = 0

            data_dict[brand] += 1

        if not status:
            return data_dict

        page += 1


def recurse_home_appliance(content: str) -> str:
    """Check whether the value of `electric_home_appliance` in the `content`. If
        this is match any of the value in `electric_home_appliance` mean, we are
        expecting to count that category which is match the key of that value.

    Args:
        content: Slug value from the ads.

    Returns:
        Returns the matches key to continue the calculated category.
    """

    for key, value in electric_home_appliance.items():
        search = re.search(value, content)
        if search:
            return key


def calculate_home_appliance(category) -> dict:
    """To handle the electronic-home-appliances category from the `serp_url`.

    Args:
        category: The category field.

    Returns:
        Number of collected brands with the dict.
    """

    page = 1
    data_dict = {}

    while True:
        ads: list = get_ads(category, page)
        status = True

        for i in ads:
            slug = i['slug']
            timestamp = i['timeStamp']

            if validate_day_and_bump_up(timestamp, bump_re_search):
                continue

            if validate_day_and_bump_up(timestamp, days_re_search):
                validated = validate_day(timestamp)
                if validated == 1:
                    status = False
                    break
                elif validated == 2:
                    continue

            if validate_day_and_bump_up(timestamp, min_hour_re_search):
                if not validate_hours_minutes(timestamp):
                    continue

            category = recurse_home_appliance(slug)
            print('*' * 100)
            print(f'timestamp: {timestamp}\nslug: {slug}\ncategory: {category}')
            if not category:
                continue

            if category not in data_dict.keys():
                data_dict[category] = 0

            data_dict[category] += 1

        if not status:
            return data_dict

        page += 1


def validate_date(str_date: str) -> datetime or None:
    """Check whether the given date format is match to YYYY-MM-DD.

    Args:
        str_date: String type date.

    Returns:
        If given date beyond the current date or the format of the given date
        doesn't match with YYYY-MM-DD return None and otherwise returns datetime
        object.
    """

    try:
        global entered_date
        entered_date = datetime.strptime(str_date, date_format)
        if not entered_date > datetime.now():
            return entered_date

        message = 'you entered a future date'
        print(message)
    except ValueError as e:
        message = 'enter your date with following YYYY-MM-DD format'
        print(message)
    except Exception as e:
        print(e)
    return None


if __name__ == "__main__":
    while True:
        date_entry = input('\nEnter a valid date in YYYY-MM-DD format: ')
        date_obj = validate_date(date_entry)
        if date_obj:
            break

    # calculate tvs
    category = 'tvs'
    tv = calculate_common(tv_brands, category, 2)
    full_dict[category] = tv

    # calculate mobile phones
    category = 'mobile-phones'
    mobile = calculate_common(mobile_brands, category, 2)
    full_dict[category] = mobile

    # calculate computers and tablets
    category = 'computers-tablets'
    pc_tablets = calculate_common(pc_brands, category, 3)
    apple_macbook = pc_tablets.pop('apple_macbook', 0)
    apple_ipad = pc_tablets.pop('apple_ipad', 0)
    apple_imac = pc_tablets.pop('apple_imac', 0)
    apple_count = apple_macbook + apple_ipad + apple_imac
    pc_tablets['apple'] = apple_count
    full_dict[category] = pc_tablets

    # calculate air conditions electrical fittings
    category = 'air-conditions-electrical-fittings'
    ac = calculate_common('', category, filtering=False)
    full_dict[category] = ac

    # calculate electronic home appliances
    category = 'electronic-home-appliances'
    home_appliance = calculate_home_appliance(category)
    full_dict[category] = home_appliance

    print(f'full_dict: {full_dict}')

    workbook = Workbook()
    sheet = workbook.active

    x_count = 1
    for key, value in full_dict.items():
        sheet.cell(row=x_count, column=1, value=key)
        for key_1, value_1 in value.items():
            sheet.cell(row=x_count, column=2, value=key_1)
            sheet.cell(row=x_count, column=3, value=value_1)
            x_count += 1
        x_count += 1

    datetime_now = date_obj.strftime(date_format)
    workbook.save(filename=f"{datetime_now}.xlsx")
