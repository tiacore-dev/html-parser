# utils/helpers.py

import re


def clean_html(html):
    """
    Удаляет лишние </div> внутри <td>, учитывая пробельные символы и переносы строк.
    """
    cleaned_html = re.sub(r'</div>\s*</td>', '</td>',
                          html, flags=re.IGNORECASE)
    return cleaned_html
