'''
pip install scikit-image
pip install pytube
pip install pytubefix
pip install pytesseract
pip install reportlab
pip install python-pptx
pip install aspose-slides
'''
import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
from datetime import timedelta
import argparse
import threading
import queue
import time
import shutil
from skimage.metrics import structural_similarity as ssim
from pytubefix import YouTube
from pytubefix.cli import on_progress
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import base64
import re

class SlideExtractor:
    def __init__(self, video_url, output_dir="slides", interval=5, similarity_threshold=0.7, 
                 ocr_confidence=30, resolution="highest", extract_text=False, 
                 export_format="pdf", batch_mode=False):
        """
        Initialize the SlideExtractor with the given parameters.
        
        Args:
            video_url (str): URL of the YouTube video
            output_dir (str): Directory to save the extracted slides
            interval (int): Time interval (in seconds) between frame checks
            similarity_threshold (float): Threshold for determining if slides are different (0.0-1.0)
            ocr_confidence (int): Confidence threshold for OCR text detection
            resolution (str): Desired resolution for the video download ("highest", "360p", "480p", "720p", "1080p")
            extract_text (bool): Whether to extract text from slides using OCR
            export_format (str): Format to export slides ("pdf", "html", "images")
            batch_mode (bool): Whether this extractor is running in batch mode
        """
        self.video_url = video_url
        self.output_dir = output_dir
        self.interval = interval
        self.similarity_threshold = similarity_threshold
        self.ocr_confidence = ocr_confidence
        self.resolution = resolution
        self.extract_text = extract_text
        self.export_format = export_format
        self.batch_mode = batch_mode
        self.video_path = os.path.join(self.output_dir, "temp_video.mp4")
        self.previous_text = ""
        self.extracted_text = {}  # Dictionary to store extracted text by slide
        self.status_queue = queue.Queue() if batch_mode else None
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def download_video(self):
        """
        Download the YouTube video using pytubefix with the selected resolution.
        
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            print(f"Downloading video from: {self.video_url}")
            self._update_status(f"Downloading video from: {self.video_url}")
            
            # Create a YouTube object with progress callback
            yt = YouTube(self.video_url, on_progress_callback=on_progress)
            
            # Get video information
            print(f"Title: {yt.title}")
            print(f"Duration: {yt.length} seconds")
            self._update_status(f"Title: {yt.title}, Duration: {yt.length} seconds")
            
            # Get stream based on selected resolution
            if self.resolution == "highest":
                # Get the highest resolution stream with video and audio
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                if not stream:
                    # If no combined stream is available, get the highest resolution video stream
                    stream = yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first()
            else:
                # Try to get a progressive stream with the selected resolution
                stream = yt.streams.filter(progressive=True, resolution=self.resolution, file_extension='mp4').first()
                
                # If no progressive stream for the selected resolution, try adaptive stream
                if not stream:
                    stream = yt.streams.filter(resolution=self.resolution, file_extension='mp4').first()
                
                # If still no stream, fall back to highest resolution
                if not stream:
                    print(f"No stream available with resolution {self.resolution}. Falling back to highest resolution.")
                    self._update_status(f"No stream with {self.resolution} available. Using highest resolution.")
                    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                    if not stream:
                        stream = yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first()
            
            if stream:
                # Start download
                print(f"Downloading {stream.resolution} stream...")
                self._update_status(f"Downloading {stream.resolution} stream...")
                video_file = stream.download(output_path=os.path.dirname(self.video_path), 
                                           filename=os.path.basename(self.video_path))
                print(f"Download complete! Video saved to: {video_file}")
                self._update_status(f"Download complete! Selected resolution: {stream.resolution}")
                return True
            else:
                print("No suitable stream found for this video.")
                self._update_status("Error: No suitable stream found for this video.")
                return False
        except Exception as e:
            print(f"Error downloading video: {str(e)}")
            self._update_status(f"Error downloading video: {str(e)}")
            return False

    def extract_slides(self):
        """
        Process the video to extract slides.
        
        Returns:
            list: List of extracted slide filenames or empty list if extraction failed
        """
        # Download the video if it doesn't exist
        if not os.path.exists(self.video_path):
            if not self.download_video():
                return []
        
        # Open the video file
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {self.video_path}")
            self._update_status(f"Error: Could not open video file {self.video_path}")
            return []
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * self.interval)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"Video duration: {timedelta(seconds=duration)}")
        print(f"Processing frames every {self.interval} seconds...")
        self._update_status(f"Video duration: {timedelta(seconds=duration)}")
        self._update_status(f"Processing frames every {self.interval} seconds...")
        
        prev_frame = None
        slide_count = 0
        extracted_slides = []
        
        # Process frames at regular intervals
        for frame_num in range(0, total_frames, frame_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Calculate timestamp for the current frame
            current_time = frame_num / fps
            timestamp = str(timedelta(seconds=current_time)).split(".")[0]
            
            # First frame is always saved
            if prev_frame is None:
                filename = self._save_slide(frame, timestamp, slide_count)
                extracted_slides.append(filename)
                prev_frame = frame
                slide_count += 1
                
                # Extract text if enabled
                if self.extract_text:
                    self._extract_and_store_text(frame, filename)
                continue
            
            # Check if current frame is a different slide using both similarity and text comparison
            if self._is_different_slide(prev_frame, frame):
                filename = self._save_slide(frame, timestamp, slide_count)
                extracted_slides.append(filename)
                prev_frame = frame
                slide_count += 1
                
                # Extract text if enabled
                if self.extract_text:
                    self._extract_and_store_text(frame, filename)
        
        # Release the video capture object
        cap.release()
        
        print(f"Extracted {slide_count} slides to {self.output_dir}")
        self._update_status(f"Extracted {slide_count} slides to {self.output_dir}")
        
        # Clean up temp video file if needed
        if os.path.exists(self.video_path):
            os.remove(self.video_path)
        
        # Export in the selected format
        if self.export_format == "pdf":
            self.convert_slides_to_pdf(extracted_slides)
        elif self.export_format == "html":
            self.convert_slides_to_html(extracted_slides)
        
        return extracted_slides

    def _is_different_slide(self, frame1, frame2):
        """
        Determine if two frames represent different slides.
        
        Args:
            frame1: First frame for comparison
            frame2: Second frame for comparison
            
        Returns:
            bool: True if frames are different slides, False otherwise
        """
        # Convert frames to grayscale for comparison
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Calculate structural similarity between frames
        score, _ = ssim(gray1, gray2, full=True)
        
        # If similarity is below threshold, it's a different slide
        if score < self.similarity_threshold:
            return True
        
        # Additional check using histogram comparison
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        hist_diff = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        if hist_diff < 0.95:
            return True
        
        # Additional check using OCR text comparison
        text1 = self._extract_text(frame1)
        text2 = self._extract_text(frame2)
        
        if text1 and text2:
            # Compare text content between frames
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if len(words1) > 3 and len(words2) > 3:
                # Only compare if enough text is detected
                common_words = words1.intersection(words2)
                
                # Calculate difference ratio in text content
                diff_ratio = 1 - len(common_words) / max(len(words1), len(words2))
                
                # If text differs significantly, it's a different slide
                if diff_ratio > 0.3:
                    return True
        
        return False

    def _extract_text(self, frame):
        """
        Extract text from a frame using OCR.
        
        Args:
            frame: The frame to extract text from
            
        Returns:
            str: Extracted text
        """
        try:
            # Convert to grayscale and threshold for better OCR
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, threshold = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Save temporary image for OCR processing
            temp_image_path = os.path.join(self.output_dir, "temp_ocr.png")
            cv2.imwrite(temp_image_path, threshold)
            
            # Extract text using pytesseract with improved parameters
            text = pytesseract.image_to_string(
                Image.open(temp_image_path),
                config=f'--psm 6 --oem 3 -c min_characters_to_try=5'
            )
            
            # Delete temporary file
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                
            return text.strip()
        except Exception as e:
            print(f"OCR error: {e}")
            return ""

    def _extract_and_store_text(self, frame, slide_filename):
        """
        Extract text from a frame and store it in the extracted_text dictionary.
        
        Args:
            frame: The frame to extract text from
            slide_filename: The filename of the slide for dictionary key
        """
        text = self._extract_text(frame)
        if text:
            self.extracted_text[slide_filename] = text
            print(f"Extracted text from {slide_filename}:")
            print(text[:150] + "..." if len(text) > 150 else text)
            self._update_status(f"Extracted text from {slide_filename}")

    def _save_slide(self, frame, timestamp, count):
        """
        Save a frame as a slide image.
        
        Args:
            frame: The frame to save
            timestamp: Timestamp of the frame
            count: Slide number
            
        Returns:
            str: Filename of the saved slide
        """
        # Create filename with slide number and timestamp
        filename = f"slide_{count:03d}_{timestamp.replace(':', '-')}.png"
        path = os.path.join(self.output_dir, filename)
        
        # Convert BGR to RGB for proper color display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        pil_image.save(path)
        
        print(f"Saved slide: {filename}")
        return filename

    def convert_slides_to_pdf(self, slide_filenames=None):
        """
        Convert all extracted slides to a single searchable PDF file.
        
        Args:
            slide_filenames: Optional list of slide filenames to include
            
        Returns:
            str: Path to the created PDF file
        """
        # If no specific filenames are provided, get all slides in the directory
        if slide_filenames is None:
            slide_filenames = sorted([
                file for file in os.listdir(self.output_dir)
                if file.lower().endswith(".png") and file.startswith("slide_")
            ])
            
        if not slide_filenames:
            print("No slide images found to convert.")
            self._update_status("No slide images found to convert to PDF.")
            return None
        
        # Define the output PDF path
        pdf_path = os.path.join(self.output_dir, "slides_output.pdf")
        
        # Create PDF using reportlab
        c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # Add each slide to the PDF
        for img_filename in slide_filenames:
            img_path = os.path.join(self.output_dir, img_filename)
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            # Calculate aspect ratio to fit on letter page
            width, height = letter
            ratio = min(width / img_width, height / img_height) * 0.9
            
            # Center the image on the page
            x = (width - img_width * ratio) / 2
            y = (height - img_height * ratio) / 2
            
            # Add the image
            c.drawImage(img_path, x, y, width=img_width * ratio, height=img_height * ratio)
            
            # If text extraction is enabled, add the text layer for searchability
            if self.extract_text and img_filename in self.extracted_text:
                text = self.extracted_text[img_filename]
                if text:
                    # Add invisible text layer for searchability
                    c.setFont("Helvetica", 1)  # Very small font, effectively invisible
                    c.setFillColorRGB(1, 1, 1, 0)  # Transparent text
                    
                    # Split text into lines and add at the bottom of the page
                    for i, line in enumerate(text.split('\n')):
                        if line.strip():
                            c.drawString(10, 10 + (i * 2), line)
            
            c.showPage()
        
        c.save()
        print(f"PDF created at: {pdf_path}")
        self._update_status(f"PDF created at: {pdf_path}")
        return pdf_path

    def convert_slides_to_html(self, slide_filenames=None):
        """
        Convert all extracted slides to an HTML slideshow with improved design.
        
        Args:
            slide_filenames: Optional list of slide filenames to include
            
        Returns:
            str: Path to the created HTML file
        """
        # If no specific filenames are provided, get all slides in the directory
        if slide_filenames is None:
            slide_filenames = sorted([
                file for file in os.listdir(self.output_dir)
                if file.lower().endswith(".png") and file.startswith("slide_")
            ])
            
        if not slide_filenames:
            print("No slide images found to convert.")
            self._update_status("No slide images found to convert to HTML.")
            return None
        
        # Create images subfolder for HTML
        html_images_dir = os.path.join(self.output_dir, "html_images")
        os.makedirs(html_images_dir, exist_ok=True)
        
        # Copy images to the HTML images directory
        for img_file in slide_filenames:
            source_path = os.path.join(self.output_dir, img_file)
            dest_path = os.path.join(html_images_dir, img_file)
            shutil.copy2(source_path, dest_path)
        
        # Define the output HTML path
        html_path = os.path.join(self.output_dir, "slides_output.html")
        
        # Create an improved HTML slideshow with better design
        with open(html_path, 'w', encoding='utf-8') as f:
            # Write HTML header with improved CSS styling
            f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Extracted Slides Presentation</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        header h1 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .slide-controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 15px;
            background-color: #34495e;
            border-radius: 0 0 8px 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .control-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background-color: #3498db;
            color: white;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .control-btn:hover {
            background-color: #2980b9;
        }
        
        .control-btn:disabled {
            background-color: #95a5a6;
            cursor: not-allowed;
        }
        
        .slide-number {
            display: flex;
            align-items: center;
            font-size: 16px;
            color: white;
        }
        
        .slide-container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            text-align: center;
        }
        
        .slide {
            display: none;
            flex-direction: column;
            align-items: center;
        }
        
        .slide.active {
            display: flex;
        }
        
        .slide img {
            max-width: 100%;
            max-height: 70vh;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            border-radius: 4px;
        }
        
        .slide-info {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            width: 100%;
        }
        
        .slide-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .slide-text {
            text-align: left;
            font-size: 16px;
            white-space: pre-wrap;
            overflow-y: auto;
            max-height: 200px;
            padding: 10px;
            background-color: #fff;
            border: 1px solid #eee;
            border-radius: 4px;
        }
        
        footer {
            text-align: center;
            padding: 15px;
            background-color: #2c3e50;
            color: white;
            border-radius: 8px;
            margin-top: 20px;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            header h1 {
                font-size: 20px;
            }
            
            .control-btn {
                padding: 8px 15px;
                font-size: 14px;
            }
            
            .slide-info {
                margin-top: 15px;
                padding: 10px;
            }
            
            .slide-title {
                font-size: 16px;
            }
            
            .slide-text {
                font-size: 14px;
                max-height: 150px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Extracted Slides Presentation</h1>
            <p>Generated with YouTube Slide Extractor</p>
        </header>
        
        <div class="slide-controls">
            <button id="prevBtn" class="control-btn" onclick="prevSlide()">Previous</button>
            <div class="slide-number">Slide <span id="currentSlide">1</span> of <span id="totalSlides">0</span></div>
            <button id="nextBtn" class="control-btn" onclick="nextSlide()">Next</button>
        </div>
        
        <div class="slide-container">''')
            
            # Add each slide to the HTML
            for i, img_filename in enumerate(slide_filenames):
                active_class = "active" if i == 0 else ""
                slide_number = i + 1
                
                # Get text if available
                slide_text = ""
                if self.extract_text and img_filename in self.extracted_text:
                    slide_text = self.extracted_text[img_filename]
                
                # Create slide HTML
                f.write(f'''
            <div class="slide {active_class}" id="slide-{slide_number}">
                <img src="html_images/{img_filename}" alt="Slide {slide_number}">
                <div class="slide-info">
                    <div class="slide-title">Slide {slide_number}</div>''')
                
                # Add extracted text if available
                if slide_text:
                    f.write(f'''
                    <div class="slide-text">{slide_text}</div>''')
                
                f.write('''
                </div>
            </div>''')
            
            # Write HTML footer with JavaScript for slideshow controls
            f.write(f'''
        </div>
        
        <footer>
            <p>YouTube Slide Extractor &copy; 2025</p>
        </footer>
    </div>

    <script>
        // Slideshow functionality
        let currentSlideIndex = 1;
        const totalSlides = {len(slide_filenames)};
        
        document.getElementById("totalSlides").textContent = totalSlides;
        
        function showSlide(n) {{
            // Hide all slides
            const slides = document.querySelectorAll('.slide');
            slides.forEach(slide => {{
                slide.classList.remove('active');
            }});
            
            // Display the selected slide
            currentSlideIndex = n;
            if (currentSlideIndex > totalSlides) {{
                currentSlideIndex = 1;
            }}
            if (currentSlideIndex < 1) {{
                currentSlideIndex = totalSlides;
            }}
            
            document.getElementById(`slide-${{currentSlideIndex}}`).classList.add('active');
            document.getElementById('currentSlide').textContent = currentSlideIndex;
            
            // Update button states
            document.getElementById('prevBtn').disabled = (currentSlideIndex === 1);
            document.getElementById('nextBtn').disabled = (currentSlideIndex === totalSlides);
        }}
        
        function nextSlide() {{
            showSlide(currentSlideIndex + 1);
        }}
        
        function prevSlide() {{
            showSlide(currentSlideIndex - 1);
        }}
        
        // Initialize slideshow
        showSlide(1);
        
        // Add keyboard navigation
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'ArrowRight') {{
                nextSlide();
            }} else if (event.key === 'ArrowLeft') {{
                prevSlide();
            }}
        }});
    </script>
</body>
</html>''')
        
        print(f"HTML slideshow created at: {html_path}")
        self._update_status(f"HTML slideshow created at: {html_path} with images in html_images folder")
        return html_path

    def _update_status(self, message):
        """
        Update the status with a new message via the status queue
        
        Args:
            message: The status message to send
        """
        if self.batch_mode and self.status_queue:
            self.status_queue.put((self.video_url, message))

def batch_process(urls, output_dir="slides", interval=5, similarity_threshold=0.7, 
                 resolution="highest", extract_text=False, export_format="pdf", 
                 parallel=True, max_workers=3, status_callback=None):
    """
    Process multiple YouTube URLs in batch mode.
    
    Args:
        urls (list): List of YouTube URLs to process
        output_dir (str): Base directory for outputs
        interval (int): Frame interval in seconds
        similarity_threshold (float): Similarity threshold for slide detection
        resolution (str): Video resolution
        extract_text (bool): Whether to extract text from slides
        export_format (str): Export format (pdf, html, images)
        parallel (bool): Whether to process videos in parallel
        max_workers (int): Maximum number of parallel workers
        status_callback (function): Callback function for status updates
        
    Returns:
        dict: Dictionary of results by URL
    """
    results = {}
    
    # Create callback function for status updates
    def update_status(url, message):
        if status_callback:
            status_callback(url, message)
    
    if parallel:
        # Process URLs in parallel
        active_threads = []
        max_active = max_workers
        
        for url in urls:
            # Wait if we've reached max active threads
            while len(active_threads) >= max_active:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.5)
            
            # Create video-specific output directory
            video_id = url.split("?v=")[-1].split("&")[0] if "?v=" in url else url.split("/")[-1]
            video_output_dir = os.path.join(output_dir, f"video_{video_id}")
            os.makedirs(video_output_dir, exist_ok=True)
            
            # Define a thread function for processing a single URL
            def process_url(url, output_dir):
                update_status(url, f"Starting extraction (interval={interval}s, threshold={similarity_threshold})")
                extractor = SlideExtractor(
                    video_url=url,
                    output_dir=output_dir,
                    interval=interval,
                    similarity_threshold=similarity_threshold,
                    resolution=resolution,
                    extract_text=extract_text,
                    export_format=export_format,
                    batch_mode=True
                )
                
                slides = extractor.extract_slides()
                update_status(url, f"Extraction complete. Found {len(slides)} slides.")
                
                # Store results
                results[url] = {
                    'slide_count': len(slides),
                    'output_dir': output_dir
                }
            
            # Create and start a new thread
            thread = threading.Thread(
                target=process_url,
                args=(url, video_output_dir),
                daemon=True
            )
            thread.start()
            active_threads.append(thread)
            
            update_status(url, "Added to processing queue")
        
        # Wait for all threads to complete
        for thread in active_threads:
            thread.join()
    else:
        # Process URLs sequentially
        for url in urls:
            # Create video-specific output directory
            video_id = url.split("?v=")[-1].split("&")[0] if "?v=" in url else url.split("/")[-1]
            video_output_dir = os.path.join(output_dir, f"video_{video_id}")
            os.makedirs(video_output_dir, exist_ok=True)
            
            update_status(url, f"Starting extraction (interval={interval}s, threshold={similarity_threshold})")
            
            extractor = SlideExtractor(
                video_url=url,
                output_dir=video_output_dir,
                interval=interval,
                similarity_threshold=similarity_threshold,
                resolution=resolution,
                extract_text=extract_text,
                export_format=export_format,
                batch_mode=True
            )
            
            slides = extractor.extract_slides()
            update_status(url, f"Extraction complete. Found {len(slides)} slides.")
            
            # Store results
            results[url] = {
                'slide_count': len(slides),
                'output_dir': video_output_dir
            }
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract slides from a YouTube video")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--interval", type=int, default=5, help="Frame interval in seconds")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold (0.0-1.0)")
    parser.add_argument("--resolution", default="highest", help="Video resolution (highest, 360p, 480p, 720p, 1080p)")
    parser.add_argument("--extract-text", action="store_true", help="Extract text from slides using OCR")
    parser.add_argument("--format", default="pdf", choices=["pdf", "html", "images"], help="Export format")
    
    args = parser.parse_args()
    
    extractor = SlideExtractor(
        video_url=args.url,
        interval=args.interval,
        similarity_threshold=args.threshold,
        resolution=args.resolution,
        extract_text=args.extract_text,
        export_format=args.format
    )
    
    slides = extractor.extract_slides()
    print(f"Extracted {len(slides)} slides.")
