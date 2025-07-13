# Analiza zegar.py - Dashboard pojazdu elektrycznego/hybrydowego

## Ogólny opis
`zegar.py` to aplikacja dashboardu w PyQt5, która wyświetla parametry pojazdu elektrycznego lub hybrydowego w czasie rzeczywistym. Nazwa "zegar" oznacza "clock" po polsku, ale aplikacja to znacznie więcej niż zwykły zegar.

## Główne funkcjonalności

### 1. **Interface użytkownika**
- **Pełnoekranowy dashboard** z ciemnym tłem
- **Okrągłe wskaźniki/gauge'e** z animowanymi łukami
- **Kolorowe gradienty** (cyan, czerwony, zielony) dla wizualizacji danych
- **Logo** wyświetlane w centrum dashboardu
- **Niestandardowa czcionka** ładowana z pliku `font.ttf`

### 2. **Monitorowane parametry pojazdu**
Aplikacja wyświetla następujące parametry:

- **RPM** (obrotów na minutę) - główny wskaźnik w centrum
- **Napięcie** (Voltage [V]) - górny lewy róg
- **Prąd** (Current [A]) - górny prawy róg  
- **Moc** (Power [kW]) - obliczana jako napięcie × prąd ÷ 1000
- **Temperatura baterii** (Battery Temperature [°C]) - dolny lewy róg
- **Temperatura silnika** (Engine Temperature [°C]) - dolny prawy róg

### 3. **Źródła danych**

#### Wersja CAN (`zegar.py`)
- **Odczyt bezpośredni z magistrali CAN** (can0)
- **Wielowątkowe przetwarzanie** RPM za pomocą `RPMWorker` thread
- **Zewnętrzne narzędzia**: `candump`, `candump2analyzer`, `analyzer`
- **Automatyczne parsowanie** komunikatów CAN z ID 127488, 127508, 127489

#### Wersja UDP (`zegar_udp.py`)
- **Odbieranie danych przez UDP** na porcie 8090
- **Sieciowe przetwarzanie** danych CAN otrzymanych zdalnie

### 4. **Przetwarzanie danych**
```python
# Kalibracja wskaźników:
calibrated_speed = float(speed) / 11.11     # RPM -> kąt (0-180°)
calibrated_current = float(current) * 4.5 * -1  # Prąd -> kąt łuku
calibrated_power = float(power) / 11.11     # Moc -> kąt łuku
```

### 5. **Animacje**
- **Płynne animacje** wszystkich wskaźników (100ms)
- **Automatyczna aktualizacja** co 1 sekundę
- **Responsive design** dostosowany do różnych rozdzielczości

## Zastosowanie
Ta aplikacja jest prawdopodobnie używana w:
- **Pojazdach elektrycznych** do monitorowania parametrów baterii i silnika
- **Pojazdach hybrydowych** do kontroli systemu napędowego
- **Projektach motorsportowych** wymagających monitoringu w czasie rzeczywistym
- **Systemach testowych** do analizy wydajności pojazdu

## Architektura techniczna

### Zależności
- **PyQt5** - interface graficzny
- **subprocess** - komunikacja z zewnętrznymi narzędziami CAN
- **socket** - komunikacja UDP (w wersji UDP)
- **threading** - wielowątkowe przetwarzanie RPM
- **regex** - parsowanie komunikatów CAN

### Struktura klas
- `CircularProgressBar` - główny widget dashboardu
- `RPMWorker` - thread worker do odczytu RPM z CAN

### Zewnętrzne narzędzia
- `candump` - odczyt raw danych z magistrali CAN
- `candump2analyzer` - preprocessing danych CAN
- `analyzer` - dekodowanie komunikatów CAN do czytelnego formatu

## Konfiguracja
- **Ścieżka czcionki**: `/home/putmonitor/Desktop/zegar/font.ttf`
- **Logo**: `logo.png` (100x100 px)
- **Interface CAN**: `can0`
- **Port UDP**: 8090 (w wersji UDP)

## Bezpieczeństwo i stabilność
- **Graceful shutdown** - prawidłowe zamykanie thread'ów
- **Error handling** dla komunikacji CAN/UDP
- **Regex validation** danych wejściowych
- **Fallback values** w przypadku błędów parsing'u