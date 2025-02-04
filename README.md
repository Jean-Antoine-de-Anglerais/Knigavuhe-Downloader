# Knigavuhe Downloader

Это графическое десктопное приложение на PyQt6, позволяющее скачивать аудиокниги с сайта knigavuhe.org.

## Возможности и всё такое

* Скачивание аудиокниг по URL
* Выбор папки для сохранения файлов (по умолчанию: ~/Music/Audiobooks/)
* Автоматическое извлечение названия книги, авторов и чтецов
* Отображение консоли с логами загрузки
* Прогресс-бар загрузки
* Тёмная тема оформления

## Установка

### Для Windows

Просто скачайте последнюю версию приложения из релизов и запустите исполняемый файл

### Для macOS

0. Убедитесь, что у вас установлен Python, версии 3.12, или новее
1. Скачайте и распакуйте исходный код проекта
2. Настройте виртуальную среду: `python3 -m venv venv`
3. Активируйте виртуальную среду: `source venv/bin/activate`
4. Установите зависимости: `pip3 install -r requirements.txt`
5. Запустите приложение: `python3 main.py`

### Для Linux

Инструкция аналогична инструкции для macOS

## Использование

1. Откройте приложение.
2. Вставьте ссылку на аудиокнигу с knigavuhe.org
3. Выберите папку для сохранения (по желанию)
4. Нажмите кнопку "Начать загрузку"
5. Дождитесь завершения загрузки

## Планы на дальнейшую разработку

1. Добавить нормальную обработку ошибок
2. Добавить возможность скачивать аудиокнигу одним объединённым файлом
3. Выложить бинарники программы для 32-битной Windows, а так же для Linux и macOS

## Лицензия

Проект распространяется под лицензией MIT. Проект никак не связан с авторами и правообладателями сайта knigavuhe.org

## Контакты

Если у вас возникнут вопросы или предложения, пожалуйста, создайте issue в репозитории
