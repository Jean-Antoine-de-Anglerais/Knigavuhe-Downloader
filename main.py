import sys
import requests
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, QProgressBar, QApplication
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal, QThread
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import re
import os
from pathlib import Path

def get_default_download_path():
    # Возвращает кроссплатформенный путь к папке /Music/Audiobooks/
    return Path.home() / "Music" / "Audiobooks"

def get_page(url: str):
    # Получаем страницу с аудиокнигой
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    cookies = {
        "new_design": "1" # Необходимо, чтобы загружался именно новый дизайн сайта
    }

    book_page = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(book_page.content, 'lxml')

    return soup

def get_json_data(soup: BeautifulSoup):
    # Ищем все теги <script>
    scripts = soup.find_all('script')

    # Перебираем теги <script> и ищем тот, который содержит 'BookController.enter'
    target_script = None
    for script in scripts:
        if script.string and "BookController.enter" in script.string:
            target_script = script
            break

    match = re.search(r'BookController\.enter\((\{.*?\})\);', target_script.string)
    if match:
        json_data = json.loads(match.group(1))  # Превращаем в Python-объект
        # print(json.dumps(json_data, indent=4, ensure_ascii=False))  # Красивый вывод

    return json_data

def get_name_and_authors_and_readers(json_data: dict):
    # Получаем название, имена авторов и имена чтецов
    name = json_data["book"]["name"]
    authors = []
    readers = []

    for author_id in json_data["book"]["author_ids"]:
        authors.append(json_data["book"]["authors"][str(author_id)]["name"])

    for reader_id in json_data["book"]["reader_ids"]:
        readers.append(json_data["book"]["readers"][str(reader_id)]["name"])

    if len(authors) == 0:
        authors.append("неизвестен")

    if len(readers) == 0:
        readers.append("неизвестен")
        
    return name, authors, readers

def get_titles_and_links(json_data: dict):
    # Получаем названия глав и ссылки на них
    titles = []
    links = []

    for chapter in json_data["playlist"]:
        titles.append(chapter["title"])
        links.append(chapter["url"])

    return dict(zip(titles, links))

def download(data: dict, path: str, name: str, progress_callback):
    # Скачиваем аудиокнигу
    if not os.path.exists(path):
        os.makedirs(path)

    total_size = 0
    downloaded_size = 0

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    # Считаем общий размер всех файлов
    for link in data.values():
        try:
            response = requests.head(link)
            if "Content-Length" in response.headers:
                total_size += int(response.headers["Content-Length"])
        except Exception as e:
            print(f"Не удалось получить размер файла: {e}")

    if total_size == 0:
        print("Не удалось определить общий размер загрузки.")
        total_size = len(data)  # Если размер файлов неизвестен, считаем их равными

    # Начинаем загрузку
    for title, link in data.items():
        try:
            response = session.get(link, stream=True, allow_redirects=True)
            file_size = int(response.headers.get("Content-Length", 1))

            with open(os.path.join(path, title + ".mp3"), "wb") as f:
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Обновляем прогресс плавно
                        progress_callback.emit(int(downloaded_size / total_size * 100))

        except Exception as e:
        #     if os.path.exists(os.path.join(path, title + ".mp3")):
        #         os.remove(os.path.join(path, title + ".mp3"))
            print(f"Ошибка при загрузке файла {title}: {e}")

        if os.path.exists(os.path.join(path, title + ".mp3")):
            actual_size = os.path.getsize(os.path.join(path, title + ".mp3"))
            if actual_size != file_size:
                print(f"Файл {title} загружен не полностью. Удаление...")
                os.remove(os.path.join(path, title + ".mp3"))


class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()  # Новый сигнал для завершения загрузки

    def __init__(self, data, path, name):
        super().__init__()
        self.data = data
        self.path = path
        self.name = name

    def run(self):
        download(self.data, self.path, self.name, self.progress_signal)
        self.finished_signal.emit()  # Отправляем сигнал о завершении
                
class MainWindow(QWidget):
    progress_signal = pyqtSignal(int)  # Сигнал для обновления прогресс-бара
    def __init__(self):
        
        super().__init__()
        self.url = ""
        self.folder = str(get_default_download_path())  # Используем кроссплатформенный путь
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Knigavuhe Downloader")
        self.resize(500, 450)
        self.setWindowIcon(QIcon(ICON_PATH))  # Добавление иконки приложения

        # Стиль для тёмной темы
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
                color: #f0f0f0;
            }
            QLabel {
                color: #f0f0f0;
                margin-bottom: 4px;
            }
            QLineEdit, QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #f0f0f0;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #66afe9;
            }
            QPushButton {
                background-color: #007BFF;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QProgressBar {
                border: 1px solid #555555;
                background: #3c3c3c;
                border-radius: 4px;
                text-align: center;
                color: #f0f0f0;
            }
            QProgressBar::chunk {
                background: #007BFF;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Поле для ввода URL
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставьте сюда ссылку на аудиокнигу...")
        layout.addWidget(url_label)
        layout.addWidget(self.url_input)

        # Поле для ввода папки сохранения + кнопка выбора
        folder_label = QLabel("Папка с аудиокнигами:")
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText(f"По умолчанию: {self.folder}")
        self.folder_button = QPushButton("📂")
        self.folder_button.setFixedWidth(40)
        self.folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_button)
        layout.addWidget(folder_label)
        layout.addLayout(folder_layout)

        # Кнопка загрузки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.button = QPushButton("⏬ Начать загрузку")
        self.button.setFixedWidth(180)
        self.button.clicked.connect(self.start_downloading)
        button_layout.addWidget(self.button)
        layout.addLayout(button_layout)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_signal.connect(self.progress_bar.setValue)
        layout.addWidget(self.progress_bar)

        # Область консоли
        console_label = QLabel("Консоль:")
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        layout.addWidget(console_label)
        layout.addWidget(self.console_output)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.folder_input.setText(folder)

    def start_downloading(self):
        self.url = self.url_input.text()
        if self.folder_input.text():
            self.folder = self.folder_input.text()
        
        self.progress_bar.setValue(0)  # Сброс прогресс-бара

        if not self.url:
            self.console_output.append("Пожалуйста, введите URL.")
            return

        if not self.url.startswith("https://m."):
            self.url = self.url.replace("https://", "https://m.", 1)

        if not self.url.startswith("https://m.knigavuhe.org/book/"):
            self.console_output.append("Неверный URL. Пожалуйста, проверьте точность введённого URL.")
            return

        self.console_output.append("Запуск загрузки...")

        page = get_page(self.url)
        json_data = get_json_data(page)
        name, authors, readers = get_name_and_authors_and_readers(json_data)
        self.console_output.append(f"Название - {name}, {'автор' if len(authors) == 1 else 'авторы'} - {', '.join(authors)}, {'чтецы' if len(readers) > 1 or readers[0] == 'артисты театров' else 'чтец'} - {', '.join(readers)}")
        titles_and_links = get_titles_and_links(json_data)

        self.folder = os.path.join(self.folder, ", ".join(authors), name, ', '.join(readers))

        # Запускаем загрузку в отдельном потоке
        self.thread = DownloadThread(titles_and_links, self.folder, name)
        self.thread.progress_signal.connect(self.progress_bar.setValue)
        self.thread.finished_signal.connect(self.on_download_finished)  # Подключение сигнала
        self.thread.start()

        # Сброс состояния
        self.folder = str(get_default_download_path())
        self.url = ""
        self.is_merged = False

    def on_download_finished(self):
        self.console_output.append("Загрузка завершена!")  # Сообщение о завершении
        
if getattr(sys, 'frozen', False):  # Если запущено как .exe
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_PATH = os.path.join(BASE_DIR, "icon.png")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
