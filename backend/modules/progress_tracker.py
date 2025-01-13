from threading import Lock
import logging
from pdf2image import convert_from_path
from PyPDF2 import PdfReader

import os

logger = logging.getLogger(__name__)

class ProgressTracker:
    """
    A class to encapsulate progress tracking logic, avoiding global variables.
    """

    def __init__(self):
        self.total_pages_processed = 0  # Instance variable to track total pages processed
        self.lock = Lock()  # Lock to ensure thread-safe updates

    def initialize_progress(self, progress_file):
        """
        Initializes the progress tracker file.
        """
        with open(progress_file, 'w') as pf:
            pf.write('0')
        self.reset_progress()
    
    def get_total_pages(self, filename, upload_folder):
        """
        Calculate the total number of pages in the given PDF file.

        :param filename: Name of the PDF file
        :param upload_folder: Path to the folder containing the file
        :return: Total number of pages in the PDF
        """
        file_path = os.path.join(upload_folder, filename)
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                total_pages = len(reader.pages)
                return total_pages
        except Exception as e:
            logger.error(f"Failed to get total pages for {filename}: {e}")
            raise

    def calculate_total_pages(self, filenames, upload_folder):
        """
        Calculates the total number of pages for all files.
        """
        return sum(len(convert_from_path(os.path.join(upload_folder, filename), 300)) for filename in filenames)

    def update_progress(self, progress_file, pages_processed_in_task, total_pages, completion=False):
        """
        Updates the progress file by aggregating progress from all tasks.

        :param progress_file: Path to the progress file
        :param pages_processed_in_task: Number of pages processed in the current task
        :param total_pages: Total number of pages to process across all tasks
        :param completion: Boolean flag indicating if the task is complete
        """
        try:
            if total_pages <= 0:
                logger.error("Total pages must be greater than zero.")
                return
            
            with self.lock:
                # Safely update the total pages processed
                self.total_pages_processed += pages_processed_in_task
                self.total_pages_processed = min(self.total_pages_processed, total_pages)  # Cap at total_pages

                # Calculate progress
                if completion:
                    progress = 100
                else:
                    progress = min(int((self.total_pages_processed / total_pages) * 100), 99)

                # Log progress
                logger.info(
                    f"Updating progress: {progress}% (Processed: {self.total_pages_processed}/{total_pages} pages)"
                )

                # Write progress to the file
                try:
                    with open(progress_file, 'w') as pf:
                        pf.write(str(progress))
                except Exception as e:
                    logger.error(f"Error writing to progress file: {e}")

        except Exception as e:
            logger.error(f"Error updating progress: {e}")


    def reset_progress(self):
        """
        Resets the progress tracker for a new extraction process.
        """
        with self.lock:
            self.total_pages_processed = 0
            logger.info("Progress tracker reset successfully.")
