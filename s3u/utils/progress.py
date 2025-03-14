"""
Progress bar utility for tracking long-running operations.
"""

import time

class ProgressBar:
    """
    A simple progress bar for terminal output.
    """
    def __init__(self, total, prefix='Progress:', suffix='Complete', length=50, fill='█', print_end="\r"):
        """
        Initialize a progress bar.
        
        Args:
            total (int): Total items
            prefix (str): Prefix string
            suffix (str): Suffix string
            length (int): Bar length
            fill (str): Bar fill character
            print_end (str): End character (e.g. "\r", "\n")
        """
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.fill = fill
        self.print_end = print_end
        self.current = 0
        self.start_time = time.time()
        self._update_bar(0)
        
    def update(self, increment=1):
        """
        Update the progress bar.
        
        Args:
            increment (int): Increment progress by this amount
        """
        self.current += increment
        self._update_bar(self.current)
        
    def _update_bar(self, current):
        """
        Internal method to update the progress bar display.
        """
        percent = ("{0:.1f}").format(100 * (current / float(self.total)))
        filled_length = int(self.length * current // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        
        # Calculate elapsed time and ETA
        elapsed = time.time() - self.start_time
        if current > 0:
            eta = elapsed * (self.total / current - 1)
            time_str = f"| {self._format_time(elapsed)} elapsed | ETA: {self._format_time(eta)}"
        else:
            time_str = ""
            
        # Print the bar
        print(f'\r{self.prefix} |{bar}| {percent}% {self.suffix} {time_str}', end=self.print_end)
        
        # Print a new line when complete
        if current == self.total:
            print()
            
    def _format_time(self, seconds):
        """Format time in a human-readable way."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds//60}m {seconds%60:.0f}s"
        else:
            return f"{seconds//3600}h {(seconds%3600)//60}m {seconds%3600%60:.0f}s"