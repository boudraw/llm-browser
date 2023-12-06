from bs4 import BeautifulSoup, Comment, Tag

# Function to check if element is visible and relevant
def is_relevant_and_visible(element):
    irrelevant_ids_classes = ['footer', 'header', 'menu', 'hidden', 'template', 'sidebar', 'advert']
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    if isinstance(element, Comment):
        return False
    if hasattr(element, 'attrs'):
        class_id_text = ' '.join(element.attrs.get('class', []) + [element.attrs.get('id', '')])
        if any(irrelevant_word in class_id_text for irrelevant_word in irrelevant_ids_classes):
            return False
        if 'style' in element.attrs:
            styles = element.attrs['style'].lower().split(';')
            for style in styles:
                if 'display:none' in style or 'visibility:hidden' in style:
                    return False
    if element.name not in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'a', 'img']:
        return False
    return True


# Function to extract content to a limited depth
def extract_to_depth(tag, max_depth, current_depth=0):
    if current_depth >= max_depth:
        return
    for child in tag.contents:
        if isinstance(child, Tag):
            yield child
            yield from extract_to_depth(child, max_depth, current_depth + 1)
