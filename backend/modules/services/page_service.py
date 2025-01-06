# backend/modules/services/page_service.py

def calculate_pages_to_process(page_config, total_pages):
    """
    Calculate the total number of pages to process.

    :param page_config: Dictionary with page ranges per file and section,
                        with nested configurations for additional features.
                        Example:
                        {
                            'document.pdf': {
                                'Section1': {
                                    'pageRange': '2',
                                    'excel': {'columnsToRemove': ['Notes'], 'numericHeaderRemoval': True}
                                },
                                'Section2': {
                                    'pageRange': '5-7',
                                    'excel': {'columnsToRemove': []}
                                }
                            }
                        }
    :param total_pages: Total number of pages in the PDF.
    :return: Total number of pages to process.
    """
    if not page_config:
        return total_pages  # No specific page configuration, process the entire PDF

    pages_to_process = 0

    for file_name, sections in page_config.items():
        for section, config in sections.items():
            # Extract the page range from the section config
            pages = config.get('pageRange', '')

            if '-' in pages:  # Page range (e.g., "6-9")
                start, end = map(int, pages.split('-'))
                pages_to_process += (end - start + 1)
            elif ',' in pages:  # Specific pages (e.g., "5,6")
                pages_to_process += len(pages.split(','))
            elif pages.isdigit():  # Single page (e.g., "2")
                pages_to_process += 1
            else:
                raise ValueError(f"Invalid page range format: {pages}")

    return pages_to_process

def calculate_file_pages_to_process(file_config, total_pages):
    """
    Calculate pages to process for a specific file configuration.
    """
    if not file_config:
        return total_pages  # No specific configuration for this file

    pages_to_process = 0

    for section, config in file_config.items():
        if not isinstance(config, dict):
            raise ValueError(f"Expected a dictionary for section config, got {type(config).__name__}: {config}")

        pages = config.get('pageRange', '')

        if '-' in pages:  # Page range (e.g., "6-9")
            start, end = map(int, pages.split('-'))
            pages_to_process += (end - start + 1)
        elif ',' in pages:  # Specific pages (e.g., "5,6")
            pages_to_process += len(pages.split(','))
        elif pages.isdigit():  # Single page (e.g., "2")
            pages_to_process += 1
        else:
            raise ValueError(f"Invalid page range format: {pages}")

    return pages_to_process
