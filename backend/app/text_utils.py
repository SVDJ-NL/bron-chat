from datetime import datetime
import locale
import markdown
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_formatted_current_date_dutch():
    return get_formatted_date_dutch(datetime.now())

def get_formatted_current_date_english():
    return get_formatted_date_english(datetime.now())

def get_formatted_date_english(date):
    logger.debug(f"Formatting date EN: {date}")
    
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            # If the string is not in ISO format, you might need to specify the format
            # date = datetime.strptime(date, '%Y-%m-%d')
            return "Invalid date format"
            
    try:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    except locale.Error:
        logger.warning("Failed to set locale to en_US.UTF-8.")

    
    return date.strftime('%A, %d %B %Y')

def get_formatted_current_year():
    return datetime.now().year

def get_formatted_date_dutch(date):
    logger.debug(f"Formatting date NL: {date}")
    
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            # If the string is not in ISO format, you might need to specify the format
            # date = datetime.strptime(date, '%Y-%m-%d')
            return "Invalid date format"
        
    try:
        locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
    except locale.Error:
        logger.warning("Failed to set locale to nl_NL.UTF-8.")

    return date.strftime('%A, %d %B %Y')

def to_markdown(text):
    return markdown.markdown(text)

def format_content(content):
    # Remove leading and trailing whitespace
    content = re.sub(r'</?(?!span\b)\w+[^>]*>', '', content)
    content = f'[...] {content} [...]'
    return to_markdown(content)
