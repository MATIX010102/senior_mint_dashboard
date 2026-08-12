# Propozycja Integracji Zdalnego Zarządzania (Remote Management Proposal)

Niniejszy dokument przedstawia cztery opcje wdrożenia stabilnego, bezpiecznego i prostego w obsłudze zdalnego zarządzania komputerem Dziadka (HP 15t-r100, Linux Mint XFCE), który najpewniej znajduje się za domowym ruterem (brak publicznego IP / NAT).

---

## Opcja 1: Headless RustDesk Daemon + Integracja z Dashboardem (Rekomendowana)

RustDesk to otwartoźródłowe oprogramowanie typu pulpitu zdalnego (alternatywa dla TeamViewer/AnyDesk). Działa bez konieczności przekierowywania portów.

### Metoda Wdrożenia:
1. **Instalacja Daemona**:
   Instalacja systemowa RustDesk poprzez pakiet `.deb` i uruchomienie usługi systemowej w tle:
   ```bash
   sudo apt-get install -y ./rustdesk-1.2.3-x86_64.deb
   sudo systemctl enable rustdesk --now
   ```
2. **Pobieranie ID i Statusu**:
   RustDesk przechowuje konfigurację i identyfikator ID w pliku `/etc/rustdesk/rustdesk.toml` lub generuje go dynamicznie w logach. Możemy napisać prosty skrypt w Pythonie (w `senior_mint_dashboard/media_transfer/detector.py`), który przy otwarciu okna "Zdalna Pomoc" odczyta ID za pomocą polecenia:
   ```bash
   rustdesk --get-id
   ```
   oraz sprawdzi status połączenia z serwerem RustDesk.
3. **Prezentacja w Dashboardzie**:
   Zamiast statycznego tekstu, okienko "Zdalna Pomoc" wyświetli rzeczywiste wygenerowane ID oraz zieloną kropkę "Połączono z serwerem pomocy".

### Zalety:
* Bezproblemowe działanie za NAT.
* Możliwość postawienia własnego, prywatnego serwera RustDesk u Wnuka dla pełnego bezpieczeństwa.
* Senior nie musi nic klikać ani akceptować – usługa w tle pozwala na bezpośrednie połączenie z hasłem stałym.

---

## Opcja 2: Prywatna Sieć Tailscale (VPN) + Szyfrowany VNC / SSH

Tailscale tworzy bezpieczną sieć typu mesh (SDN) pomiędzy komputerem Dziadka a komputerem Wnuka.

### Metoda Wdrożenia:
1. **Instalacja Tailscale**:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up --authkey=tskey-auth-... # Autoryzacja jednorazowym kluczem instalacyjnym
   ```
2. **Uruchomienie serwera VNC i SSH**:
   Serwer VNC (np. `x11vnc` lub domyślny w Mint) jest skonfigurowany tak, aby nasłuchiwał **wyłącznie** na interfejsie VPN Tailscale (np. na adresie IP z puli `100.x.y.z`).
3. **Zdalna sesja**:
   Wnuk łączy się bezpośrednio poprzez Tailscale za pomocą SSH lub klienta VNC:
   ```bash
   ssh dziadek@100.x.y.z
   vncviewer 100.x.y.z:0
   ```

### Zalety:
* Maksymalne bezpieczeństwo – porty VNC/SSH nie są widoczne w internecie, dostęp ma wyłącznie Wnuk.
* Bardzo niskie zużycie zasobów (WireGuard w jądrze systemu).
* Brak wpływu na interfejs użytkownika Dziadka.

---

## Opcja 3: Automatyczny Tunel Reverse SSH (Systemd Service)

Rozwiązanie całkowicie bezkosztowe i lekkie. Komputer Dziadka sam zestawia połączenie SSH z serwerem Wnuka i wystawia swój port SSH/VNC na serwerze Wnuka.

### Metoda Wdrożenia:
1. Skonfigurowanie bezhasłowego logowania kluczem SSH z konta `dziadek` na serwer Wnuka.
2. Dodanie usługi systemd `~/.config/systemd/user/reverse-ssh.service` na komputerze Dziadka:
   ```ini
   [Unit]
   Description=Reverse SSH Tunnel for Remote Management
   After=network-online.target

   [Service]
   ExecStart=/usr/bin/ssh -N -R 2222:localhost:22 -R 5900:localhost:5900 wnuk@serwer-wnuka.pl
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=default.target
   ```
3. Wnuk loguje się na swój serwer, a stamtąd łączy się z portem `2222` na localhost, aby sterować komputerem Dziadka:
   ```bash
   ssh -p 2222 dziadek@localhost
   ```

### Zalety:
* Brak dodatkowych zewnętrznych usług (tylko standardowe SSH).
* Skrajnie niskie zużycie RAM i CPU.

---

## Opcja 4: noVNC + Cloudflare Tunnel (Zarządzanie przez Przeglądarkę)

Cloudflare Tunnels pozwala na bezpieczne wystawienie lokalnej usługi na zewnątrz pod dedykowaną domeną, z opcjonalnym uwierzytelnieniem Google/GitHub na poziomie Cloudflare.

### Metoda Wdrożenia:
1. Uruchomienie serwera `x11vnc` oraz serwera webowego `noVNC` (który renderuje ekran w HTML5/WebSockets).
2. Zainstalowanie demona `cloudflared` i skonfigurowanie tunelu kierującego domenę `pomoc.wnuk.pl` na lokalny port noVNC.
3. Wnuk wchodzi na stronę `https://pomoc.wnuk.pl`, loguje się przez logowanie Google (Cloudflare Access), po czym otrzymuje pełny pulpit Dziadka bezpośrednio w przeglądarce (nawet na telefonie!).

### Zalety:
* Wnuk nie musi instalować żadnych programów klienckich – wystarczy przeglądarka internetowa.
* Ochrona domeny silnym uwierzytelnieniem Cloudflare.

---

## Rekomendowany Krok w Przód:

Dla uproszczenia zalecamy **Opcję 1 (RustDesk)**:
1. W kolejnej iteracji możemy zmienić przycisk "Zdalna Pomoc", tak aby zamiast statycznego okna dialogowego wywoływał skrypt pobierający ID z działającej w tle usługi RustDesk:
   ```python
   # W media_transfer/ui/help_dialog.py (lub transfer_window.py):
   # Pobranie ID za pomocą polecenia `rustdesk --get-id` i wstawienie do okienka.
   ```
2. Dziadek po prostu klika "Zdalna Pomoc" i czyta wnukowi ID widoczne na dużym ekranie, bądź wnuk łączy się bezpośrednio bez pytania, jeśli skonfigurowano hasło stałe.
