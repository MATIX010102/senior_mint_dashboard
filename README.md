# Senior Mint Dashboard 🖥️👴

Ultra-lightweight, locked-down senior-friendly custom desktop environment and dashboard launcher for **Linux Mint 22 XFCE 64-bit** (Ubuntu 24.04 noble base). Designed specifically for elderly non-technical users on low-spec hardware (such as HP 15t-r100: Intel Celeron N2840 @ 2.16 GHz, 4GB RAM, HDD).

---

## ⚡ Szybka Instalacja Jedną Komendą (One-Line Installer)

Zaloguj się na konto z uprawnieniami administratora (`root` / `sudo`) w systemie Linux Mint i uruchom w terminalu:

```bash
curl -sSL https://raw.githubusercontent.com/MATIX010102/senior_mint_dashboard/main/install.sh | sudo bash
```

Instalator wykona wszystko automatycznie:
1. Zainstaluje wymagane pakiety systemowe (`python3-pyqt6`, `python3-pyqt6.qtwebengine`, `cups`, `hplip`, `gvfs-backends`, `mtp-tools`, `rsync`, `python3-gi`).
2. Utworzy zablokowane konto użytkownika `dziadek` bez dostępu do `sudo`, terminala i możliwości modyfikacji dysków.
3. Skonfiguruje autologowanie w LightDM bezpośrednio do bezpiecznego pulpitu Dziadka.
4. Zainstaluje usługę automatycznych cichych aktualizacji z GitHub.

---

## 🛠️ Ręczna Instalacja (Manual Installation)

Jeśli wolisz sklonować repozytorium ręcznie:

```bash
git clone https://github.com/MATIX010102/senior_mint_dashboard.git
cd senior_mint_dashboard
sudo bash install.sh
```

---

## 🌟 Główne Funkcje (Key Features)

### 1. 🔒 Kuloodporne Zabezpieczenie Systemu (System Lockdown)
- **Konto Dziadka**: Dedykowany restricted user `dziadek` pozbawiony grup `sudo`, `wheel`, `adm` i `lpadmin`.
- **Reguła Polkit v124+** (`/etc/polkit-1/rules.d/50-dziadek-udisks2-lockdown.rules`): Całkowicie blokuje formatowanie dysków, usuwanie partycji oraz czyszczenie nośników USB/telefonu.
- **Blokada Skrótów Klawiszowych**: Zneutralizowane skróty `Ctrl+Alt+T` (terminal), `Alt+F4` (zamykanie okien) oraz `Alt+F2` w ustawieniach XFCE.

### 2. 🎨 Lekki Pulpit Dziadka (Python 3 + PyQt6)
- **Bardzo niskie zużycie RAM**: `< 150 MB`, szybki zimny start `< 2s` na dyskach HDD i procesorach Intel Celeron.
- **Duże, czytelne widgety**: Zegar (54pt), Data (22pt) oraz Pogoda (20pt).
- **Rodzinny Pokaz Slajdów**: Tapeta automatycznie zmienia zdjęcia z folderu `~/Obrazki/Tapety`. Dodatkowo prosty przycisk w UI *"Zmień tapetę rodzinną"*.
- **Wbudowane Okna WebViews**: Bezpieczne podglądy stron: **Bank**, **Gmail**, **Poczta Onet**, **Ubezpieczenia** z przyciskami łatwej nawigacji (*Domowa, Odśwież, Powiększ czcionkę*) oraz osobny przycisk tradycyjnej przeglądarki.
- **Gry Offline**: Wbudowane skróty do pasjansa (`aisleriot`) i mahjonga (`gnome-mahjongg`).
- **Obsługa Drukarek HP**: Skrót sprawdzający status i drukujący stronę testową na starych drukarkach HP via CUPS / HPLIP.

### 3. 📱 Zaawansowane Przesyłanie Zdjęć z Telefonu na Dysk Zewnętrzny
- **Automatyczne wykrywanie**: Wykrywa podłączony telefon przez MTP (`/run/user/<UID>/gvfs/mtp*`) oraz zewnętrzny dysk HDD (`/media/dziadek/*`).
- **Wskaźnik pojemności dysku**: Pasek wolnego miejsca na dysku HDD z kolorowymi strefami (zielony >20%, bursztynowy 10-20%, czerwony <10%).
- **Dedykowane przyciski akcji**:
  - *"Skopiuj zdjęcia z WhatsApp na dysk"*
  - *"Skopiuj filmy z WhatsApp na dysk"*
  - *"Skopiuj zdjęcia z aparatu (DCIM) na dysk"*
  - *"Skopiuj filmy z aparatu (DCIM) na dysk"*
- **Przełącznik bezpiecznego kopiowania**: Przycisk *"Zostaw w telefonie"* vs *"Usuń z telefonu po skopiowaniu"* (domyślnie zostawia w telefonie).
- **Przycisk Awaryjny**: *"Poproś wnuka o pomoc"* z wyświetlaniem danych kontaktowych i identyfikatora pulpitu zdalnego.

### 4. 🔄 Automatyczny Cichy Self-Update z GitHub
- Usługa `systemd` w tle (`senior-mint-updater.timer`), która co określony czas pobiera aktualizacje z GitHub (`git pull --ff-only`).
- Weryfikacja składni Python (`py_compile`) – w przypadku błędu system automatycznie wycofuje zmiany (`git reset --hard ORIG_HEAD`).

---

## 🧪 Testy i Weryfikacja

Wszystkie moduły zostały przetestowane automatycznie przy użyciu `pytest`:

```bash
python -m pytest
```

Wynik testów: **136 passed, 0 failed**.

---

## 📁 Struktura Repozytorium

```text
.
├── install.sh                     # Skrypt instalacyjny dla konta root
├── main.py                        # Punkt wejścia aplikacji pulpitu
├── README.md                      # Dokumentacja projektu
├── PROJECT.md                     # Specyfikacja techniczna i kamienie milowe
├── senior_mint_dashboard/         # Pakiet aplikacji Python
│   ├── config.py                  # Ścieżki i konfiguracje
│   ├── launcher/                  # Pulpit PyQt6, widgety, gry i webview
│   ├── media_transfer/            # Autodetekcja MTP, kopiowanie zdjęć i interfejs
│   └── updater/                   # Usługa automatycznych aktualizacji systemd/git
└── tests/                         # Kompletny zestaw 136 testów automatycznych
```
