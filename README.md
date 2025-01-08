# Telegram Bot with Django Integration 📢💻 Web Hook Version

This bot is a Python-based Telegram bot seamlessly integrated with a Django backend. It supports database management, payment handling, digital product selling, and dynamic user interactions.

---

## Features 🏢

### Telegram Bot 📲

- **Multi-language Support**:

  - Currently supports three languages, with the ability to add more.(There is a help comment in bot_settings.py)
  - Users can change the language via the main menu.

- **User Account Management**:

  - Automatically creates user accounts if they don’t exist.
  - Retrieves and displays user balance. 💳
  - Displays user transaction history. 🔄

- **Interactive Menu**:

  - Provides options like **My Account**, **My Balance**, **Deposit**, and **Product Categories**.
  - Includes inline keyboards for seamless navigation. 📝

- **Payment Handling**:

  - Generates unique payment links. 📡
  - Processes payments via the Django backend.
  - Updates user balance upon successful payment. ✔️

- **Product Management**:

  - Dynamically displays categories and products. 🛒
  - Supports product purchases via balance deduction. 💸

- **Customization**:
  - In `bot_settings.py`, you can customize:
    - Number of categories and products displayed per row.
    - All text messages. 🖊️
    - Primary and secondary languages.
    - Inline button text and callback data.
    - Payment link time limits. ⏳

### Django Backend 📚

- **Database Models**:

  - `UserData`: Manages user account information. By default, the language is set to English (`en`). If your primary language isn’t English, update this in `bot_settings.py` and the database model.
  - `Transaction`: Tracks payment transactions. 📋
  - `Category`, `Product`, `ProductDetail`: Manages products and their details. 🛠️
  - `ProductDetail`: The field detail that contain product info is encrypted 🔒 by ([django-encrypted-json-fields](https://pypi.org/project/django-encrypted-json-fields/))

- **Payment Processing**:
  - Dynamically creates payment links. 🔗
  - Updates the database after payment confirmation.

---

## Installation ⚙️

### Prerequisites 🔎

0. Need a domain that supports https
1. Python 3.8 or higher 💾
2. Django (latest version recommended) ⬆️
3. PostgreSQL or any preferred database system configured in Django ([Learn More](https://docs.djangoproject.com/en/5.1/ref/databases/))
4. Required libraries: `python-telegram-bot`, `asgiref`, `python-decouple`, etc.
5. Dependencies are listed in `req.txt`

### Setup Instructions 🔧

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/RezaTaheri01/telegram-store-bot.git
   ```

   ```bash
   cd telegram-store-bot/telegram_store
   ```

2. **Install Dependencies**([virtual environment](https://realpython.com/python-virtual-environments-a-primer/#create-it) recommended):

   ```bash
   pip install -r req.txt
   ```

3. **Configure Django Settings**:

   - Set the `telegram_store.settings` module:
     - Change `EJF_ENCRYPTION_KEYS` and `SECRET_KEY`
   - Configure your database in `settings.py`.

4. **Set Up Environment Variables**:

   - Create a `.env` file in the root directory with the following structure:
     ```env
     TOKEN_WEB=<your-telegram-bot-token>
     ```

5. **Migrate the Database** and **Create Super User**:

   ```bash
   python manage.py makemigrations payment users products
   ```

   ```bash
   python manage.py migrate
   ```

   ```bash
   python manage.py createsuperuser
   ```

6. Add your domain to **TELEGRAM_WEBHOOK_URL** in settings.py:

   ```bash
   python manage.py set_webhook --action set
   ```

7. **Run the Django Development Server**:

   ```bash
   python manage.py runserver
   ```

8. **Run the Telegram Bot**:
   ```bash
   python bot.py
   ```

---

## Code Overview 🛠️

### Telegram Bot 📲

#### Key Features

- **Imports**:

  - `Django`: Sets up the Django environment for database operations.
  - `telegram.ext`: Facilitates bot creation and updates handling.

- **Global Variables**:

  - `main_menu_keys`: Defines the main menu layout.
  - `textStart`, `textBalance`, etc.: Predefined messages for user interactions.

- **Core Functions**:
  - `start_menu`: Displays the main menu. 🌐
  - `change_language`: Allows users to change their language and updates the `UserData` language field. 🌎
  - `check_create_account`: Automatically creates user accounts if they don’t exist. 🔧
  - `user_balance`: Fetches and displays the user’s balance. 💳
  - `deposit_money`: Initiates the deposit process and generates payment links. 💵
  - `charge_account`: Updates the user’s balance upon successful payment. ✔️
  - `get_name`: Retrieves names based on user language. 🌐
  - `product_categories`: Dynamically displays product categories. 🛒
  - `products`: Lists products under a selected category. 🍾
  - `product_payment_detail`: Displays payment details for a product. 💸
  - `payment`: Handles product purchases and balance deductions. 💰
  - `get_user_language`: Retrieves the user’s language from a language cache or the database. 🌐

#### Conversation States

- `ENTER_AMOUNT`: Captures the deposit amount entered by the user. 💵

#### Error Handling 🛠️

- Logs all errors to `logs.log`.
- Notifies users of issues without disrupting the bot experience. ⚠️

---

### Payment Link Workflow 🔗

- **Link Format**:
  ```
  http://127.0.0.1:8000/payment/confirm/?chat_id={chat_id}&user_id={user_id}&amount={amount}&bot_link={bot_link}&transaction={transaction}
  ```
- Redirects users to a Django view for payment processing.

---

## Usage 🚀

1. **Start the Bot**:

   - Send `/start` to the bot. 📢
   - Explore options like **My Account**, **My Balance**, **Deposit**, or **Product Categories**.

2. **Deposit Money**:

   - Select the **Deposit** option from the menu. 💵
   - Enter the desired amount.
   - Click the payment link to complete the transaction. ✔️
   - Verify the updated balance in your account. 💳

3. **Browse Products**:
   - Select **Product Categories** from the menu. 🛒
   - Choose a category and view available products. 🍾
   - Purchase a product using your balance. 💰

---

## Logs 🔍

- All errors are logged in `logs.log` with detailed messages. 📄

---

## Notes 📊

- Ensure the Django server is running for smooth payment processing. ⚙️
- Update the `payment_url` in the bot code to match your server’s address when deploying. 🔗

---

## License 🔒

This project is licensed under the MIT License. See the [`LICENSE`](https://github.com/RezaTaheri01/telegram-store-bot/blob/main/LICENSE) file for more details. 🔖
