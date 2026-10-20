import math
import time
import traceback

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


# Dicari hanya di footer chat, agar tidak memilih kotak pencarian.
COMPOSER_SELECTORS = (
    '#main footer [contenteditable="true"][role="textbox"]',
    '#main footer [contenteditable="true"]',
)


def find_composer(driver):
    for selector in COMPOSER_SELECTORS:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if element.is_displayed() and element.is_enabled():
                    return element
            except StaleElementReferenceException:
                continue
    return False


def composer_is_empty(driver):
    try:
        element = find_composer(driver)
        if not element:
            return False
        text = element.get_attribute("textContent") or ""
        return not text.replace("\u200b", "").strip()
    except StaleElementReferenceException:
        return False


def ask_count():
    while True:
        try:
            value = int(input("Jumlah pesan [Enter = 1]: ").strip() or "1")
            if value >= 1:
                return value
        except ValueError:
            pass
        print("Masukkan bilangan bulat minimal 1.")


def ask_gap():
    while True:
        try:
            value = float(
                input("Jeda dalam detik [Enter = 3]: ").strip() or "3"
            )
            if math.isfinite(value) and value >= 0:
                return value
        except ValueError:
            pass
        print("Masukkan angka yang valid, minimal 0.")


def main():
    driver = None
    stage = "membuka Chrome"

    try:
        print("[1] Membuka Chrome...", flush=True)

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=options)

        stage = "membuka WhatsApp Web"
        print("[2] Membuka WhatsApp Web...", flush=True)
        driver.get("https://web.whatsapp.com/")

        print(
            "\nDi browser yang baru terbuka:\n"
            "1. Scan QR untuk login jika diminta.\n"
            "2. Buka kontak atau grup tujuan.\n"
            "3. Pastikan kotak penulisan pesan terlihat dan kosong."
        )
        input("\nSetelah selesai, kembali ke terminal dan tekan Enter: ")

        stage = "menemukan kotak pesan"
        wait = WebDriverWait(driver, 30)
        wait.until(find_composer)

        if not composer_is_empty(driver):
            raise RuntimeError(
                "Ada draft di kotak pesan. Kosongkan dahulu, "
                "kemudian jalankan ulang skrip."
            )

        message = input("Isi pesan (satu baris): ")
        if not message.strip():
            print("Pesan kosong. Proses dibatalkan.")
            return

        count = ask_count()
        gap = ask_gap()
        add_status = (
            input("Tambahkan nomor status? (y/N): ").strip().lower() == "y"
        )

        print(f"\nAkan mengirim {count} pesan ke chat yang sedang terbuka.")
        confirmation = input(
            "Periksa penerima di browser. Ketik KIRIM untuk mulai: "
        )
        if confirmation.strip() != "KIRIM":
            print("Pengiriman dibatalkan.")
            return

        for index in range(1, count + 1):
            stage = f"mengirim pesan {index}/{count}"

            box = wait.until(find_composer)
            if not composer_is_empty(driver):
                raise RuntimeError(
                    "Kotak pesan tidak kosong. Pengiriman dihentikan "
                    "agar tidak menambahkan pesan ke draft."
                )

            text = (
                f"<Status: {index}/{count}> {message}"
                if add_status
                else message
            )

            box.click()
            box.send_keys(text)
            box.send_keys(Keys.ENTER)

            # Composer kosong bukan bukti pesan diterima penerima.
            # Jika timeout, tidak mencoba ulang untuk menghindari duplikat.
            wait.until(composer_is_empty)
            print(f"[OK] Pesan {index}/{count} keluar dari kotak pesan.")

            if index < count:
                time.sleep(gap)

        print("\nSelesai. Periksa tanda status pesan di WhatsApp.")

    except KeyboardInterrupt:
        print("\nDihentikan oleh pengguna.")

    except Exception:
        print(f"\nGAGAL pada tahap: {stage}")
        traceback.print_exc()

    finally:
        try:
            input("\nTekan Enter untuk menutup program dan browser...")
        except (EOFError, KeyboardInterrupt):
            pass

        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()