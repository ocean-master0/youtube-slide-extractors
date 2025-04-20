# YouTube Slide Extractors 📊 🎓

## A powerful tool to extract slides from educational videos with ease!

![YouTube Slide Extctor Screenshot

## 📋 Table of Contents
- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration Options](#configuration-options)
- [Author](#author)
- [License](#license)

## ✨ Features

- 🎯 **Extract Slides from YouTube Videos** - Automatically identify and extract slides from educational videos
- 📦 **Multiple Export Formats** - Save slides as PDF, HTML slideshow, or individual images
- 🔍 **OCR Text Extraction** - Extract text from slides to create searchable PDFs
- 🎛️ **Customizable Parameters** - Adjust frame interval and similarity threshold for optimal extraction
- 📱 **Resolution Control** - Choose video quality from 360p to 1080p
- 📚 **Batch Processing** - Process multiple videos in one go
- ⚡ **Parallel Processing** - Extract from multiple videos simultaneously
- 📁 **Organized Output** - Neatly organized output folders for each processed video

## 📸 Screenshots


![Single Video Mode](assets/images/single Mode](assets/images/batch-mode.png](assets/images/extracted-slides.png

- Python 3.7 or higher
- Tesseract OCR Engine (for text extraction)

## 📥 Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/ocean-master0/youtube-slide-extractors.git
cd youtube-slide-extractors
```

### Step 2: Install required Python packages

```bash
pip install -r requirements.txt
```

### Step 3: Install Tesseract OCR Engine

#### Windows:
1. Download and install Tesseract from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Add Tesseract to your PATH environment variable

#### macOS:
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install tesseract-ocr
```

### Step 4: Verify installation

```bash
python main.py
```

## 📝 Usage

### Single Video Mode

1. Launch the application: `python main.py`
2. Enter a YouTube URL in the "YouTube URL" field
3. Adjust parameters as needed:
   - Frame Interval: How often to check for new slides (in seconds)
   - Similarity Threshold: How different frames need to be to count as new slides (0.0-1.0)
   - Video Resolution: Quality of the downloaded video
4. Select your preferred export format (PDF, HTML, or Images)
5. Click "Extract Slides" and wait for processing to complete
6. Use "Open Output Folder" to view the extracted slides

### Batch Processing Mode

1. Switch to the "Batch Processing" tab
2. Add multiple YouTube URLs using the input field and "Add URL" button
3. Configure batch settings (similar to single video mode)
4. Enable/disable parallel processing as needed
5. Click "Start Batch Processing"
6. Monitor progress in the batch log
7. Access all extracted slides in the output folder

## ⚙️ Configuration Options

### Frame Interval
- Lower values (1-2 seconds) catch more slides but take longer to process
- Higher values (5+ seconds) are faster but might miss some slides

### Similarity Threshold
- Lower values (0.7) detect more slides, including slightly different ones
- Higher values (0.9) only detect significantly different slides

### Resolution
- Higher resolutions provide better quality slides but take longer to download
- Recommended: 720p for a good balance of quality and speed

### Export Formats
- **PDF**: Creates a single document with all slides
- **HTML**: Creates an interactive slideshow viewable in any browser
- **Images Only**: Saves each slide as a separate PNG file

## 👤 Author


**Name**: Abhishek Kumar   
**GitHub**: [ocean-master0](https://github.com/ocean-master0)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

```
MIT License

Copyright (c) 2025 YouTube Slide Extractor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
