import re
from pydantic_extra_types.phone_numbers import PhoneNumber


def sanitize_phone_number(phone_number: PhoneNumber):
    if isinstance(phone_number, int):
        return phone_number
    if not re.match(r'^\+\d+$', phone_number):
        raise ValueError("Phone number contains invalid characters")
    phone_number_digits = re.sub(r'\D', '', phone_number)
    return int(phone_number_digits)
