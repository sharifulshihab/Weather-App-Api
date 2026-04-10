import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QSizePolicy, \
    QStackedLayout, QMessageBox
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
from matplotlib.patches import Polygon
from matplotlib.colors import LinearSegmentedColormap

rcParams['font.family'] = 'Segoe UI Emoji'
import numpy as np


class LocationWorker(QThread):
    location_obtained = pyqtSignal(float, float, str)
    error_occurred = pyqtSignal(str)

    def run(self):
        services = [
            self.get_location_ipapi,
            self.get_location_ipinfo,
            self.get_location_geoplugin
        ]

        for service in services:
            try:
                lat, lon, city = service()
                if lat and lon:
                    self.location_obtained.emit(lat, lon, city)
                    return
            except:
                continue

        self.error_occurred.emit("Could not detect your location. Please enter city name manually.")

    def get_location_ipapi(self):

        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            lat = data.get('latitude')
            lon = data.get('longitude')
            city = data.get('city', '')
            if lat and lon:
                return lat, lon, city
        return None, None, None

    def get_location_ipinfo(self):

        response = requests.get('https://ipinfo.io/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            loc = data.get('loc', '').split(',')
            if len(loc) == 2:
                lat = float(loc[0])
                lon = float(loc[1])
                city = data.get('city', '')
                return lat, lon, city
        return None, None, None

    def get_location_geoplugin(self):

        response = requests.get('http://www.geoplugin.net/json.gp', timeout=5)
        if response.status_code == 200:
            data = response.json()
            lat = data.get('geoplugin_latitude')
            lon = data.get('geoplugin_longitude')
            city = data.get('geoplugin_city', '')
            if lat and lon and lat != '0' and lon != '0':
                return float(lat), float(lon), city
        return None, None, None


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.city_label = QLabel("Enter City Name", self)
        self.city_input = QLineEdit(self)
        self.location_button = QPushButton("📍 Use My Location", self)
        self.get_weather_button = QPushButton("Get Weather", self)
        self.temperature_label = QLabel("", self)
        self.feels_label = QLabel("", self)
        self.toggle_button = QPushButton("", self)
        self.sound_enabled = False
        self.sound_button = QPushButton("🔇", self)
        self.emoji_label = QLabel("", self)
        self.description_label = QLabel("", self)
        self.humidity_label = QLabel("", self)

        self.hourly_chart = FigureCanvas(Figure(figsize=(7, 3.8), dpi=100))
        self.hourly_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.hourly_chart.figure.subplots()

        self.gif_label = QLabel(self)
        self.player = QMediaPlayer()
        self.is_celsius = True
        self.movie = None
        self.location_worker = None
        self.is_dark_theme = False

        self.toggle_container = QWidget(self)
        self.toggle_stack = QStackedLayout(self.toggle_container)
        self.toggle_placeholder = QWidget()
        self.toggle_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toggle_placeholder.setFixedHeight(40)
        self.toggle_stack.addWidget(self.toggle_placeholder)
        self.toggle_stack.addWidget(self.toggle_button)
        self.toggle_stack.setCurrentWidget(self.toggle_placeholder)

        self.chart_container = QWidget(self)
        self.chart_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chart_stack = QStackedLayout(self.chart_container)
        self.chart_placeholder = QWidget()
        self.chart_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chart_stack.addWidget(self.chart_placeholder)
        self.chart_stack.addWidget(self.hourly_chart)
        self.chart_stack.setCurrentWidget(self.chart_placeholder)

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Weather App")
        self.setWindowIcon(QIcon("assets//weather_icon"))
        self.setMinimumSize(550, 850)
        self.resize(600, 950)

        vbox = QVBoxLayout()
        vbox.setSpacing(10)
        vbox.setContentsMargins(15, 15, 15, 15)

        vbox.addWidget(self.city_label, 1)
        vbox.addWidget(self.city_input, 1)
        vbox.addWidget(self.location_button, 1)
        vbox.addWidget(self.get_weather_button, 1)
        vbox.addWidget(self.toggle_container, 1)
        vbox.addWidget(self.sound_button, 1)
        vbox.addWidget(self.temperature_label, 2)
        vbox.addWidget(self.feels_label, 1)
        vbox.addWidget(self.emoji_label, 2)
        vbox.addWidget(self.description_label, 1)
        vbox.addWidget(self.humidity_label, 1)
        vbox.addWidget(self.chart_container, 4)

        self.setLayout(vbox)

        self.city_label.setAlignment(Qt.AlignCenter)
        self.city_input.setAlignment(Qt.AlignCenter)
        self.temperature_label.setAlignment(Qt.AlignCenter)
        self.feels_label.setAlignment(Qt.AlignCenter)
        self.emoji_label.setAlignment(Qt.AlignCenter)
        self.description_label.setAlignment(Qt.AlignCenter)
        self.humidity_label.setAlignment(Qt.AlignCenter)

        self.city_label.setObjectName("city_label")
        self.city_input.setObjectName("city_input")
        self.location_button.setObjectName("location_button")
        self.get_weather_button.setObjectName("get_weather_button")
        self.toggle_button.setObjectName("toggle_button")
        self.sound_button.setObjectName("sound_button")
        self.temperature_label.setObjectName("temperature_label")
        self.feels_label.setObjectName("feels_label")
        self.emoji_label.setObjectName("emoji_label")
        self.description_label.setObjectName("description_label")
        self.humidity_label.setObjectName("humidity_label")

        self.base_style = """
            QLabel, QPushButton {
                font-family: calibri;
            }
            QLabel#city_label {
                font-size: 28px;
                font-style: italic;
            }
            QPushButton {
                font-size: 20px;
                font-weight: bold;
                padding: 6px;
                margin: 5px;
            }
            QPushButton#location_button {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
            }
            QPushButton#location_button:hover {
                background-color: #45a049;
            }
            QPushButton#get_weather_button {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
            }
            QPushButton#get_weather_button:hover {
                background-color: #0b7dda;
            }
            QPushButton#sound_button {
                font-size: 14px;      
                padding: 2px;         
                margin: 0px;
                border: none;        
                color: #007BFF;
                background-color: transparent;
            }
            QPushButton#toggle_button {
                background-color: #FF9800;
                color: white;
                border-radius: 10px;
            }
            QPushButton#toggle_button:hover {
                background-color: #fb8c00;
            }
            QLineEdit#city_input {
                font-size: 28px; 
                padding: 6px;   
                margin: 5px;
                border: 2px solid #ccc;
                border-radius: 10px;
            }
            QLabel#temperature_label {
                font-size: 50px;
            }
            QLabel#feels_label {
                font-size: 20px;
            }
            QLabel#emoji_label {
                font-size: 60px;
                font-family: Segoe UI Emoji;
            }
            QLabel#description_label {
                font-size: 30px;
            }
            QLabel#humidity_label {
                font-size: 30px;
            }
        """
        self.setStyleSheet(self.base_style + "QWidget {background-color:white;}")
        self.temperature_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.emoji_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sound_button.setFixedSize(28, 28)
        self.gif_label.setGeometry(0, 0, self.width(), self.height())
        self.gif_label.setScaledContents(True)
        self.gif_label.lower()

        self.get_weather_button.clicked.connect(self.get_weather)
        self.location_button.clicked.connect(self.get_location_weather)
        self.city_input.returnPressed.connect(self.get_weather)
        self.toggle_button.clicked.connect(self.toggle_temp)
        self.sound_button.clicked.connect(self.toggle_sound)

    def apply_button_styles(self, opaque=False):
        if opaque:
            button_style = """
                QPushButton#location_button { background-color: #4CAF50; color: white; }
                QPushButton#get_weather_button { background-color: #2196F3; color: white; }
                QPushButton#toggle_button { background-color: #FF9800; color: white; }
                QPushButton#sound_button { background-color: transparent; color: #007BFF; }
            """
        else:
            text_color = "white" if self.is_dark_theme else "#2c3e50"
            button_style = f"""
                QPushButton#location_button {{ background-color: rgba(76, 175, 80, 0.5); color: {text_color}; }}
                QPushButton#get_weather_button {{ background-color: rgba(33, 150, 243, 0.5); color: {text_color}; }}
                QPushButton#toggle_button {{ background-color: rgba(255, 152, 0, 0.5); color: {text_color}; }}
                QPushButton#sound_button {{ background-color: rgba(0, 0, 0, 0.3); color: {text_color}; }}
            """

        button_style += """
            QPushButton#location_button:hover { background-color: rgba(76, 175, 80, 0.8); }
            QPushButton#get_weather_button:hover { background-color: rgba(33, 150, 243, 0.8); }
            QPushButton#toggle_button:hover { background-color: rgba(255, 152, 0, 0.8); }
        """
        self.location_button.setStyleSheet(button_style)
        self.get_weather_button.setStyleSheet(button_style)
        self.toggle_button.setStyleSheet(button_style)
        self.sound_button.setStyleSheet(button_style)

    def resizeEvent(self, event):
        if hasattr(self, "gif_label"):
            self.gif_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def get_location_weather(self):
        self.location_button.setEnabled(False)
        self.location_button.setText("📍 Detecting location...")

        self.temperature_label.setText("📍 Detecting your location...\nPlease wait...")
        self.temperature_label.setStyleSheet("font-size:20px;color:#4CAF50")

        self.location_worker = LocationWorker()
        self.location_worker.location_obtained.connect(self.on_location_obtained)
        self.location_worker.error_occurred.connect(self.on_location_error)
        self.location_worker.start()

    def on_location_obtained(self, lat, lon, city):
        self.location_button.setEnabled(True)
        self.location_button.setText("📍 Use My Location")

        api_key = "ENTER_YOUR_API_KEY"
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["cod"] == 200:
                self.city_input.setText(data["name"])
                self.display_weather(data)
            else:
                self.display_error("Could not get weather for your location")
        except Exception as e:
            self.display_error(f"Could not get weather for your location:\nPlease check your internet connection")

    def on_location_error(self, error_msg):
        self.location_button.setEnabled(True)
        self.location_button.setText("📍 Use My Location")

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Location Detection")
        msg.setText("Could not detect your location automatically")
        msg.setInformativeText(
            "You can still:\n• Type your city name manually\n• Use the 'Get Weather' button\n\nMake sure you have an internet connection.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

        if self.temperature_label.text().startswith("📍"):
            self.temperature_label.clear()
            self.temperature_label.setStyleSheet("font-size:50px")


    def get_weather(self):
        api_key = "ENTER_YOUR_API_KEY"
        city = self.city_input.text()
        if not city.strip():
            self.display_error("Please enter a city name")
            return
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["cod"] == 200:
                self.display_weather(data)
        except requests.exceptions.HTTPError as http_error:
            match response.status_code:
                case 400:
                    self.display_error("Bad Request:\nPlease check Your Input")
                case 401:
                    self.display_error("Unauthorized:\nInvalid Api Key")
                case 403:
                    self.display_error("Forbidden:\nAccess is denied")
                case 404:
                    self.display_error("Not found:\nCity not found")
                case 500:
                    self.display_error("Internal Server Error:\nPlease try again later")
                case 501:
                    self.display_error("Bad Gateway:\nInvalid response from the server")
                case 503:
                    self.display_error("Server Unavailable:\nServer is down")
                case 504:
                    self.display_error("Gateway timeout:\nNo response from the server")
                case _:
                    self.display_error(f"Http error occured:\n{http_error}")
        except requests.exceptions.ConnectionError:
            self.display_error(f"Connection Error:\nPlease check your connection")
        except requests.exceptions.Timeout:
            self.display_error("Timeout Error:\nThe request timed out")
        except requests.exceptions.TooManyRedirects:
            self.display_error("Too Many RedirectsL:\nCheck the url")
        except requests.exceptions.RequestException as req_error:
            self.display_error(f"Request error:\n{req_error}")

    def display_error(self, message):
        error_style = """
            QWidget {
                background-color: #FF4444;
            }
            QLabel {
                color: white;
                font-size: 20px;
            }
            QPushButton {
                background-color: rgba(255,255,255,0.3);
                color: white;
            }
            QLineEdit {
                background-color: white;
                color: black;
            }
        """
        self.setStyleSheet(self.base_style + error_style)

        self.temperature_label.setStyleSheet("font-size:30px;color:white")
        self.temperature_label.setText(message)
        self.feels_label.clear()
        self.emoji_label.clear()
        self.description_label.clear()
        self.humidity_label.clear()
        self.toggle_button.setText("")
        self.is_celsius = True
        self.stop_animation()
        self.stop_sound()

        self.toggle_stack.setCurrentWidget(self.toggle_placeholder)
        self.chart_stack.setCurrentWidget(self.chart_placeholder)

        if hasattr(self, "current_weather_id"):
            del self.current_weather_id
        if hasattr(self, "temperature_c"):
            del self.temperature_c
        if hasattr(self, "feels_like_c"):
            del self.feels_like_c

        self.apply_button_styles(opaque=True)

    def display_weather(self, data):
        self.temperature_label.setStyleSheet("font-size:50px")
        self.temperature_c = data["main"]["temp"]
        self.temperature_f = round(self.temperature_c * 1.8 + 32)
        self.temperature_label.setText(f"{round(self.temperature_c)}°C")
        self.toggle_button.setText("Switch to °F")
        self.feels_like_c = data["main"]["feels_like"]
        self.feels_like_f = round(self.feels_like_c * 1.8 + 32)
        self.feels_label.setText(f"Feels Like: {round(self.feels_like_c)}°C")

        weather_desc = data["weather"][0]["description"]
        weather_id = data["weather"][0]["id"]
        self.current_weather_id = weather_id
        humidity = data["main"]["humidity"]

        self.emoji_label.setText(self.get_weather_emoji(weather_id))
        self.description_label.setText(f"{weather_desc.title()}")
        self.humidity_label.setText(f"💧{humidity} %")
        self.set_weather_theme(weather_id)
        self.set_weather_animation(weather_id)
        self.set_weather_sound(weather_id)

        self.toggle_stack.setCurrentWidget(self.toggle_button)
        self.chart_stack.setCurrentWidget(self.hourly_chart)

        self.apply_button_styles(opaque=False)

        self.get_hourly_forecast(self.city_input.text())

    def toggle_temp(self):
        if not hasattr(self, "temperature_c"):
            return
        if self.is_celsius:
            self.temperature_label.setText(f"{self.temperature_f}°F")
            self.feels_label.setText(f"Feels Like: {round(self.feels_like_f)}°F")
            self.toggle_button.setText("Switch to °C")
            self.is_celsius = False
        else:
            self.temperature_label.setText(f"{round(self.temperature_c)}°C")
            self.feels_label.setText(f"Feels Like: {round(self.feels_like_c)}°C")
            self.toggle_button.setText("Switch to °F")
            self.is_celsius = True

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.sound_button.setText("🔊")
            if hasattr(self, "current_weather_id"):
                self.set_weather_sound(self.current_weather_id)
        else:
            self.sound_button.setText("🔇")
            self.stop_sound()

    def stop_animation(self):
        if hasattr(self, "movie") and self.movie:
            self.movie.stop()
            self.gif_label.clear()
            self.movie = None

    def play_sound(self, file):
        self.player.stop()
        try:
            self.player.mediaStatusChanged.disconnect()
        except:
            pass

        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file)))
        self.player.setVolume(60)
        self.player.play()
        self.player.mediaStatusChanged.connect(self.loop_sound)

    def loop_sound(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.player.play()

    def stop_sound(self):
        self.player.stop()

    @staticmethod
    def get_weather_emoji(weather_id):
        if 200 <= weather_id <= 232:
            return "⛈️"
        elif 300 <= weather_id <= 321:
            return "🌦️"
        elif 500 <= weather_id <= 531:
            return "🌧️"
        elif 600 <= weather_id <= 622:
            return "❄️"
        elif 700 <= weather_id <= 781:
            return "🌫️"
        elif weather_id == 800:
            return "☀️"
        elif 801 <= weather_id <= 804:
            return "☁️"
        else:
            return "🌈"

    def set_weather_theme(self, weather_id):
        if weather_id == 800:
            self.setStyleSheet(self.base_style + "QWidget {background-color:#87CEEB;}")
            self.is_dark_theme = False
        elif 200 <= weather_id <= 232:
            self.setStyleSheet(self.base_style + "QWidget {background-color:#4B4B4B;}QLabel {color:white;}")
            self.is_dark_theme = True
        elif 300 <= weather_id <= 321:
            self.setStyleSheet(self.base_style + "QWidget {background-color:#A4B0BD;}")
            self.is_dark_theme = False
        elif 500 <= weather_id <= 531:
            self.setStyleSheet(self.base_style + "QWidget {background-color:#5F9EA0;}QLabel {color:white;}")
            self.is_dark_theme = True
        elif 600 <= weather_id <= 622:
            self.setStyleSheet(self.base_style + "QWidget {background-color:#E0FFFF;}")
            self.is_dark_theme = False
        elif 700 <= weather_id <= 741:
            self.setStyleSheet(self.base_style + "QWidget {background-color:#D3D3D3;}")
            self.is_dark_theme = False
        elif 801 <= weather_id <= 804:
            self.setStyleSheet(self.base_style + "QWidget {background-color:#C0C0C0;}")
            self.is_dark_theme = False
        else:
            self.setStyleSheet(self.base_style + "QWidget {background-color:white;}")
            self.is_dark_theme = False

    def set_weather_animation(self, weather_id):
        self.stop_animation()
        if 200 <= weather_id <= 232:
            self.movie = QMovie("assets//thunder.gif")
            self.setStyleSheet(self.base_style + "QLabel {color: white;background: transparent}")
        elif 500 <= weather_id <= 531:
            self.movie = QMovie("assets//rain.gif")
            self.setStyleSheet(self.base_style + "QLabel {color: white;background: transparent}")
        elif 600 <= weather_id <= 622:
            self.movie = QMovie("assets//snow.webp")
            self.setStyleSheet(self.base_style + "QLabel {color: black;background: transparent}")
        else:
            return
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        self.movie.setScaledSize(self.size())

    def set_weather_sound(self, weather_id):
        self.stop_sound()
        if not self.sound_enabled:
            return
        if 200 <= weather_id <= 232:
            self.play_sound("assets//thunder_sound.mp3")
        elif 300 <= weather_id <= 531:
            self.play_sound("assets//rain_sound.mp3")
        elif 600 <= weather_id <= 622:
            self.play_sound("assets//snow_sound.mp3")
        else:
            return

    def is_active_animation_weather(self, weather_id):
        return (200 <= weather_id <= 232) or (500 <= weather_id <= 531) or \
            (600 <= weather_id <= 622)

    def get_hourly_forecast(self, city):
        api_key = "ENTER_YOUR_API_KEY"
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            hourly_data = []
            for i in range(min(8, len(data["list"]))):
                item = data["list"][i]
                temp = round(item["main"]["temp"])
                time = item["dt_txt"].split(" ")[1][:5]
                weather_id = item["weather"][0]["id"]

                hourly_data.append({
                    "time": time,
                    "temp": temp,
                    "weather_id": weather_id
                })

            self.plot_hourly_forecast(hourly_data)

        except Exception as e:
            print("Forecast error:", e)

    def plot_hourly_forecast(self, hourly_data):
        self.ax.clear()

        animation_active = self.is_active_animation_weather(self.current_weather_id)

        if animation_active:
            bg_color = (0.5, 0.5, 0.5, 0.5) 
            self.hourly_chart.figure.patch.set_facecolor(bg_color)
            self.ax.set_facecolor(bg_color)
            text_color = 'white' 
        else:
            self.hourly_chart.figure.patch.set_facecolor('none')
            self.ax.set_facecolor('none')
            text_color = 'white' if self.is_dark_theme else 'black'

        self.hourly_chart.setAutoFillBackground(False)
        self.hourly_chart.setStyleSheet("background: transparent;")

        x = np.arange(len(hourly_data))
        temps = [h['temp'] for h in hourly_data]
        times = [h['time'] for h in hourly_data]

        x_smooth = np.linspace(0, len(hourly_data) - 1, 100)
        temps_smooth = np.interp(x_smooth, x, temps)

        rainbow_cmap = LinearSegmentedColormap.from_list(
            'rainbow_gradient',
            ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082', '#9400D3']
        )

        for i in range(len(x_smooth) - 1):
            color = rainbow_cmap(i / len(x_smooth))
            verts = [(x_smooth[i], 0)] + \
                    [(x_smooth[i], temps_smooth[i]),
                     (x_smooth[i + 1], temps_smooth[i + 1])] + \
                    [(x_smooth[i + 1], 0)]
            polygon = Polygon(verts, facecolor=color, alpha=0.35, edgecolor='none', zorder=1)
            self.ax.add_patch(polygon)

        self.ax.plot(x, temps, marker='o', linewidth=2.5,
                     color='#FF3366', markersize=6, zorder=3,
                     markerfacecolor='white', markeredgewidth=2, markeredgecolor='#FF3366')

        def to_12hr(t):
            h, m = map(int, t.split(":"))
            suffix = "AM" if h < 12 else "PM"
            h = h % 12
            if h == 0:
                h = 12
            return f"{h}:{m:02d} {suffix}"

        times_12 = [to_12hr(t) for t in times]

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(times_12, fontsize=7, color=text_color)
        self.ax.tick_params(axis='x', colors=text_color, pad=4)

        min_temp = min(temps) - 6
        max_temp = max(temps) + 16
        self.ax.set_ylim(min_temp, max_temp)

        y_ticks = range(int(min_temp) - (int(min_temp) % 10),
                        int(max_temp) + 11, 10)
        self.ax.set_yticks(y_ticks)
        self.ax.set_yticklabels([f"{t}°C" for t in y_ticks], fontsize=7, color=text_color)
        self.ax.set_ylabel('')

        for i, temp in enumerate(temps):
            offset = 4 if temp >= 0 else -12
            bg_anno = "white" if text_color == 'black' else "#333333"
            self.ax.annotate(f"{temp}°C",
                             (x[i], temps[i]),
                             textcoords="offset points",
                             xytext=(0, offset),
                             ha='center',
                             fontsize=7.5,
                             fontweight='bold',
                             color=text_color,
                             bbox=dict(boxstyle="round,pad=0.15",
                                       facecolor=bg_anno,
                                       edgecolor="#FF3366",
                                       alpha=0.85))

        for i, h in enumerate(hourly_data):
            emoji = self.get_weather_emoji(h['weather_id'])
            offset = 12 if temps[i] >= 0 else -22
            self.ax.annotate(emoji,
                             (x[i], temps[i]),
                             textcoords="offset points",
                             xytext=(0, offset),
                             ha='center',
                             fontsize=14,
                             color=text_color,
                             zorder=5)

        self.ax.grid(True, linestyle='--', alpha=0.25, linewidth=0.4)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        for spine in self.ax.spines.values():
            spine.set_color(text_color)

        self.ax.set_title("🌈 24-Hour Forecast", fontsize=9.5, fontweight='bold', pad=9.0, color=text_color)
        self.ax.figure.subplots_adjust(left=0.07, right=0.98, top=0.85, bottom=0.18)

        self.hourly_chart.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WeatherApp()
    win.show()
    sys.exit(app.exec_())