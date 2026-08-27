import os
import csv
import requests
from bs4 import BeautifulSoup

# Recupera i Secret configurati su GitHub
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

CSV_FILE = "eventi_registrati.csv"

def send_telegram_message(message):
    """Invia un messaggio Telegram usando la formattazione HTML (sicura e stabile)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Errore: Token o Chat ID non configurati nei Secrets di GitHub.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(url, json=payload)
        res_data = response.json()
        if not res_data.get("ok"):
            print(f"Errore Telegram API: {res_data}")
        else:
            print("Notifica inviata con successo!")
    except Exception as e:
        print(f"Errore durante l'invio a Telegram: {e}")

def load_seen_events():
    """Carica gli URL degli eventi già notificati per evitare duplicati."""
    seen = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    seen.add(row[0])
    return seen

def save_seen_event(link, title, date_str):
    """Salva un nuovo evento nel file CSV per lo storico."""
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["link", "titolo", "data_rilevamento"])
        writer.writerow([link, title, date_str])

def run():
    print("Avvio ricerca sagre ed eventi Provincia di La Spezia...")
    seen_events = load_seen_events()
    
    # URL di ricerca per eventi e sagre nella provincia della Spezia
    url = "https://www.cittadellaspezia.com/tag/sagre/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Errore nella richiesta HTTP: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Estrazione articoli ed eventi
    articles = soup.find_all("article")
    new_events = []
    
    for article in articles:
        title_tag = article.find("h2") or article.find("h3") or article.find("a")
        if not title_tag:
            continue
            
        link_tag = article.find("a")
        if not link_tag or not link_tag.get("href"):
            continue
            
        link = link_tag["href"]
        title = title_tag.get_text(strip=True)
        
        if link not in seen_events:
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_events.append({
                "link": link,
                "titolo": title,
                "data_rilevamento": today_str
            })

    if not new_events:
        print("Nessun nuovo evento trovato rispetto all'ultima scansione.")
        return

    print(f"Trovati {len(new_events)} nuovi eventi!")

    for event in new_events:
        msg = (
            f"🚨 <b>NUOVA SAGRA / EVENTO RILEVATO</b> 🚨\n\n"
            f"📌 <b>Titolo:</b> {event['titolo']}\n"
            f"🔗 <b>Link:</b> <a href=\"{event['link']}\">Leggi Notizia su Città della Spezia</a>\n"
            f"📅 <b>Rilevato il:</b> {event['data_rilevamento']}\n\n"
            f"💡 <i>Azione HORECA: Contattare la Pro Loco o il Comitato Organizzatore.</i>"
        )
        
        send_telegram_message(msg)
        save_seen_event(event["link"], event["titolo"], event["data_rilevamento"])
        print(f"Notifica inviata per: {event['titolo']}")

if __name__ == "__main__":
    run()
