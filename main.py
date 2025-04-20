import os
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import threading
import time
import queue
import customtkinter as ctk
from slide_extractor import SlideExtractor, batch_process
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

class SlideExtractorApp:
    def __init__(self, root):
        """Initialize the application window and settings"""
        self.root = root
        self.root.title("YouTube Slide Extractor")
        self.root.geometry("950x750")  # Increased window size for additional options

        # Queue for batch processing status updates
        self.status_queue = queue.Queue()

        # Store batch URLs
        self.batch_urls = []

        self.create_widgets()

        # Start queue monitor for batch processing
        self.queue_monitoring = True
        threading.Thread(target=self.monitor_queue, daemon=True).start()

    def create_widgets(self):
        """Create and arrange all GUI components"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title and subtitle
        ctk.CTkLabel(
            self.main_frame,
            text="YouTube Slide Extractor",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            self.main_frame,
            text="Extract slides from educational videos with ease",
            font=ctk.CTkFont(size=16)
        ).pack(pady=(0, 20))

        # Tab view for single/batch mode
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.tabview.add("Single Video")
        self.tabview.add("Batch Processing")

        # Set default tab
        self.tabview.set("Single Video")

        # Create widgets for Single Video tab
        self.create_single_mode_widgets(self.tabview.tab("Single Video"))

        # Create widgets for Batch Processing tab
        self.create_batch_mode_widgets(self.tabview.tab("Batch Processing"))

        # Add footer text
        ctk.CTkLabel(
            self.root,
            text="© 2025 YouTube Slide Extractor | Created with Python & CustomTkinter",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 10))

    def create_single_mode_widgets(self, parent_frame):
        """Create widgets for Single Video mode"""
        # Settings frame
        settings_frame = ctk.CTkFrame(parent_frame)
        settings_frame.pack(fill=tk.X, padx=10, pady=10)

        # URL Input
        url_frame = ctk.CTkFrame(settings_frame)
        url_frame.pack(fill=tk.X, padx=10, pady=10)

        ctk.CTkLabel(
            url_frame,
            text="YouTube URL:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.url_entry = ctk.CTkEntry(url_frame, width=500, height=40, font=ctk.CTkFont(size=14))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Parameters frame
        params_frame = ctk.CTkFrame(settings_frame)
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        # Frame Interval
        interval_frame = ctk.CTkFrame(params_frame)
        interval_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ctk.CTkLabel(
            interval_frame,
            text="Frame Interval (Seconds):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)

        self.interval_entry = ctk.CTkEntry(interval_frame, width=100, height=30)
        self.interval_entry.insert(0, "2")  # Lower default to catch more slides
        self.interval_entry.pack(pady=5)

        # Similarity Threshold
        threshold_frame = ctk.CTkFrame(params_frame)
        threshold_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ctk.CTkLabel(
            threshold_frame,
            text="Similarity Threshold (0.0 to 1.0):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)

        self.threshold_entry = ctk.CTkEntry(threshold_frame, width=100, height=30)
        self.threshold_entry.insert(0, "0.7")  # Lower default for better detection
        self.threshold_entry.pack(pady=5)

        # Help text for threshold
        ctk.CTkLabel(
            threshold_frame,
            text="Lower values (0.7) detect more slides. Higher values (0.9) are more selective.",
            font=ctk.CTkFont(size=12, slant="italic")
        ).pack(pady=(0, 5))

        # Resolution selector
        resolution_frame = ctk.CTkFrame(settings_frame)
        resolution_frame.pack(fill=tk.X, padx=10, pady=10)

        ctk.CTkLabel(
            resolution_frame,
            text="Video Resolution:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=tk.LEFT, padx=(10, 10), pady=10)

        # Add resolution options
        resolution_options = ["Highest Quality", "360p", "480p", "720p", "1080p"]
        self.resolution_var = ctk.StringVar(value=resolution_options[0])
        resolution_dropdown = ctk.CTkOptionMenu(
            resolution_frame,
            variable=self.resolution_var,
            values=resolution_options,
            width=150,
            height=30,
            font=ctk.CTkFont(size=14)
        )
        resolution_dropdown.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        # Help text for resolution
        ctk.CTkLabel(
            resolution_frame,
            text="Higher resolutions provide better quality but may take longer to download.",
            font=ctk.CTkFont(size=12, slant="italic")
        ).pack(side=tk.LEFT, padx=(0, 10), pady=10)

        # Export format options
        export_frame = ctk.CTkFrame(settings_frame)
        export_frame.pack(fill=tk.X, padx=10, pady=10)

        ctk.CTkLabel(
            export_frame,
            text="Export Format:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=tk.LEFT, padx=(10, 10), pady=10)

        # Add export format options (removed PowerPoint)
        export_options = ["PDF", "HTML", "Images Only"]
        self.export_var = ctk.StringVar(value=export_options[0])
        export_dropdown = ctk.CTkOptionMenu(
            export_frame,
            variable=self.export_var,
            values=export_options,
            width=200,
            height=30,
            font=ctk.CTkFont(size=14)
        )
        export_dropdown.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        # Options frame
        options_frame = ctk.CTkFrame(parent_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        # OCR Text Extraction option
        self.extract_text_var = tk.BooleanVar(value=False)
        extract_text_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="Extract text from slides using OCR (enables searchable PDFs)",
            variable=self.extract_text_var,
            font=ctk.CTkFont(size=14),
            onvalue=True,
            offvalue=False
        )
        extract_text_checkbox.pack(pady=10, padx=10, anchor=tk.W)

        # Delete PNG after export option
        self.delete_png_var = tk.BooleanVar(value=False)
        delete_png_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="Delete PNG images after export generation",
            variable=self.delete_png_var,
            font=ctk.CTkFont(size=14),
            onvalue=True,
            offvalue=False
        )
        delete_png_checkbox.pack(pady=10, padx=10, anchor=tk.W)

        # Progress frame
        progress_frame = ctk.CTkFrame(parent_frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=10)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Status: Ready",
            font=ctk.CTkFont(size=16)
        )
        self.progress_label.pack(anchor=tk.W, pady=(10, 5), padx=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.progress_bar.set(0)  # Initialize progress bar

        # Buttons frame
        buttons_frame = ctk.CTkFrame(parent_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=(10, 20))

        # Extract button
        self.extract_button = ctk.CTkButton(
            buttons_frame,
            text="Extract Slides",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.extract_slides
        )
        self.extract_button.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        # Open Output Folder button
        self.open_folder_button = ctk.CTkButton(
            buttons_frame,
            text="Open Output Folder",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.open_output_folder
        )
        self.open_folder_button.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        # Output log frame
        log_frame = ctk.CTkFrame(parent_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            log_frame,
            text="Output Log:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))

        # Output log text area
        self.log_text = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(size=14))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")  # Make read-only initially

    def create_batch_mode_widgets(self, parent_frame):
        """Create widgets for Batch Processing mode"""
        # Batch URLs frame
        batch_frame = ctk.CTkFrame(parent_frame)
        batch_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # URL input area
        url_entry_frame = ctk.CTkFrame(batch_frame)
        url_entry_frame.pack(fill=tk.X, padx=10, pady=10)

        ctk.CTkLabel(
            url_entry_frame,
            text="Enter YouTube URL:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.batch_url_entry = ctk.CTkEntry(url_entry_frame, width=400, height=40, font=ctk.CTkFont(size=14))
        self.batch_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Add URL button
        self.add_url_button = ctk.CTkButton(
            url_entry_frame,
            text="Add URL",
            font=ctk.CTkFont(size=14),
            height=40,
            width=100,
            command=self.add_batch_url
        )
        self.add_url_button.pack(side=tk.LEFT)

        # URL list frame
        url_list_frame = ctk.CTkFrame(batch_frame)
        url_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            url_list_frame,
            text="URLs to Process:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor=tk.W, pady=(10, 5), padx=10)

        # URL listbox
        self.url_listbox = scrolledtext.ScrolledText(
            url_list_frame,
            wrap=tk.WORD,
            height=8,
            font=("TkDefaultFont", 12)
        )
        self.url_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # URL list buttons
        url_buttons_frame = ctk.CTkFrame(batch_frame)
        url_buttons_frame.pack(fill=tk.X, padx=10, pady=5)

        # Clear selected button
        self.clear_selected_button = ctk.CTkButton(
            url_buttons_frame,
            text="Remove Selected",
            font=ctk.CTkFont(size=14),
            command=self.remove_selected_url
        )
        self.clear_selected_button.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)

        # Clear all button
        self.clear_all_button = ctk.CTkButton(
            url_buttons_frame,
            text="Clear All URLs",
            font=ctk.CTkFont(size=14),
            command=self.clear_all_urls
        )
        self.clear_all_button.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)

        # Import from file button
        self.import_urls_button = ctk.CTkButton(
            url_buttons_frame,
            text="Import URLs from File",
            font=ctk.CTkFont(size=14),
            command=self.import_urls_from_file
        )
        self.import_urls_button.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)

        # Batch settings frame
        batch_settings_frame = ctk.CTkFrame(parent_frame)
        batch_settings_frame.pack(fill=tk.X, padx=10, pady=10)

        # Left settings column
        left_settings = ctk.CTkFrame(batch_settings_frame)
        left_settings.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Interval
        ctk.CTkLabel(
            left_settings,
            text="Frame Interval (Seconds):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5, anchor=tk.W, padx=10)

        self.batch_interval_entry = ctk.CTkEntry(left_settings, width=100, height=30)
        self.batch_interval_entry.insert(0, "2")
        self.batch_interval_entry.pack(pady=5, anchor=tk.W, padx=10)

        # Similarity threshold
        ctk.CTkLabel(
            left_settings,
            text="Similarity Threshold:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5, anchor=tk.W, padx=10)

        self.batch_threshold_entry = ctk.CTkEntry(left_settings, width=100, height=30)
        self.batch_threshold_entry.insert(0, "0.7")
        self.batch_threshold_entry.pack(pady=5, anchor=tk.W, padx=10)

        # Right settings column
        right_settings = ctk.CTkFrame(batch_settings_frame)
        right_settings.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Resolution
        ctk.CTkLabel(
            right_settings,
            text="Video Resolution:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5, anchor=tk.W, padx=10)

        # Add resolution options
        batch_resolution_options = ["Highest Quality", "360p", "480p", "720p", "1080p"]
        self.batch_resolution_var = ctk.StringVar(value=batch_resolution_options[0])
        batch_resolution_dropdown = ctk.CTkOptionMenu(
            right_settings,
            variable=self.batch_resolution_var,
            values=batch_resolution_options,
            width=150,
            height=30,
            font=ctk.CTkFont(size=14)
        )
        batch_resolution_dropdown.pack(pady=5, anchor=tk.W, padx=10)

        # Export format
        ctk.CTkLabel(
            right_settings,
            text="Export Format:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5, anchor=tk.W, padx=10)

        # Add export format options (removed PowerPoint)
        batch_export_options = ["PDF", "HTML", "Images Only"]
        self.batch_export_var = ctk.StringVar(value=batch_export_options[0])
        batch_export_dropdown = ctk.CTkOptionMenu(
            right_settings,
            variable=self.batch_export_var,
            values=batch_export_options,
            width=200,
            height=30,
            font=ctk.CTkFont(size=14)
        )
        batch_export_dropdown.pack(pady=5, anchor=tk.W, padx=10)

        # Batch options frame
        batch_options_frame = ctk.CTkFrame(parent_frame)
        batch_options_frame.pack(fill=tk.X, padx=10, pady=10)

        # Extract text
        self.batch_extract_text_var = tk.BooleanVar(value=False)
        batch_extract_text_checkbox = ctk.CTkCheckBox(
            batch_options_frame,
            text="Extract text from slides using OCR",
            variable=self.batch_extract_text_var,
            font=ctk.CTkFont(size=14),
            onvalue=True,
            offvalue=False
        )
        batch_extract_text_checkbox.pack(pady=5, padx=10, anchor=tk.W)

        # Parallel processing
        self.batch_parallel_var = tk.BooleanVar(value=True)
        batch_parallel_checkbox = ctk.CTkCheckBox(
            batch_options_frame,
            text="Process videos in parallel (faster but uses more resources)",
            variable=self.batch_parallel_var,
            font=ctk.CTkFont(size=14),
            onvalue=True,
            offvalue=False
        )
        batch_parallel_checkbox.pack(pady=5, padx=10, anchor=tk.W)

        # Delete PNG after export
        self.batch_delete_png_var = tk.BooleanVar(value=False)
        batch_delete_png_checkbox = ctk.CTkCheckBox(
            batch_options_frame,
            text="Delete PNG images after export generation",
            variable=self.batch_delete_png_var,
            font=ctk.CTkFont(size=14),
            onvalue=True,
            offvalue=False
        )
        batch_delete_png_checkbox.pack(pady=5, padx=10, anchor=tk.W)

        # Batch progress
        batch_progress_frame = ctk.CTkFrame(parent_frame)
        batch_progress_frame.pack(fill=tk.X, padx=10, pady=10)

        self.batch_progress_label = ctk.CTkLabel(
            batch_progress_frame,
            text="Status: Ready",
            font=ctk.CTkFont(size=16)
        )
        self.batch_progress_label.pack(anchor=tk.W, pady=(10, 5), padx=10)

        self.batch_progress_bar = ctk.CTkProgressBar(batch_progress_frame)
        self.batch_progress_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.batch_progress_bar.set(0)  # Initialize progress bar

        # Batch control buttons
        batch_buttons_frame = ctk.CTkFrame(parent_frame)
        batch_buttons_frame.pack(fill=tk.X, padx=10, pady=(10, 20))

        # Start batch processing button
        self.start_batch_button = ctk.CTkButton(
            batch_buttons_frame,
            text="Start Batch Processing",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.start_batch_processing
        )
        self.start_batch_button.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        # Open batch output folder button
        self.open_batch_folder_button = ctk.CTkButton(
            batch_buttons_frame,
            text="Open Output Folder",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.open_output_folder
        )
        self.open_batch_folder_button.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        # Batch log frame
        batch_log_frame = ctk.CTkFrame(parent_frame)
        batch_log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            batch_log_frame,
            text="Batch Processing Log:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))

        # Batch log text area
        self.batch_log_text = ctk.CTkTextbox(batch_log_frame, font=ctk.CTkFont(size=14))
        self.batch_log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.batch_log_text.configure(state="disabled")  # Make read-only initially

    def add_batch_url(self):
        """Add a URL to the batch processing list"""
        url = self.batch_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        # Add URL to list
        self.batch_urls.append(url)

        # Update the URL listbox
        self.url_listbox.configure(state="normal")
        self.url_listbox.insert(tk.END, f"{url}\n")
        self.url_listbox.configure(state="disabled")

        # Clear the URL entry
        self.batch_url_entry.delete(0, tk.END)

        # Update the batch progress label
        self.batch_progress_label.configure(text=f"Status: Ready - {len(self.batch_urls)} URLs in queue")

    def remove_selected_url(self):
        """Remove the selected URL from the batch list"""
        try:
            # Get the currently selected text
            selected_text = self.url_listbox.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            
            # Remove it from batch_urls
            if selected_text in self.batch_urls:
                self.batch_urls.remove(selected_text)
                
            # Rebuild the listbox
            self.url_listbox.configure(state="normal")
            self.url_listbox.delete(1.0, tk.END)
            for url in self.batch_urls:
                self.url_listbox.insert(tk.END, f"{url}\n")
            self.url_listbox.configure(state="disabled")
            
            # Update status
            self.batch_progress_label.configure(text=f"Status: Ready - {len(self.batch_urls)} URLs in queue")
        except tk.TclError:
            # No selection
            messagebox.showinfo("Information", "Please select a URL to remove first")

    def clear_all_urls(self):
        """Clear all URLs from the batch list"""
        self.batch_urls = []
        self.url_listbox.configure(state="normal")
        self.url_listbox.delete(1.0, tk.END)
        self.url_listbox.configure(state="disabled")
        self.batch_progress_label.configure(text="Status: Ready - 0 URLs in queue")

    def import_urls_from_file(self):
        """Import URLs from a text file"""
        file_path = filedialog.askopenfilename(
            title="Import URLs from File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as file:
                imported_urls = [line.strip() for line in file if line.strip()]
                
            # Add to existing URLs
            self.batch_urls.extend(imported_urls)
            
            # Update the listbox
            self.url_listbox.configure(state="normal")
            self.url_listbox.delete(1.0, tk.END)
            for url in self.batch_urls:
                self.url_listbox.insert(tk.END, f"{url}\n")
            self.url_listbox.configure(state="disabled")
            
            # Update status
            self.batch_progress_label.configure(text=f"Status: Ready - {len(self.batch_urls)} URLs in queue")
            self.update_batch_log(f"Imported {len(imported_urls)} URLs from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import URLs: {str(e)}")

    def extract_slides(self):
        """Function to handle slide extraction for single video mode"""
        # Get input values
        url = self.url_entry.get()
        
        # Validate URL input
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        # Validate numeric inputs
        try:
            interval = int(self.interval_entry.get())
            threshold = float(self.threshold_entry.get())
            
            if interval < 1:
                messagebox.showerror("Error", "Interval must be at least 1 second")
                return
                
            if threshold < 0.1 or threshold > 1.0:
                messagebox.showerror("Error", "Threshold must be between 0.1 and 1.0")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for interval and threshold")
            return
            
        # Get selected resolution
        resolution = self.resolution_var.get()
        
        # Convert GUI resolution option to the format expected by the backend
        if resolution == "Highest Quality":
            resolution = "highest"
            
        # Get export format
        export_format = self.export_var.get()
        format_mapping = {
            "PDF": "pdf",
            "HTML": "html",
            "Images Only": "images"
        }
        export_format_value = format_mapping.get(export_format, "pdf")
        
        # Get OCR text extraction option
        extract_text = self.extract_text_var.get()
        
        # Disable inputs while processing
        self.disable_inputs()
        
        # Update status and start progress bar
        self.progress_label.configure(text="Status: Downloading video...")
        self.progress_bar.start()
        
        # Update log
        self.update_log(f"Starting extraction from: {url}\n")
        self.update_log(f"Parameters: Interval = {interval}s, Threshold = {threshold}, Resolution = {resolution}\n")
        self.update_log(f"Export Format: {export_format}, Text Extraction: {'Enabled' if extract_text else 'Disabled'}\n")
        
        # Start the slide extraction in a separate thread
        threading.Thread(
            target=self.start_slide_extraction,
            args=(url, interval, threshold, resolution, extract_text, export_format_value),
            daemon=True
        ).start()

    def start_slide_extraction(self, url, interval, threshold, resolution, extract_text, export_format):
        """Threaded function for slide extraction"""
        try:
            # Create a SlideExtractor instance
            extractor = SlideExtractor(
                video_url=url,
                interval=interval,
                similarity_threshold=threshold,
                resolution=resolution,
                extract_text=extract_text,
                export_format=export_format
            )
            
            # Perform slide extraction
            self.update_log("Downloading video...\n")
            slides = extractor.extract_slides()
            
            if slides and len(slides) > 0:
                # Update progress and log based on chosen export format
                format_display_name = {
                    "pdf": "PDF",
                    "html": "HTML slideshow",
                    "images": "image files"
                }.get(export_format, "output")
                
                self.progress_label.configure(
                    text=f"Status: Extraction Complete! Found {len(slides)} slides. {format_display_name.capitalize()} created."
                )
                
                self.update_log(f"Extraction complete! Found {len(slides)} slides.\n")
                self.update_log(f"Created {format_display_name} in the output directory.\n")
                
                # Show extracted slides in log
                for slide in slides:
                    self.update_log(f" - {slide}\n")
                
                # Delete PNG files if option is checked
                if self.delete_png_var.get() and export_format != "images":
                    self.delete_png_files("slides")
            else:
                self.progress_label.configure(
                    text="Status: No slides were extracted. Try adjusting parameters."
                )
                self.update_log("No slides were extracted. Try adjusting parameters.\n")
        except Exception as e:
            self.progress_label.configure(text=f"Error: {str(e)}")
            self.update_log(f"Error: {str(e)}\n")
        finally:
            # Stop the progress bar
            self.progress_bar.stop()
            # Re-enable inputs
            self.enable_inputs()

    def start_batch_processing(self):
        """Start batch processing of multiple YouTube URLs"""
        # Check if we have any URLs
        if not self.batch_urls:
            messagebox.showerror("Error", "Please add at least one YouTube URL to the batch queue")
            return
            
        # Validate numeric inputs
        try:
            interval = int(self.batch_interval_entry.get())
            threshold = float(self.batch_threshold_entry.get())
            
            if interval < 1:
                messagebox.showerror("Error", "Interval must be at least 1 second")
                return
                
            if threshold < 0.1 or threshold > 1.0:
                messagebox.showerror("Error", "Threshold must be between 0.1 and 1.0")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for interval and threshold")
            return
            
        # Get selected resolution
        resolution = self.batch_resolution_var.get()
        if resolution == "Highest Quality":
            resolution = "highest"
            
        # Get export format
        export_format = self.batch_export_var.get()
        format_mapping = {
            "PDF": "pdf",
            "HTML": "html",
            "Images Only": "images"
        }
        export_format_value = format_mapping.get(export_format, "pdf")
        
        # Get options
        extract_text = self.batch_extract_text_var.get()
        parallel = self.batch_parallel_var.get()
        
        # Disable inputs
        self.disable_batch_inputs()
        
        # Update progress
        self.batch_progress_label.configure(text=f"Status: Starting batch processing of {len(self.batch_urls)} URLs...")
        self.batch_progress_bar.start()
        
        # Update log
        self.update_batch_log(f"Starting batch processing of {len(self.batch_urls)} URLs\n")
        self.update_batch_log(f"Parameters: Interval = {interval}s, Threshold = {threshold}, Resolution = {resolution}\n")
        self.update_batch_log(f"Export Format: {export_format}, Text Extraction: {'Enabled' if extract_text else 'Disabled'}\n")
        self.update_batch_log(f"Parallel Processing: {'Enabled' if parallel else 'Disabled'}\n\n")
        
        # Start batch processing in a separate thread
        threading.Thread(
            target=self.run_batch_processing,
            args=(interval, threshold, resolution, extract_text, export_format_value, parallel),
            daemon=True
        ).start()

    def run_batch_processing(self, interval, threshold, resolution, extract_text, export_format, parallel):
        """Run the batch processing in a separate thread"""
        try:
            # Define the status callback function
            def status_callback(url, message):
                self.status_queue.put((url, message))
                
            # Start batch processing
            results = batch_process(
                urls=self.batch_urls,
                output_dir="slides",
                interval=interval,
                similarity_threshold=threshold,
                resolution=resolution,
                extract_text=extract_text,
                export_format=export_format,
                parallel=parallel,
                max_workers=3,
                status_callback=status_callback
            )
            
            # Process completed
            total_slides = sum(result['slide_count'] for result in results.values())
            
            # Update progress and log
            self.batch_progress_label.configure(text=f"Status: Batch processing complete! Extracted {total_slides} slides from {len(results)} videos.")
            self.update_batch_log(f"\nBatch processing complete!\n")
            self.update_batch_log(f"Total videos processed: {len(results)}\n")
            self.update_batch_log(f"Total slides extracted: {total_slides}\n\n")
            
            # Log details for each video
            for url, result in results.items():
                self.update_batch_log(f"URL: {url}\n")
                self.update_batch_log(f" - Slides extracted: {result['slide_count']}\n")
                self.update_batch_log(f" - Output directory: {result['output_dir']}\n\n")
                
            # Delete PNG files if option is checked
            if self.batch_delete_png_var.get() and export_format != "images":
                for result in results.values():
                    self.delete_png_files(result['output_dir'])
        except Exception as e:
            self.batch_progress_label.configure(text=f"Error: {str(e)}")
            self.update_batch_log(f"Error in batch processing: {str(e)}\n")
        finally:
            # Stop the progress bar
            self.batch_progress_bar.stop()
            # Re-enable inputs
            self.enable_batch_inputs()

    def monitor_queue(self):
        """Monitor the status queue for batch processing updates"""
        while self.queue_monitoring:
            try:
                url, message = self.status_queue.get(block=False)
                # Format the URL for display (shortened if too long)
                short_url = url[:30] + "..." if len(url) > 30 else url
                self.update_batch_log(f"[{short_url}] {message}\n")
                self.status_queue.task_done()
            except queue.Empty:
                # If queue is empty, sleep a bit
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in queue monitor: {e}")
                time.sleep(1)

    def enable_inputs(self):
        """Enable inputs after extraction is complete"""
        self.url_entry.configure(state="normal")
        self.interval_entry.configure(state="normal")
        self.threshold_entry.configure(state="normal")
        self.extract_button.configure(state="normal")
        self.open_folder_button.configure(state="normal")

    def disable_inputs(self):
        """Disable inputs during processing"""
        self.url_entry.configure(state="disabled")
        self.interval_entry.configure(state="disabled")
        self.threshold_entry.configure(state="disabled")
        self.extract_button.configure(state="disabled")
        self.open_folder_button.configure(state="disabled")

    def enable_batch_inputs(self):
        """Enable batch mode inputs after processing"""
        self.batch_url_entry.configure(state="normal")
        self.batch_interval_entry.configure(state="normal")
        self.batch_threshold_entry.configure(state="normal")
        self.add_url_button.configure(state="normal")
        self.clear_selected_button.configure(state="normal")
        self.clear_all_button.configure(state="normal")
        self.import_urls_button.configure(state="normal")
        self.start_batch_button.configure(state="normal")
        self.open_batch_folder_button.configure(state="normal")

    def disable_batch_inputs(self):
        """Disable batch mode inputs during processing"""
        self.batch_url_entry.configure(state="disabled")
        self.batch_interval_entry.configure(state="disabled")
        self.batch_threshold_entry.configure(state="disabled")
        self.add_url_button.configure(state="disabled")
        self.clear_selected_button.configure(state="disabled")
        self.clear_all_button.configure(state="disabled")
        self.import_urls_button.configure(state="disabled")
        self.start_batch_button.configure(state="disabled")
        self.open_batch_folder_button.configure(state="disabled")

    def open_output_folder(self):
        """Open the output folder in file explorer"""
        output_dir = "slides"
        if os.path.exists(output_dir):
            # Open folder in file explorer (works on Windows, macOS, and most Linux)
            if os.name == 'nt':  # Windows
                os.startfile(output_dir)
            elif os.name == 'posix':  # macOS and Linux
                import subprocess
                try:
                    subprocess.Popen(['xdg-open', output_dir])  # Linux
                except FileNotFoundError:
                    try:
                        subprocess.Popen(['open', output_dir])  # macOS
                    except:
                        messagebox.showinfo("Information", f"Output folder is at: {os.path.abspath(output_dir)}")
        else:
            messagebox.showinfo("Information", "No output folder found. Extract slides first.")

    def delete_png_files(self, folder_path):
        """Delete all PNG files in the specified folder"""
        try:
            count = 0
            self.update_log("Deleting PNG files...\n")
            
            for filename in os.listdir(folder_path):
                if filename.endswith('.png'):
                    file_path = os.path.join(folder_path, filename)
                    os.remove(file_path)
                    self.update_log(f" - Deleted: {filename}\n")
                    count += 1
                    
            self.update_log(f"Deleted {count} PNG files.\n")
            self.progress_label.configure(text=f"Status: Export completed and {count} PNG files deleted.")
        except Exception as e:
            self.update_log(f"Error deleting PNG files: {str(e)}\n")

    def update_log(self, message):
        """Update the log text area with a new message"""
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)  # Scroll to the end
        self.log_text.configure(state="disabled")

    def update_batch_log(self, message):
        """Update the batch log text area with a new message"""
        self.batch_log_text.configure(state="normal")
        self.batch_log_text.insert(tk.END, message)
        self.batch_log_text.see(tk.END)  # Scroll to the end
        self.batch_log_text.configure(state="disabled")

# Run the application
if __name__ == "__main__":
    root = ctk.CTk()
    app = SlideExtractorApp(root)
    root.mainloop()
