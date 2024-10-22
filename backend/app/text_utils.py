from datetime import datetime
import locale
import markdown
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_formatted_dutch_date():
    try:
        locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
    except locale.Error:
        logger.warning("Failed to set locale to nl_NL.UTF-8. Trying nl_NL.utf8...")

    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime('%A, %d %B %Y %H:%M:%S %Z')
    return formatted_date

def get_formatted_date_english():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')

def to_markdown(text):
    return markdown(text)

def format_content(content):
    # Remove leading and trailing whitespace
    content = f'[...] {content} [...]'
    return to_markdown(content)
