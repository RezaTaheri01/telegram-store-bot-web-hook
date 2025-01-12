
# Telegram Bot with Django Integration Web Hook 📢💻  

A Python-based Telegram bot integrated with a Django backend, featuring webhook support with Uvicorn and serve as a digital store.  
This code is base on [telegram-store-bot](https://github.com/RezaTaheri01/telegram-store-bot) but webhook version, the main functionalities didn't change.

---

## Features 🛠️  

- **Webhook Integration**: Efficient updates handling with Uvicorn. 🌐  
- **Multi-language Support**: Easily customizable in `bot_settings.py`. 🌍  
- **User Management**: Automatic account creation, balance display, and transaction history. 💳  
- **Payments**: Generate payment links and update balances after successful payments. ✔️  
- **Products**: Dynamic categories, product listings, and purchases via user balance. 🛒  

---

## Setup 🚀  

1. **Clone the Repository**:  
   ```bash
   git clone --branch single-run https://github.com/RezaTaheri01/telegram-store-bot-web-hook.git
   cd telegram-store-bot-web-hook/telegram_store
   ```

2. **Install Dependencies**:  
   ```bash
   pip install -r req.txt
   ```

3. **Configure the `.env` File**:  
   Create a `.env` file in the project root and populate it with the following sample values:  
   ```env
   TOKEN=your-telegram-api-token
   ADMIN_CHAT_ID=123456789
   SECRET_KEY=your-django-secret-key
   ENCRYPTION_KEYS=your-encryption-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
   WEBHOOK_URL=https://your-domain.com
   WEBHOOK_PORT=8001
   PAYMENT_DOMAIN=https://your-domain.com
   USE_SQLITE=False
   # If USE_SQLITE=False complete below
   PASS_DB=<db-password>
   USER_DB=<db-user>
   HOST_DB=<db-host>
   NAME_DB=<db-name>
   PORT_DB=<db-port>
   ```

   **Note**: Replace placeholder values with your actual credentials. If using localhost, use a tunneling tool (e.g., Ngrok or Cloudflare Tunnel) for `WEBHOOK_URL` and `PAYMENT_DOMAIN`.  

4. **Run Migrations** Already done for sqlite3!:<br>
   **Attention**: If you what to use below commands first comment bot_module/app.py ready function.
   ```bash
   python manage.py makemigrations users payment products
   python manage.py migrate
   python manage.py createsuperuser
   ```

   **Superuser** username and password:
   ```
   username: admin
   password: admin1234
   ```

6. **Start Servers**:  
     ```bash
     uvicorn telegram_store.asgi:application --host 0.0.0.0 --port 8000
     ```

     This command also run webserver on 127.0.0.1:<PORT that define on .env>

---

## Usage 💬  

1. Start the bot and send `/start`.  
2. Access features like **My Account**, **Deposit**, and **Product Categories**.  
3. Use payment links to recharge and purchase products.  

---

## Notes 📝  

- Ensure HTTPS support for webhooks and backend (use a tunneling tool for localhost).  
- Update `WEBHOOK_URL` and `PAYMENT_DOMAIN` for production deployment.  

--- 
