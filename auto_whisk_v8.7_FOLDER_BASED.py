"""
Auto Whisk v8.7 - FOLDER BASED SYSTEM
======================================
NEW SYSTEM: No manual upload, uses KARAKTER/, MEKAN/, STIL/ folders
FIXED: No character mixing, no HTTP errors, exact name matching

Author: Enhanced by Claude
License: MIT
Date: 2025-12-23
"""

import sys
import json
import requests
import base64
import os
import time
import re
import queue
import random
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QPlainTextEdit, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QProgressBar, QGroupBox, QSplitter, QCheckBox, QSpinBox, QFrame
)
from PySide6.QtGui import QPixmap, QColor, QDesktopServices, QFont, QIcon
from PySide6.QtCore import Qt, Signal, QThread, QUrl, QTimer

# ==================== CONFIGURATION ====================
APP_VERSION = 'v8.7.0 FOLDER BASED'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
API_AUTH_SESSION = 'https://labs.google/fx/api/auth/session'

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
        return os.path.join(base_path, relative_path)
    except:
        return os.path.abspath(relative_path)

ICON_FILE = resource_path('icon.ico')

APP_NAME = 'AutoWhisk'
if sys.platform == 'win32':
    app_data = os.getenv('APPDATA') or os.path.expanduser('~\\AppData\\Roaming')
elif sys.platform == 'darwin':
    app_data = os.path.expanduser('~/Library/Application Support')
else:
    app_data = os.path.expanduser('~/.local/share')

APP_DIR = os.path.join(app_data, APP_NAME)
os.makedirs(APP_DIR, exist_ok=True)
AUTH_FILE = os.path.join(APP_DIR, 'auth_session.json')

# Folder paths (relative to EXE location)
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
KARAKTER_FOLDER = os.path.join(BASE_DIR, 'KARAKTER')
MEKAN_FOLDER = os.path.join(BASE_DIR, 'MEKAN')
STIL_FOLDER = os.path.join(BASE_DIR, 'STIL')

RATIO_DATA = [
    ('Landscape 16:9', 'IMAGE_ASPECT_RATIO_LANDSCAPE'),
    ('Portrait 9:16', 'IMAGE_ASPECT_RATIO_PORTRAIT'),
    ('Square 1:1', 'IMAGE_ASPECT_RATIO_SQUARE')
]

# ==================== TRANSLATIONS ====================
TRANSLATIONS = {
    'en': {
        'window_title': f'Auto Whisk {APP_VERSION}',
        'grp_auth': 'Account Configuration',
        'lbl_cookie': 'Cookie (JSON):',
        'placeholder_cookie': 'Paste cookie...',
        'btn_check': 'Check & Save',
        'grp_folders': 'Folder Status',
        'grp_config': 'Configuration',
        'lbl_ratio': 'Aspect Ratio:',
        'lbl_count': 'Image Count:',
        'lbl_prompts': 'Prompts (one per line):',
        'placeholder_prompts': 'Enter prompts...',
        'btn_import': 'Import TXT',
        'btn_start': 'START',
        'btn_stop': 'STOP',
        'btn_pause': 'PAUSE',
        'btn_resume': 'RESUME',
        'lbl_output': 'Output:',
        'btn_browse': 'Browse',
        'btn_open': 'Open Folder',
        'chk_auto_open': 'Auto-open when done',
        'alert_no_prompts': 'Enter at least one prompt!',
        'alert_no_token': 'Check and save cookie first!',
        'alert_cookie_valid': 'Token OK!\nExpires: ',
        'alert_cookie_invalid': 'Cookie validation failed!',
        'status_idle': 'Ready',
        'status_running': 'Running...',
        'status_done': '✓ Done',
        'status_error': '✗ Error'
    },
    'tr': {
        'window_title': f'Auto Whisk {APP_VERSION}',
        'grp_auth': 'Hesap Yapılandırması',
        'lbl_cookie': 'Cookie (JSON):',
        'placeholder_cookie': 'Cookie yapıştır...',
        'btn_check': 'Kontrol Et',
        'grp_folders': 'Klasör Durumu',
        'grp_config': 'Yapılandırma',
        'lbl_ratio': 'Oran:',
        'lbl_count': 'Sayı:',
        'lbl_prompts': 'Promptlar:',
        'placeholder_prompts': 'Prompt gir...',
        'btn_import': 'TXT Al',
        'btn_start': 'BAŞLAT',
        'btn_stop': 'DURDUR',
        'btn_pause': 'DURAKLAT',
        'btn_resume': 'DEVAM',
        'lbl_output': 'Çıktı:',
        'btn_browse': 'Gözat',
        'btn_open': 'Klasör Aç',
        'chk_auto_open': 'Bitince otomatik aç',
        'alert_no_prompts': 'Prompt gir!',
        'alert_no_token': 'Cookie kaydet!',
        'alert_cookie_valid': 'Token OK!\n',
        'alert_cookie_invalid': 'Cookie hatalı!',
        'status_idle': 'Hazır',
        'status_running': 'Çalışıyor',
        'status_done': '✓ Tamam',
        'status_error': '✗ Hata'
    }
}

STYLE = '''
QWidget { background: #f4f7f6; font: 13px "Segoe UI"; color: #2c3e50; }
QGroupBox { background: #fff; border-radius: 8px; margin-top: 22px; padding-top: 10px; border: 1px solid #e0e0e0; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 4px 10px; background: #34495e; color: white; border-radius: 8px; font-weight: bold; margin-left: 10px; }
QLineEdit, QPlainTextEdit, QComboBox { border: 1px solid #ccc; border-radius: 4px; padding: 5px; background: #fff; }
QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #3498db; }
QPushButton { border-radius: 5px; padding: 6px 12px; font-weight: bold; color: white; }
QPushButton:disabled { background: #bdc3c7 !important; color: #7f8c8d !important; }
QTableWidget { background: white; border: 1px solid #e0e0e0; border-radius: 4px; gridline-color: #f0f0f0; }
QHeaderView::section { background: #ecf0f1; padding: 6px; border: none; border-bottom: 2px solid #dcdcdc; font-weight: bold; }
'''


# ==================== FOLDER MANAGEMENT ====================

def normalize_turkish(text):
    """Normalize Turkish characters and lowercase"""
    replacements = {
        'ı': 'i', 'İ': 'i', 'I': 'i',
        'ş': 's', 'Ş': 's',
        'ğ': 'g', 'Ğ': 'g',
        'ü': 'u', 'Ü': 'u',
        'ö': 'o', 'Ö': 'o',
        'ç': 'c', 'Ç': 'c'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.lower()

def get_file_base_name(filename):
    """
    Extract clean name from filename
    'Kırmızı_Şapkalı_Kedi.jpg' → 'kirmizi sapkali kedi'
    """
    name = os.path.splitext(filename)[0]  # Remove extension
    name = name.replace('_', ' ')  # Underscores to spaces
    name = normalize_turkish(name)
    return name.strip()

def scan_folder(folder_path):
    """
    Scan folder for image files
    Returns: list of (filename, base_name) tuples
    """
    if not os.path.exists(folder_path):
        return []
    
    files = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            base_name = get_file_base_name(filename)
            files.append((filename, base_name))
    
    return files

def is_exact_match(file_base_name, prompt):
    """
    Check if file base name EXACTLY matches in prompt
    Uses word boundaries and Turkish suffixes
    
    Examples:
        file: "ahmet", prompt: "ahmet parkta" → TRUE
        file: "ahmet", prompt: "ahmetin arabası" → TRUE (suffix)
        file: "park", prompt: "otopark" → FALSE (word boundary)
    """
    prompt_norm = normalize_turkish(prompt)
    file_norm = file_base_name  # Already normalized
    
    # Exact match
    if file_norm in prompt_norm:
        # Check word boundaries
        pattern = r'\b' + re.escape(file_norm) + r'\b'
        if re.search(pattern, prompt_norm):
            return True
    
    # Check Turkish suffixes (possessive, locative, etc.)
    suffixes = [
        'in', 'nin', 'un', 'nun', 'ın', 'nın', 'ün', 'nün',  # Possessive
        'da', 'de', 'ta', 'te', 'nda', 'nde',  # Locative
        'a', 'e', 'na', 'ne', 'ya', 'ye',  # Dative
        'i', 'ı', 'u', 'ü', 'ni', 'nı', 'nu', 'nü',  # Accusative
        'dan', 'den', 'tan', 'ten', 'ndan', 'nden'  # Ablative
    ]
    
    for suffix in suffixes:
        pattern = r'\b' + re.escape(file_norm) + suffix + r'\b'
        if re.search(pattern, prompt_norm):
            return True
    
    return False

def match_files_in_folder(folder_files, prompt):
    """
    Match files from folder against prompt
    Returns: list of matching filenames
    """
    matches = []
    
    for filename, base_name in folder_files:
        if is_exact_match(base_name, prompt):
            matches.append(filename)
            print(f"[MATCH] '{base_name}' → {filename}")
    
    return matches

# ==================== API UTILITIES ====================

def parse_cookie_input(raw):
    """Parse various cookie formats"""
    raw = raw.strip()
    if not raw:
        return ''
    
    # JSON format
    if raw.startswith('[') or raw.startswith('{'):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = [data]
            cookies = [f"{c['name']}={c['value']}" for c in data if 'name' in c and 'value' in c]
            if cookies:
                return '; '.join(cookies)
        except:
            pass
    
    # JWT token
    if raw.startswith('ey'):
        return f'__Secure-next-auth.session-token={raw}'
    
    return raw

def upload_image_to_google(file_path, category, cookie_str, token):
    """
    Upload image to Google Labs
    Returns: (media_id, caption, error)
    """
    if not os.path.exists(file_path):
        return (None, '', 'File not found')
    
    try:
        # Read and encode
        with open(file_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Detect MIME
        ext = os.path.splitext(file_path)[1].lower()
        if '.png' in ext:
            mime = 'image/png'
        elif '.webp' in ext:
            mime = 'image/webp'
        else:
            mime = 'image/jpeg'
        
        data_uri = f'data:{mime};base64,{b64}'
        sess_id = f';{int(datetime.now().timestamp() * 1000)}'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT,
            'Origin': 'https://labs.google',
            'Referer': 'https://labs.google/fx/tools/whisk',
            'Cookie': parse_cookie_input(cookie_str)
        }
        
        # Get caption
        caption = ''
        try:
            r = requests.post(
                'https://labs.google/fx/api/trpc/backbone.captionImage',
                headers=headers,
                json={
                    'json': {
                        'clientContext': {'workflowId': '', 'sessionId': sess_id},
                        'captionInput': {
                            'candidatesCount': 1,
                            'mediaInput': {
                                'mediaCategory': category,
                                'rawBytes': data_uri
                            }
                        }
                    }
                },
                timeout=40
            )
            if r.status_code == 200:
                cands = r.json().get('result', {}).get('data', {}).get('json', {}).get('result', {}).get('candidates', [])
                if cands:
                    caption = cands[0].get('output', '')
        except:
            pass
        
        # Upload
        r = requests.post(
            'https://labs.google/fx/api/trpc/backbone.uploadImage',
            headers=headers,
            json={
                'json': {
                    'clientContext': {'workflowId': '', 'sessionId': sess_id},
                    'uploadMediaInput': {
                        'mediaCategory': category,
                        'rawBytes': data_uri
                    }
                }
            },
            timeout=60
        )
        
        if r.status_code != 200:
            return (None, '', f'HTTP {r.status_code}')
        
        mid = r.json().get('result', {}).get('data', {}).get('json', {}).get('result', {}).get('uploadMediaGenerationId')
        if mid:
            return (mid, caption, None)
        
        return (None, '', 'No media ID')
        
    except Exception as e:
        return (None, '', str(e))


# ==================== WORKERS ====================

class CookieValidatorWorker(QThread):
    """Validate cookie and get access token"""
    result = Signal(bool, str, int)
    
    def __init__(self, cookie_str):
        super().__init__()
        self.cookie_str = cookie_str
    
    def run(self):
        try:
            headers = {
                'Cookie': parse_cookie_input(self.cookie_str),
                'User-Agent': USER_AGENT
            }
            
            r = requests.get(API_AUTH_SESSION, headers=headers, timeout=20)
            
            if r.status_code != 200:
                self.result.emit(False, '', 0)
                return
            
            token = r.json().get('access_token') or r.json().get('accessToken')
            if not token:
                self.result.emit(False, '', 0)
                return
            
            # Get expiry
            try:
                ri = requests.get(f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={token}', timeout=10)
                exp = int(ri.json().get('exp', 0)) if ri.status_code == 200 else 0
                self.result.emit(True, token, exp)
            except:
                self.result.emit(True, token, 0)
                
        except:
            self.result.emit(False, '', 0)


class GenerationWorker(QThread):
    """
    FOLDER-BASED GENERATION WORKER
    - Scans folders for matches per prompt
    - No manual upload needed
    - Guarantees no character mixing
    """
    task_started = Signal(int, str)
    task_success = Signal(int, int, str)
    task_failed = Signal(int, int, str)
    all_done = Signal()
    
    def __init__(self, task_queue, settings, output_dir, num_images, 
                 karakter_files, mekan_files, stil_file, stil_media_id,
                 cookie_str, token):
        super().__init__()
        self.task_queue = task_queue
        self.settings = settings
        self.output_dir = output_dir
        self.num_images = num_images
        self.karakter_files = karakter_files
        self.mekan_files = mekan_files
        self.stil_file = stil_file
        self.stil_media_id = stil_media_id
        self.cookie_str = cookie_str
        self.token = token
        self.running = True
        self.paused = False
        
        # Cache for uploaded media IDs
        self.media_cache = {}
    
    def upload_if_needed(self, file_path, category):
        """Upload file if not cached, return media_id"""
        if file_path in self.media_cache:
            return self.media_cache[file_path]
        
        mid, cap, err = upload_image_to_google(file_path, category, self.cookie_str, self.token)
        
        if mid:
            self.media_cache[file_path] = mid
            print(f"[UPLOAD] {os.path.basename(file_path)} → {mid[:12]}...")
            return mid
        else:
            raise Exception(f"Upload failed: {err}")
    
    def run(self):
        while self.running:
            while self.paused and self.running:
                time.sleep(0.5)
            
            try:
                item = self.task_queue.get(timeout=1)
                row_idx, prompt = item if len(item) == 2 else (item[0], item[1])
                indices = range(self.num_images) if len(item) == 2 else item[2]
            except queue.Empty:
                continue
            
            print(f"\n{'='*60}")
            print(f"[PROMPT {row_idx+1}] {prompt[:50]}...")
            
            # === MATCH FILES FOR THIS PROMPT ===
            karakter_matches = match_files_in_folder(self.karakter_files, prompt)
            mekan_matches = match_files_in_folder(self.mekan_files, prompt)
            
            # Limit to 1 scene
            if len(mekan_matches) > 1:
                print(f"[INFO] Multiple scenes matched, using first: {mekan_matches[0]}")
                mekan_matches = mekan_matches[:1]
            
            if not karakter_matches:
                print("[INFO] No character matches")
            if not mekan_matches:
                print("[INFO] No scene matches")
            
            # === PREPARE REFERENCES ===
            refs = []
            
            try:
                # Characters
                for filename in karakter_matches:
                    file_path = os.path.join(KARAKTER_FOLDER, filename)
                    mid = self.upload_if_needed(file_path, 'MEDIA_CATEGORY_SUBJECT')
                    refs.append({
                        'caption': get_file_base_name(filename),
                        'mediaInput': {
                            'mediaCategory': 'MEDIA_CATEGORY_SUBJECT',
                            'mediaGenerationId': mid
                        }
                    })
                
                # Scenes
                for filename in mekan_matches:
                    file_path = os.path.join(MEKAN_FOLDER, filename)
                    mid = self.upload_if_needed(file_path, 'MEDIA_CATEGORY_SCENE')
                    refs.append({
                        'caption': get_file_base_name(filename),
                        'mediaInput': {
                            'mediaCategory': 'MEDIA_CATEGORY_SCENE',
                            'mediaGenerationId': mid
                        }
                    })
                
                # Style (always included if exists)
                if self.stil_media_id:
                    refs.append({
                        'caption': get_file_base_name(self.stil_file) if self.stil_file else '',
                        'mediaInput': {
                            'mediaCategory': 'MEDIA_CATEGORY_STYLE',
                            'mediaGenerationId': self.stil_media_id
                        }
                    })
                    print(f"[INFO] Style: {self.stil_file}")
                
            except Exception as e:
                print(f"[ERROR] Reference preparation: {str(e)}")
                self.task_failed.emit(row_idx, 0, str(e)[:30])
                self.task_queue.task_done()
                continue
            
            print(f"[REFS] Total: {len(refs)} references prepared")
            print(f"{'='*60}\n")
            
            # === GENERATE IMAGES ===
            for i in indices:
                if not self.running:
                    break
                
                while self.paused and self.running:
                    time.sleep(0.5)
                
                col_idx = i + 1
                self.task_started.emit(row_idx, f'{i+1}/{self.num_images}')
                
                try:
                    sess_id = f';{int(datetime.now().timestamp() * 1000)}'
                    
                    headers = {
                        'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json',
                        'User-Agent': USER_AGENT,
                        'Origin': 'https://labs.google',
                        'Referer': 'https://labs.google/fx/tools/whisk',
                        'Cookie': parse_cookie_input(self.cookie_str)
                    }
                    
                    seed = random.randint(1, 2147483647)
                    
                    if refs:
                        url = 'https://aisandbox-pa.googleapis.com/v1/whisk:runImageRecipe'
                        settings = self.settings.copy()
                        settings['imageModel'] = 'GEM_PIX' if len(refs) == 1 else 'R2I'
                        
                        payload = {
                            'clientContext': {'workflowId': '', 'tool': 'BACKBONE', 'sessionId': sess_id},
                            'imageModelSettings': settings,
                            'userInstruction': prompt,
                            'recipeMediaInputs': refs,
                            'seed': seed
                        }
                    else:
                        url = 'https://aisandbox-pa.googleapis.com/v1/whisk:generateImage'
                        
                        payload = {
                            'clientContext': {'workflowId': '', 'tool': 'BACKBONE', 'sessionId': sess_id},
                            'imageModelSettings': self.settings,
                            'prompt': prompt,
                            'mediaCategory': 'MEDIA_CATEGORY_BOARD',
                            'seed': seed
                        }
                    
                    r = requests.post(url, headers=headers, json=payload, timeout=60)
                    
                    if not self.running:
                        self.task_queue.task_done()
                        break
                    
                    if r.status_code == 200:
                        panels = r.json().get('imagePanels', [])
                        if panels and panels[0].get('generatedImages'):
                            b64 = panels[0]['generatedImages'][0].get('encodedImage', '')
                            
                            safe_prompt = re.sub(r'[^\w\s-]', '', prompt).strip().replace(' ', '_')[:40]
                            filename = f"{row_idx+1}_{safe_prompt}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}.jpg"
                            filepath = os.path.join(self.output_dir, filename)
                            
                            with open(filepath, 'wb') as f:
                                f.write(base64.b64decode(b64))
                            
                            self.task_success.emit(row_idx, col_idx, filepath)
                        else:
                            self.task_failed.emit(row_idx, col_idx, 'No image data')
                    else:
                        self.task_failed.emit(row_idx, col_idx, f'HTTP {r.status_code}')
                        
                except Exception as e:
                    self.task_failed.emit(row_idx, col_idx, str(e)[:30])
                
                time.sleep(2)
            
            self.task_queue.task_done()
            time.sleep(1)
        
        self.all_done.emit()
    
    def stop(self):
        self.running = False
    
    def pause(self):
        self.paused = True
    
    def resume(self):
        self.paused = False


# ==================== CUSTOM WIDGETS ====================

class ImageCellWidget(QWidget):
    """Display generated image in table cell"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.lbl = QLabel()
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet('border: 1px solid #ddd; background: #f9f9f9;')
        layout.addWidget(self.lbl)
    
    def set_image(self, path):
        pix = QPixmap(path)
        if not pix.isNull():
            self.lbl.setPixmap(pix.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))


class PromptCellWidget(QWidget):
    """Editable prompt cell"""
    def __init__(self, text=''):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.txt = QPlainTextEdit()
        self.txt.setPlainText(text)
        self.txt.setStyleSheet('border: 1px solid #ddd; font-size: 12px;')
        layout.addWidget(self.txt)
    
    def get_text(self):
        return self.txt.toPlainText().strip()


class StatusCellWidget(QWidget):
    """Status cell with retry/folder buttons"""
    retry_requested = Signal(int)
    open_folder_requested = Signal(int)
    
    def __init__(self, row_idx, lang='en'):
        super().__init__()
        self.row_idx = row_idx
        self.lang = lang
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        self.lbl = QLabel(TRANSLATIONS[lang]['status_idle'])
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet('font-weight: bold; padding: 4px;')
        layout.addWidget(self.lbl)
        
        btn_layout = QHBoxLayout()
        
        self.btn_retry = QPushButton('🔄')
        self.btn_retry.setFixedSize(30, 25)
        self.btn_retry.setStyleSheet('background: #3498db;')
        self.btn_retry.clicked.connect(lambda: self.retry_requested.emit(self.row_idx))
        self.btn_retry.setVisible(False)
        
        self.btn_folder = QPushButton('📁')
        self.btn_folder.setFixedSize(30, 25)
        self.btn_folder.setStyleSheet('background: #2ecc71;')
        self.btn_folder.clicked.connect(lambda: self.open_folder_requested.emit(self.row_idx))
        self.btn_folder.setVisible(False)
        
        btn_layout.addWidget(self.btn_retry)
        btn_layout.addWidget(self.btn_folder)
        layout.addLayout(btn_layout)
    
    def set_status(self, key):
        self.lbl.setText(TRANSLATIONS[self.lang][key])
        
        if key == 'status_error':
            self.lbl.setStyleSheet('color: #e74c3c; font-weight: bold; padding: 4px;')
            self.btn_retry.setVisible(True)
        elif key == 'status_done':
            self.lbl.setStyleSheet('color: #27ae60; font-weight: bold; padding: 4px;')
            self.btn_folder.setVisible(True)
        elif key == 'status_running':
            self.lbl.setStyleSheet('color: #3498db; font-weight: bold; padding: 4px;')
        else:
            self.lbl.setStyleSheet('font-weight: bold; padding: 4px;')


# ==================== MAIN WINDOW ====================

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_lang = 'tr'  # Default Turkish
        self.access_token = ''
        self.cookie_str = ''
        self.worker = None
        self.task_queue = queue.Queue()
        
        # Folder data
        self.karakter_files = []
        self.mekan_files = []
        self.stil_file = None
        self.stil_media_id = None
        
        self.init_ui()
        self.load_auth()
        self.scan_folders()
    
    def init_ui(self):
        self.setWindowTitle(TRANSLATIONS[self.current_lang]['window_title'])
        self.setMinimumSize(1200, 800)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === AUTHENTICATION GROUP ===
        auth_group = QGroupBox(TRANSLATIONS[self.current_lang]['grp_auth'])
        auth_layout = QVBoxLayout(auth_group)
        
        cookie_layout = QHBoxLayout()
        cookie_layout.addWidget(QLabel(TRANSLATIONS[self.current_lang]['lbl_cookie']))
        
        self.txt_cookie = QPlainTextEdit()
        self.txt_cookie.setPlaceholderText(TRANSLATIONS[self.current_lang]['placeholder_cookie'])
        self.txt_cookie.setMaximumHeight(80)
        cookie_layout.addWidget(self.txt_cookie)
        
        self.btn_check = QPushButton(TRANSLATIONS[self.current_lang]['btn_check'])
        self.btn_check.setStyleSheet('background: #3498db; min-width: 120px;')
        self.btn_check.clicked.connect(self.check_cookie)
        cookie_layout.addWidget(self.btn_check)
        
        auth_layout.addLayout(cookie_layout)
        main_layout.addWidget(auth_group)
        
        # === FOLDER STATUS GROUP ===
        folder_group = QGroupBox(TRANSLATIONS[self.current_lang]['grp_folders'])
        folder_layout = QVBoxLayout(folder_group)
        
        self.lbl_karakter_status = QLabel()
        self.lbl_mekan_status = QLabel()
        self.lbl_stil_status = QLabel()
        
        folder_layout.addWidget(self.lbl_karakter_status)
        folder_layout.addWidget(self.lbl_mekan_status)
        folder_layout.addWidget(self.lbl_stil_status)
        
        main_layout.addWidget(folder_group)
        
        # === CONFIGURATION GROUP ===
        config_group = QGroupBox(TRANSLATIONS[self.current_lang]['grp_config'])
        config_layout = QVBoxLayout(config_group)
        
        # Ratio & Count
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel(TRANSLATIONS[self.current_lang]['lbl_ratio']))
        self.combo_ratio = QComboBox()
        for name, _ in RATIO_DATA:
            self.combo_ratio.addItem(name)
        settings_layout.addWidget(self.combo_ratio)
        
        settings_layout.addWidget(QLabel(TRANSLATIONS[self.current_lang]['lbl_count']))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 20)
        self.spin_count.setValue(4)
        settings_layout.addWidget(self.spin_count)
        
        settings_layout.addStretch()
        config_layout.addLayout(settings_layout)
        
        # Prompts
        config_layout.addWidget(QLabel(TRANSLATIONS[self.current_lang]['lbl_prompts']))
        
        self.txt_prompts = QPlainTextEdit()
        self.txt_prompts.setPlaceholderText(TRANSLATIONS[self.current_lang]['placeholder_prompts'])
        self.txt_prompts.setMinimumHeight(150)
        config_layout.addWidget(self.txt_prompts)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_import = QPushButton(TRANSLATIONS[self.current_lang]['btn_import'])
        self.btn_import.setStyleSheet('background: #95a5a6;')
        self.btn_import.clicked.connect(self.import_prompts)
        btn_layout.addWidget(self.btn_import)
        
        btn_layout.addStretch()
        
        self.btn_start = QPushButton(TRANSLATIONS[self.current_lang]['btn_start'])
        self.btn_start.setStyleSheet('background: #27ae60; min-width: 100px; font-size: 14px;')
        self.btn_start.clicked.connect(self.start_generation)
        btn_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton(TRANSLATIONS[self.current_lang]['btn_stop'])
        self.btn_stop.setStyleSheet('background: #e74c3c; min-width: 100px; font-size: 14px;')
        self.btn_stop.clicked.connect(self.stop_generation)
        self.btn_stop.setEnabled(False)
        btn_layout.addWidget(self.btn_stop)
        
        self.btn_pause = QPushButton(TRANSLATIONS[self.current_lang]['btn_pause'])
        self.btn_pause.setStyleSheet('background: #f39c12; min-width: 100px;')
        self.btn_pause.clicked.connect(self.pause_generation)
        self.btn_pause.setEnabled(False)
        btn_layout.addWidget(self.btn_pause)
        
        self.btn_resume = QPushButton(TRANSLATIONS[self.current_lang]['btn_resume'])
        self.btn_resume.setStyleSheet('background: #16a085; min-width: 100px;')
        self.btn_resume.clicked.connect(self.resume_generation)
        self.btn_resume.setEnabled(False)
        self.btn_resume.setVisible(False)
        btn_layout.addWidget(self.btn_resume)
        
        config_layout.addLayout(btn_layout)
        
        # Output folder
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel(TRANSLATIONS[self.current_lang]['lbl_output']))
        
        self.txt_output = QLineEdit()
        self.txt_output.setText(os.path.join(os.path.expanduser('~'), 'Desktop', 'AutoWhisk_Output'))
        output_layout.addWidget(self.txt_output)
        
        self.btn_browse = QPushButton(TRANSLATIONS[self.current_lang]['btn_browse'])
        self.btn_browse.setStyleSheet('background: #7f8c8d;')
        self.btn_browse.clicked.connect(self.browse_output)
        output_layout.addWidget(self.btn_browse)
        
        self.btn_open_folder = QPushButton(TRANSLATIONS[self.current_lang]['btn_open'])
        self.btn_open_folder.setStyleSheet('background: #2ecc71;')
        self.btn_open_folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.txt_output.text())))
        output_layout.addWidget(self.btn_open_folder)
        
        config_layout.addLayout(output_layout)
        
        self.chk_auto_open = QCheckBox(TRANSLATIONS[self.current_lang]['chk_auto_open'])
        config_layout.addWidget(self.chk_auto_open)
        
        main_layout.addWidget(config_group)
        
        # === PROGRESS TABLE ===
        self.table = QTableWidget()
        self.table.setColumnCount(self.spin_count.value() + 2)
        self.table.setHorizontalHeaderLabels(['Prompt'] + [f'#{i+1}' for i in range(self.spin_count.value())] + ['Status'])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setMinimumHeight(250)
        
        main_layout.addWidget(self.table)
        
        # Progress bar
        self.progress = QProgressBar()
        main_layout.addWidget(self.progress)
        
        # Connect spin count change
        self.spin_count.valueChanged.connect(self.update_table_columns)
    
    def scan_folders(self):
        """Scan KARAKTER, MEKAN, STIL folders"""
        # Scan KARAKTER
        self.karakter_files = scan_folder(KARAKTER_FOLDER)
        if os.path.exists(KARAKTER_FOLDER):
            self.lbl_karakter_status.setText(f"✅ KARAKTER/ → {len(self.karakter_files)} files found")
            self.lbl_karakter_status.setStyleSheet('color: #27ae60; font-weight: bold;')
        else:
            self.lbl_karakter_status.setText(f"⚠️ KARAKTER/ → Folder not found (will skip)")
            self.lbl_karakter_status.setStyleSheet('color: #f39c12; font-weight: bold;')
        
        # Scan MEKAN
        self.mekan_files = scan_folder(MEKAN_FOLDER)
        if os.path.exists(MEKAN_FOLDER):
            self.lbl_mekan_status.setText(f"✅ MEKAN/ → {len(self.mekan_files)} files found")
            self.lbl_mekan_status.setStyleSheet('color: #27ae60; font-weight: bold;')
        else:
            self.lbl_mekan_status.setText(f"⚠️ MEKAN/ → Folder not found (will skip)")
            self.lbl_mekan_status.setStyleSheet('color: #f39c12; font-weight: bold;')
        
        # Scan STIL
        stil_files = scan_folder(STIL_FOLDER)
        if stil_files:
            self.stil_file = stil_files[0][0]  # First file
            self.lbl_stil_status.setText(f"✅ STIL/ → {self.stil_file}")
            self.lbl_stil_status.setStyleSheet('color: #27ae60; font-weight: bold;')
            
            # Upload style immediately if we have token
            if self.access_token:
                self.upload_style()
        else:
            if os.path.exists(STIL_FOLDER):
                self.lbl_stil_status.setText(f"⚠️ STIL/ → No files (will skip)")
            else:
                self.lbl_stil_status.setText(f"⚠️ STIL/ → Folder not found (will skip)")
            self.lbl_stil_status.setStyleSheet('color: #f39c12; font-weight: bold;')
    
    def upload_style(self):
        """Upload style file immediately"""
        if not self.stil_file or not self.access_token:
            return
        
        stil_path = os.path.join(STIL_FOLDER, self.stil_file)
        print(f"[STYLE] Uploading: {self.stil_file}...")
        
        mid, cap, err = upload_image_to_google(stil_path, 'MEDIA_CATEGORY_STYLE', self.cookie_str, self.access_token)
        
        if mid:
            self.stil_media_id = mid
            print(f"[STYLE] ✅ Uploaded: {mid[:12]}...")
            self.lbl_stil_status.setText(f"✅ STIL/ → {self.stil_file} (uploaded)")
        else:
            print(f"[STYLE] ❌ Upload failed: {err}")
            self.lbl_stil_status.setText(f"❌ STIL/ → Upload failed: {err}")
            self.lbl_stil_status.setStyleSheet('color: #e74c3c; font-weight: bold;')

    
    def load_auth(self):
        """Load saved authentication"""
        if os.path.exists(AUTH_FILE):
            try:
                with open(AUTH_FILE, 'r') as f:
                    data = json.load(f)
                    self.txt_cookie.setPlainText(data.get('cookie', ''))
                    self.access_token = data.get('token', '')
            except:
                pass
    
    def save_auth(self):
        """Save authentication"""
        try:
            with open(AUTH_FILE, 'w') as f:
                json.dump({
                    'cookie': self.cookie_str,
                    'token': self.access_token
                }, f)
        except:
            pass
    
    def check_cookie(self):
        """Validate cookie and get token"""
        cookie_text = self.txt_cookie.toPlainText().strip()
        
        if not cookie_text:
            QMessageBox.warning(self, 'Error', 'Please enter cookie!')
            return
        
        self.cookie_str = cookie_text
        self.btn_check.setEnabled(False)
        self.btn_check.setText('Checking...')
        
        self.cookie_worker = CookieValidatorWorker(cookie_text)
        self.cookie_worker.result.connect(self.on_cookie_checked)
        self.cookie_worker.start()
    
    def on_cookie_checked(self, success, token, exp):
        """Handle cookie validation result"""
        self.btn_check.setEnabled(True)
        self.btn_check.setText(TRANSLATIONS[self.current_lang]['btn_check'])
        
        if success:
            self.access_token = token
            self.save_auth()
            
            exp_date = datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M') if exp else 'Unknown'
            QMessageBox.information(self, 'Success', 
                TRANSLATIONS[self.current_lang]['alert_cookie_valid'] + exp_date)
            
            # Upload style if available
            if self.stil_file:
                self.upload_style()
        else:
            QMessageBox.critical(self, 'Error', 
                TRANSLATIONS[self.current_lang]['alert_cookie_invalid'])
    
    def import_prompts(self):
        """Import prompts from TXT file"""
        file_path, _ = QFileDialog.getOpenFileName(self, 'Import Prompts', '', 'Text Files (*.txt)')
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    prompts = f.read()
                    self.txt_prompts.setPlainText(prompts)
            except:
                QMessageBox.warning(self, 'Error', 'Failed to read file!')
    
    def browse_output(self):
        """Browse output folder"""
        folder = QFileDialog.getExistingDirectory(self, 'Select Output Folder')
        if folder:
            self.txt_output.setText(folder)
    
    def update_table_columns(self):
        """Update table columns when count changes"""
        count = self.spin_count.value()
        self.table.setColumnCount(count + 2)
        self.table.setHorizontalHeaderLabels(['Prompt'] + [f'#{i+1}' for i in range(count)] + ['Status'])
    
    def start_generation(self):
        """Start image generation"""
        # Validate
        prompts_text = self.txt_prompts.toPlainText().strip()
        if not prompts_text:
            QMessageBox.warning(self, 'Error', TRANSLATIONS[self.current_lang]['alert_no_prompts'])
            return
        
        if not self.access_token:
            QMessageBox.warning(self, 'Error', TRANSLATIONS[self.current_lang]['alert_no_token'])
            return
        
        # Parse prompts
        prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]
        
        # Create output folder
        output_dir = self.txt_output.text()
        os.makedirs(output_dir, exist_ok=True)
        
        # Setup table
        self.table.setRowCount(len(prompts))
        count = self.spin_count.value()
        
        for row, prompt in enumerate(prompts):
            # Prompt cell
            prompt_widget = PromptCellWidget(prompt)
            self.table.setCellWidget(row, 0, prompt_widget)
            self.table.setRowHeight(row, 100)
            
            # Image cells
            for col in range(count):
                cell = ImageCellWidget()
                self.table.setCellWidget(row, col + 1, cell)
            
            # Status cell
            status_widget = StatusCellWidget(row, self.current_lang)
            status_widget.retry_requested.connect(self.retry_row)
            status_widget.open_folder_requested.connect(lambda r=row: QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir)))
            self.table.setCellWidget(row, count + 1, status_widget)
            
            # Queue task
            self.task_queue.put((row, prompt))
        
        # Setup progress
        self.progress.setMaximum(len(prompts) * count)
        self.progress.setValue(0)
        
        # Get model settings
        ratio_idx = self.combo_ratio.currentIndex()
        ratio_api = RATIO_DATA[ratio_idx][1]
        
        settings = {
            'imageAspectRatio': ratio_api,
            'imageModel': 'R2I'
        }
        
        # Start worker
        self.worker = GenerationWorker(
            self.task_queue,
            settings,
            output_dir,
            count,
            self.karakter_files,
            self.mekan_files,
            self.stil_file,
            self.stil_media_id,
            self.cookie_str,
            self.access_token
        )
        
        self.worker.task_started.connect(self.on_task_started)
        self.worker.task_success.connect(self.on_task_success)
        self.worker.task_failed.connect(self.on_task_failed)
        self.worker.all_done.connect(self.on_all_done)
        
        self.worker.start()
        
        # Update UI
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
    
    def stop_generation(self):
        """Stop generation"""
        if self.worker:
            self.worker.stop()
            
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_resume.setVisible(False)
    
    def pause_generation(self):
        """Pause generation"""
        if self.worker:
            self.worker.pause()
            
        self.btn_pause.setVisible(False)
        self.btn_resume.setVisible(True)
        self.btn_resume.setEnabled(True)
    
    def resume_generation(self):
        """Resume generation"""
        if self.worker:
            self.worker.resume()
            
        self.btn_pause.setVisible(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setVisible(False)
    
    def retry_row(self, row_idx):
        """Retry failed row"""
        prompt_widget = self.table.cellWidget(row_idx, 0)
        if prompt_widget:
            prompt = prompt_widget.get_text()
            self.task_queue.put((row_idx, prompt))
            
            # Reset status
            status_widget = self.table.cellWidget(row_idx, self.spin_count.value() + 1)
            if status_widget:
                status_widget.set_status('status_idle')
    
    def on_task_started(self, row_idx, progress_text):
        """Handle task started"""
        status_widget = self.table.cellWidget(row_idx, self.spin_count.value() + 1)
        if status_widget:
            status_widget.lbl.setText(progress_text)
            status_widget.set_status('status_running')
    
    def on_task_success(self, row_idx, col_idx, image_path):
        """Handle task success"""
        cell_widget = self.table.cellWidget(row_idx, col_idx)
        if cell_widget:
            cell_widget.set_image(image_path)
        
        self.progress.setValue(self.progress.value() + 1)
        
        # Check if row is done
        count = self.spin_count.value()
        all_done = True
        for c in range(1, count + 1):
            widget = self.table.cellWidget(row_idx, c)
            if widget and not widget.lbl.pixmap():
                all_done = False
                break
        
        if all_done:
            status_widget = self.table.cellWidget(row_idx, count + 1)
            if status_widget:
                status_widget.set_status('status_done')
    
    def on_task_failed(self, row_idx, col_idx, error_msg):
        """Handle task failure"""
        self.progress.setValue(self.progress.value() + 1)
        
        # Set status to error
        status_widget = self.table.cellWidget(row_idx, self.spin_count.value() + 1)
        if status_widget:
            status_widget.lbl.setText(error_msg)
            status_widget.set_status('status_error')
    
    def on_all_done(self):
        """Handle all tasks done"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_resume.setVisible(False)
        
        if self.chk_auto_open.isChecked():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.txt_output.text()))
        
        QMessageBox.information(self, 'Done', 'All tasks completed!')


# ==================== MAIN ENTRY POINT ====================

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    
    if os.path.exists(ICON_FILE):
        app.setWindowIcon(QIcon(ICON_FILE))
    
    # Create folders if they don't exist
    for folder in [KARAKTER_FOLDER, MEKAN_FOLDER, STIL_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[INIT] Created folder: {folder}")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

