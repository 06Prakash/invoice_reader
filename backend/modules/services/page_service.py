# backend/modules/services/page_service.py

def calculate_pages_to_process(page_config, total_pages):
    """
    Calculate the total number of pages to process.

    :param page_config: Dictionary with page ranges per file
                        (e.g., {'renault_test_document.pdf': {'Test': '2', 'Rest': '6-9'}}).
    :param total_pages: Total number of pages in the PDF.
    :return: Total number of pages to process.
    """
    if not page_config:
        return total_pages  # No specific page configuration, process the entire PDF

    pages_to_process = 0

    for file_name, ranges in page_config.items():
        # Ranges is a dictionary, e.g., {'Test': '2', 'Rest': '6-9'}
        for section, pages in ranges.items():
            if '-' in pages:  # Page range (e.g., "6-9")
                start, end = map(int, pages.split('-'))
                pages_to_process += (end - start + 1)
            elif ',' in pages:  # Specific pages (e.g., "5,6")
                pages_to_process += len(pages.split(','))
            else:  # Single page (e.g., "2")
                pages_to_process += 1

    return pages_to_process

