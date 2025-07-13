import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QConicalGradient, QBrush, QPixmap, QFontDatabase
from PyQt5.QtCore import Qt, QTimer, QTime, QRect, QPropertyAnimation, pyqtProperty, QPoint, QThread, pyqtSignal, QDateTime
import math
import subprocess
import re
import csv
import os

# CAN data worker thread
class RPMWorker(QThread):
    rpm_signal = pyqtSignal(int)  # signal emitted with RPM value
    voltage_signal = pyqtSignal(str)  # signal emitted with voltage value
    current_signal = pyqtSignal(str)  # signal emitted with current value
    battery_temp_signal = pyqtSignal(str)  # signal emitted with battery temperature
    engine_temp_signal = pyqtSignal(str)  # signal emitted with engine temperature

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop = False
        # Patterns for different CAN message IDs
        self.rpm_pattern = re.compile(r'Speed\s*=\s*([\d\.]+)\s*rpm', re.IGNORECASE)
        self.voltage_pattern = re.compile(r'Voltage\s*=\s*([\d\.]+)\s*V', re.IGNORECASE)
        self.current_pattern = re.compile(r'Current\s*=\s*(-?[\d\.]+)\s*A', re.IGNORECASE)
        self.battery_temp_pattern = re.compile(r'Temperature\s*=\s*([\d\.]+)\s*C', re.IGNORECASE)
        self.engine_temp_pattern = re.compile(r'Temperature\s*=\s*([\d\.]+)\s*C', re.IGNORECASE)
        self.cmd = "candump can0 | candump2analyzer | analyzer"

    def run(self):
        process = subprocess.Popen(
            self.cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        while not self._stop:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                # Handle RPM data from message ID 127488
                if "127488" in line:
                    match = self.rpm_pattern.search(line)
                    if match:
                        try:
                            rpm_value = int(float(match.group(1)))
                            print("RPM:", rpm_value)
                            self.rpm_signal.emit(rpm_value)
                        except ValueError:
                            pass
                
                # Handle battery data from message ID 127508
                elif "127508" in line:
                    print("Battery Status Line:", line)
                    voltage_match = self.voltage_pattern.search(line)
                    current_match = self.current_pattern.search(line)
                    battery_temp_match = self.battery_temp_pattern.search(line)
                    
                    if voltage_match:
                        voltage_value = voltage_match.group(1)
                        print("Voltage:", voltage_value)
                        self.voltage_signal.emit(voltage_value)
                    
                    if current_match:
                        current_value = current_match.group(1)
                        print("Current:", current_value)
                        self.current_signal.emit(current_value)
                    
                    if battery_temp_match:
                        battery_temp_value = battery_temp_match.group(1)
                        print("Battery Temperature:", battery_temp_value)
                        self.battery_temp_signal.emit(battery_temp_value)
                
                # Handle engine temperature from message ID 127489
                elif "127489" in line:
                    print("Engine Temperature Line:", line)
                    engine_temp_match = self.engine_temp_pattern.search(line)
                    if engine_temp_match:
                        engine_temp_value = engine_temp_match.group(1)
                        print("Engine Temperature:", engine_temp_value)
                        self.engine_temp_signal.emit(engine_temp_value)
        
        process.terminate()
        process.wait()

    def stop(self):
        self._stop = True

class CircularProgressBar(QWidget):
    def __init__(self, radius, width):
        super().__init__()
        self.defined_radius = radius
        self.defined_width = width
        self._angle = 180
        self._additional_angle1 = 60
        self._additional_angle2 = 60
        self._additional_angle3 = 30
        self._additional_angle4 = 30

        font_path = "/home/putmonitor/Desktop/zegar/font.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.initUI()
        self.create_animation()
        # Load the image
        self.image = QPixmap("logo.png")  # Replace with your image path

        # Scale the image
        self.scaled_image = self.image.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setWindowTitle("POWERClock")
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove window frame
        self.showFullScreen()  # Set to full screen

        #Initialize CAN raw data
        self.data = ''

        # Initialize CAN data variables
        self.voltage = '0.0'
        self.current = '0.0'
        self.battery_temperature = '0.0'
        self.speed = '0.0'
        self.power = '0.0'
        self.engine_temperature = '0.0'

        # Start CAN worker thread
        self.rpm_worker = RPMWorker()
        self.rpm_worker.rpm_signal.connect(self.on_rpm_update)
        self.rpm_worker.voltage_signal.connect(self.on_voltage_update)
        self.rpm_worker.current_signal.connect(self.on_current_update)
        self.rpm_worker.battery_temp_signal.connect(self.on_battery_temp_update)
        self.rpm_worker.engine_temp_signal.connect(self.on_engine_temp_update)
        self.rpm_worker.start()

    def initUI(self):
        self.setGeometry(0, 0, int(self.defined_radius * 2 + 20), int(self.defined_radius * 2 + 20))
        self.setWindowTitle('Clock with Semi-Circular Progress Bar')
        center = QPoint(self.width() - 105, self.height() - 150)
        self.setStyleSheet("background-color: dark-blue;")
        self.setFocusPolicy(Qt.StrongFocus)  # Enable keyboard focus

        # Initialize voltage clock
        self.label1 = QLabel('1111111111111', self)
        self.label1.move(center.x() - self.defined_radius - 250, center.y() - 350)
        self.label1.setStyleSheet("color: white;")
        self.label1.setFont(QFont(self.font_family, 24))

        # Initialize current clock
        self.label2 = QLabel('1111111111', self)
        self.label2.move(center.x() - self.defined_radius + 125, center.y() - 350)
        self.label2.setStyleSheet("color: white;")
        self.label2.setFont(QFont(self.font_family, 24))

        # Initialize RPM clock
        self.label3 = QLabel('1111111111', self)
        self.label3.move(center.x() - self.defined_radius - 70, center.y() - self.defined_radius - 200)
        self.label3.setStyleSheet("color: white;")
        self.label3.setFont(QFont(self.font_family, 50))

        # Initialize power clock
        self.label4 = QLabel('1111111111111', self)
        self.label4.move(center.x() - self.defined_radius - 75, center.y() - 300)
        self.label4.setStyleSheet("color: white;")
        self.label4.setFont(QFont(self.font_family, 48))

        # Initialize battery temperature clock
        self.label5 = QLabel('111111111111', self)
        self.label5.move(center.x() - self.defined_radius - 250, center.y() - 500)
        self.label5.setStyleSheet("color: white;")
        self.label5.setFont(QFont(self.font_family, 24))

        # Initialize engine temperature clock
        self.label6 = QLabel('11111111111', self)
        self.label6.move(center.x() - self.defined_radius + 130, center.y() - 500)
        self.label6.setStyleSheet("color: white;")
        self.label6.setFont(QFont(self.font_family, 24))

        #Clocks labels section

        # Draw RPM label
        self.label7 = QLabel('RPM', self)
        self.label7.move(center.x() - self.defined_radius - 35, center.y() - self.defined_radius - 235)
        self.label7.setStyleSheet("color: white;")
        self.label7.setFont(QFont(self.font_family, 16))

        # Draw Voltage label
        self.label8 = QLabel('Voltage [ V ]', self)
        self.label8.move(center.x() - self.defined_radius - 250, center.y() - 400)
        self.label8.setStyleSheet("color: white;")
        self.label8.setFont(QFont(self.font_family, 12))

        # Draw Current label
        self.label9 = QLabel('Current [ A ]', self)
        self.label9.move(center.x() - self.defined_radius + 125, center.y() - 400)
        self.label9.setStyleSheet("color: white;")
        self.label9.setFont(QFont(self.font_family, 12))

        # Draw Power label
        self.label10 = QLabel('Power [ kW ]', self)
        self.label10.move(center.x() - self.defined_radius - 75, center.y() - 350)
        self.label10.setStyleSheet("color: white;")
        self.label10.setFont(QFont(self.font_family, 16))

        # Draw battery temperature label
        self.label11 = QLabel('Battery Temperature [ °C ]', self)
        self.label11.move(center.x() - self.defined_radius - 280, center.y() - 550)
        self.label11.setStyleSheet("color: white;")
        self.label11.setFont(QFont(self.font_family, 12))

        # Draw engine temperature label
        self.label12 = QLabel('Engine Temperature [ °C ]', self)
        self.label12.move(center.x() - self.defined_radius + 50, center.y() - 550)
        self.label12.setStyleSheet("color: white;")
        self.label12.setFont(QFont(self.font_family, 12))

        # CSV dump timer label (under logo)
        self.dump_timer_label = QLabel('', self)
        self.dump_timer_label.move(center.x() - self.defined_radius - 50, center.y() + 80)
        self.dump_timer_label.setStyleSheet("color: yellow;")
        self.dump_timer_label.setFont(QFont(self.font_family, 16))
        self.dump_timer_label.hide()

        # CSV logging variables
        self.csv_logging = False
        self.csv_file = None
        self.csv_writer = None
        self.dump_start_time = None
        self.dump_timer = QTimer(self)
        self.dump_timer.timeout.connect(self.update_dump_timer)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)  # Update every 1 seconds
        self.showFullScreen()

    def create_animation(self):
        self.angle_animation = QPropertyAnimation(self, b"angle")
        self.angle_animation.setDuration(100)  # Adjusted duration to match timer

        self.additional_angle1_animation = QPropertyAnimation(self, b"additional_angle1")
        self.additional_angle1_animation.setDuration(100)  # Adjusted duration to match timer

        self.additional_angle2_animation = QPropertyAnimation(self, b"additional_angle2")
        self.additional_angle2_animation.setDuration(100)  # Adjusted duration to match timer

        self.additional_angle3_animation = QPropertyAnimation(self, b"additional_angle3")
        self.additional_angle3_animation.setDuration(100)  # Adjusted duration to match timer

        self.additional_angle4_animation = QPropertyAnimation(self, b"additional_angle4")
        self.additional_angle4_animation.setDuration(100)  # Adjusted duration to match timer

    def paintEvent(self, event):
        center = QPoint(self.width() // 2, self.height() // 2)
        radius = min(self.width(), self.height()) // 2 - 50
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QConicalGradient(center.x(), center.y(), 180)
        gradient.setColorAt(0.0, QColor(Qt.cyan))
        gradient.setColorAt(0.33, QColor(Qt.red))
        gradient.setColorAt(0.67, QColor(Qt.red))
        gradient.setColorAt(1.0, QColor(Qt.cyan))

        gradient2 = QConicalGradient(center.x() + 200, center.y() + 150, 180)
        gradient2.setColorAt(0.0, QColor(Qt.red))
        gradient2.setColorAt(0.1, QColor(Qt.green))
        gradient2.setColorAt(0.3, QColor(Qt.green))
        gradient2.setColorAt(0.4, QColor(Qt.red))
        gradient2.setColorAt(1.0, QColor(Qt.red))

        # Define main arc brush
        pen = QPen(QBrush(gradient), 24, Qt.DashDotLine)
        dashes = [1, 1.525]
        pen.setDashPattern(dashes)

        painter.setPen(pen)
        # Draw arcs
        scale_factor = 1.83
        window_width = self.width()
        window_height = self.height()
        arc_width = int(min(window_width, window_height) // 2 * scale_factor)
        arc_height = arc_width
        x = (window_width - arc_width) // 2
        y = (window_height - arc_height) // 2
        rect = QRect(x, y, arc_width, arc_height)
        painter.drawArc(rect, 180 * 16, -self.angle * 16)

        painter.setPen(QPen(QBrush(gradient2), 24))
        painter.drawArc(rect, 300 * 16, self.additional_angle1 * 8)

        painter.setPen(QPen(QBrush(gradient2), 24))
        painter.drawArc(rect, 240 * 16, -self.additional_angle2 * 8)

        painter.setPen(QPen(Qt.white, 10))
        painter.setFont(QFont(self.font_family, 18))  # Set font for hour marks

        for i in range(9):
            angle = i * 22.5
            radian = math.radians(angle)

            x1 = center.x() + (radius - 20) * math.cos(radian) * -1
            y1 = center.y() + (radius - 20) * math.sin(radian) * -1
            x2 = center.x() + radius * math.cos(radian) * -1
            y2 = center.y() + radius * math.sin(radian) * -1

            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            tx = center.x() + (radius - 40) * math.cos(radian) * -1 - 25
            ty = center.y() + (radius - 40) * math.sin(radian) * -1 + 30

            painter.drawText(int(tx), int(ty), str(250 * i))

        img_x = center.x() - self.scaled_image.width() // 2
        img_y = center.y() - self.scaled_image.height() // 2
        painter.drawPixmap(img_x, img_y, self.scaled_image)
        painter.end()

    def calculate_power(self):
        """Calculate power from voltage and current"""
        try:
            power_value = str(round(float(self.voltage) * float(self.current), 1) / -1000)
            self.power = power_value
            print(f"Calculated Power: {power_value} kW (V={self.voltage}, I={self.current})")
        except (ValueError, AttributeError):
            self.power = '0.0'

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Space:
            if not self.csv_logging:
                self.start_csv_logging()
            else:
                self.stop_csv_logging()
        super().keyPressEvent(event)

    def start_csv_logging(self):
        """Start CSV data logging"""
        # Create filename with current date and time
        current_datetime = QDateTime.currentDateTime()
        filename = current_datetime.toString("yyyy-MM-dd_hh-mm-ss") + "_data.csv"
        
        try:
            self.csv_file = open(filename, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write header
            header = ['Timestamp', 'RPM', 'Voltage_V', 'Current_A', 'Power_kW', 'Battery_Temp_C', 'Engine_Temp_C']
            self.csv_writer.writerow(header)
            
            self.csv_logging = True
            self.dump_start_time = QTime.currentTime()
            self.dump_timer.start(100)  # Update every 100ms for smooth timer display
            self.dump_timer_label.show()
            
            print(f"Started CSV logging to: {filename}")
            
        except Exception as e:
            print(f"Error starting CSV logging: {e}")

    def stop_csv_logging(self):
        """Stop CSV data logging"""
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
        
        self.csv_logging = False
        self.dump_timer.stop()
        self.dump_timer_label.hide()
        print("Stopped CSV logging")

    def log_data_to_csv(self):
        """Log current data to CSV file"""
        if self.csv_logging and self.csv_writer:
            try:
                current_time = QTime.currentTime()
                timestamp = current_time.toString("hh:mm:ss.zzz")
                
                row = [
                    timestamp,
                    self.speed,
                    self.voltage,
                    self.current,
                    self.power,
                    self.battery_temperature,
                    self.engine_temperature
                ]
                
                self.csv_writer.writerow(row)
                self.csv_file.flush()  # Ensure data is written immediately
                
            except Exception as e:
                print(f"Error logging data to CSV: {e}")

    def update_dump_timer(self):
        """Update the dump timer display"""
        if self.dump_start_time:
            current_time = QTime.currentTime()
            elapsed_ms = self.dump_start_time.msecsTo(current_time)
            elapsed_seconds = elapsed_ms / 1000.0
            
            minutes = int(elapsed_seconds // 60)
            seconds = elapsed_seconds % 60
            
            timer_text = f"Recording: {minutes:02d}:{seconds:05.2f}"
            self.dump_timer_label.setText(timer_text)

    def on_voltage_update(self, voltage_value):
        self.voltage = voltage_value
        self.calculate_power()
        self.update_progress()

    def on_current_update(self, current_value):
        self.current = current_value
        self.calculate_power()
        self.update_progress()

    def on_battery_temp_update(self, battery_temp_value):
        self.battery_temperature = battery_temp_value
        self.update_progress()

    def on_engine_temp_update(self, engine_temp_value):
        self.engine_temperature = engine_temp_value
        self.update_progress()

    def update_progress(self):
        current_time = QTime.currentTime()
        seconds = current_time.second()
        milliseconds = current_time.msec()
        total_seconds = seconds + milliseconds / 1000.0
        calibrated_speed = float(self.speed) / 11.11
        calibrated_current = float(self.current) * 4.5 * -1
        calibrated_power = float(self.power) / 11.11
        new_angle = calibrated_speed % 181
        new_additional_angle1 = calibrated_power % 91
        new_additional_angle2 = calibrated_current % 90
        new_additional_angle3 = (total_seconds * 1.5) % 90
        new_additional_angle4 = (total_seconds * 1) % 90
        self.label1.setText(self.voltage)
        self.label2.setText(self.current)
        self.label3.setText(self.speed)
        self.label4.setText(self.power)
        self.label5.setText(self.battery_temperature)
        self.label6.setText(self.engine_temperature)
        
        # Log data to CSV if logging is active
        self.log_data_to_csv()
        
        self.angle_animation.stop()
        self.angle_animation.setStartValue(self.angle)
        self.angle_animation.setEndValue(new_angle)
        self.angle_animation.start()

        self.additional_angle1_animation.stop()
        self.additional_angle1_animation.setStartValue(self.additional_angle1)
        self.additional_angle1_animation.setEndValue(new_additional_angle1)
        self.additional_angle1_animation.start()

        self.additional_angle2_animation.stop()
        self.additional_angle2_animation.setStartValue(self.additional_angle2)
        self.additional_angle2_animation.setEndValue(new_additional_angle2)
        self.additional_angle2_animation.start()

        self.additional_angle3_animation.stop()
        self.additional_angle3_animation.setStartValue(self.additional_angle3)
        self.additional_angle3_animation.setEndValue(new_additional_angle3)
        self.additional_angle3_animation.start()

    def on_rpm_update(self, rpm_value):
        self.speed = str(rpm_value)
        self.update_progress()

    def closeEvent(self, event):
        # Stop CSV logging if active
        if self.csv_logging:
            self.stop_csv_logging()
        
        # Stop CAN worker thread
        if hasattr(self, 'rpm_worker'):
            self.rpm_worker.stop()
            self.rpm_worker.wait()
        
        super().closeEvent(event)

    @pyqtProperty(int)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.update()

    @pyqtProperty(int)
    def additional_angle1(self):
        return self._additional_angle1

    @additional_angle1.setter
    def additional_angle1(self, value):
        self._additional_angle1 = value
        self.update()

    @pyqtProperty(int)
    def additional_angle2(self):
        return self._additional_angle2

    @additional_angle2.setter
    def additional_angle2(self, value):
        self._additional_angle2 = value
        self.update()

    @pyqtProperty(int)
    def additional_angle3(self):
        return self._additional_angle3

    @additional_angle3.setter
    def additional_angle3(self, value):
        self._additional_angle3 = value
        self.update()

    @pyqtProperty(int)
    def additional_angle4(self):
        return self._additional_angle4

    @additional_angle4.setter
    def additional_angle4(self, value):
        self._additional_angle4 = value
        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CircularProgressBar(500, 20)
    sys.exit(app.exec_())