# cloudflared-windows-amd64.exe tunnel --url http://localhost:8000
# standalone Django app for webhook
# !/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.
# pylint: disable=import-error,unused-argument
# to check if webhook set correctly:
# https://api.telegram.org/bot<your-bot-token>/getWebhookInfo

"""
Simple example of a bot that uses a custom webhook setup and handles custom updates.
For the custom webhook setup, the libraries `Django` and `uvicorn` are used. Please
install them as `pip install Django~=4.2.4 uvicorn~=0.23.2`.
Note that any other `asyncio` based web server framework can be used for a custom webhook setup
just as well.

Usage:
Set bot Token, URL, admin CHAT_ID and PORT after the imports.
You may also need to change the `listen` value in the uvicorn configuration to match your setup.
Press Ctrl-C on the command line or send a signal to the process to stop the bot.
"""
import threading
from uuid import uuid4

from bot_settings import *
from asgiref.sync import sync_to_async
from django.utils import timezone
from decouple import config

import asyncio
import html
import json
import uvicorn
from dataclasses import dataclass

# region Django Imports

import django
from telegram_store import settings as main_settings
from django.conf import settings
from django.urls import path

from django.views.decorators.csrf import csrf_exempt
from django.core.asgi import get_asgi_application
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest

settings.configure(
    SECRET_KEY=uuid4().hex,
    ROOT_URLCONF=__name__,
    DEBUG=config('DEBUG_WEBHOOK', default=False, cast=bool),
    ALLOWED_HOSTS=config('ALLOWED_HOSTS_WEBHOOK', default='').split(','),
    DATABASES=main_settings.DATABASES,
    INSTALLED_APPS=main_settings.INSTALLED_APPS,
    LANGUAGES=main_settings.LANGUAGES,
    MIDDLEWARE=main_settings.MIDDLEWARE,
    EJF_ENCRYPTION_KEYS=main_settings.EJF_ENCRYPTION_KEYS,
)

django.setup()

from users.models import UserData
from payment.models import Transactions
from products.models import Category, Product, ProductDetail

# endregion


# region Telegram Imports

from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ContextTypes,
    ExtBot
)

# endregion


# region logging

import logging

# Enable logging
logging.basicConfig(
    filename="webhook_bot.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# endregion


# region Global Variables

# Define configuration constants
URL = config('WEBHOOK_URL', default=f'http://127.0.0.1')
ADMIN_CHAT_ID = config("ADMIN_CHAT_ID")
PORT = int(config('WEBHOOK_PORT', default='8000'))
TOKEN = config("TOKEN")

# Define states
ENTER_AMOUNT = 1

bot_username = ""

# # Todo: implement aging for better memory usage
language_cache: dict = {}


# endregion


# region Menu

async def start_menu(update: Update, context: CallbackContext) -> None:  # active command is /start
    usr_lng = await user_language(update.effective_user.id)
    full_name = f"{update.effective_user.first_name or ''} {update.effective_user.last_name or ''}".strip()
    try:
        await check_create_account(update)  # Create a user if not exist
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=texts[usr_lng]["textStart"].format(full_name),
            reply_markup=buttons[usr_lng]["main_menu_markup"],
        )
        await update.message.delete()
    except Exception as e:
        await error_message(update=update, usr_lng=usr_lng)
        logger.error(f"Error in start_menu function: {e}")


async def menu_from_callback(query: CallbackQuery) -> None:
    usr_lng = await user_language(query.from_user.id)
    try:
        await query.edit_message_text(
            text=texts[usr_lng]["textMenu"],
            reply_markup=buttons[usr_lng]["main_menu_markup"],
        )
    except Exception as e:
        await error_message(query=query, usr_lng=usr_lng)
        logger.error(f"Error in menu_from_callback function: {e}")


# endregion


# region Balance

async def user_balance(update: Update, context: CallbackContext) -> None:
    balance = 0  # Default balance
    usr_lng = await user_language(update.effective_user.id)
    try:
        current_user = await sync_to_async(UserData.objects.filter(id=update.effective_user.id).first,
                                           thread_sensitive=True)()

        if not current_user:
            await check_create_account(update)
        else:
            balance = current_user.balance

        await update.message.reply_text(
            text=texts[usr_lng]["textBalance"].format(
                balance, texts[usr_lng]["textPriceUnit"]),
            reply_markup=buttons[usr_lng]["back_menu_markup"])
        await update.message.delete()
    except Exception as e:
        await error_message(update=update, usr_lng=usr_lng)
        logger.error(f"Error in user_balance function: {e}")


async def user_balance_from_call_back(update: Update, query: CallbackQuery) -> None:
    balance = 0  # Default balance
    usr_lng = await user_language(update.effective_user.id)
    try:
        current_user = await sync_to_async(UserData.objects.filter(id=query.from_user.id).first,
                                           thread_sensitive=True)()

        if not current_user:
            await check_create_account(update)
        else:
            balance = current_user.balance

        await query.edit_message_text(
            text=texts[usr_lng]["textBalance"].format(balance, texts[usr_lng]["textPriceUnit"]),
            reply_markup=buttons[usr_lng]["back_menu_markup"])
    except Exception as e:
        await error_message(query=query, usr_lng=usr_lng)
        logger.error(f"Error in user_balance_from_call_back function: {e}")


# endregion


# Todo: function that return purchased products with pagination
# region Manage account
async def account_menu_call_back(query: CallbackQuery):
    usr_lng = await user_language(query.from_user.id)
    full_name = f"{query.from_user.first_name or ''} {query.from_user.last_name or ''}".strip()
    try:
        await query.edit_message_text(
            text=texts[usr_lng]["textAccountMenu"].format(full_name),
            reply_markup=buttons[usr_lng]["account_keys_markup"],
        )
    except Exception as e:
        await error_message(query=query, usr_lng=usr_lng)
        logger.error(f"Error in menu_from_callback function: {e}")


async def account_info(query: CallbackQuery) -> None:
    user_id = query.from_user.id
    user_data = await sync_to_async(UserData.objects.filter(id=user_id).first, thread_sensitive=True)()
    usr_lng = await user_language(user_id)

    if not user_data:
        await query.edit_message_text(text=texts[usr_lng]["textNotUser"],
                                      reply_markup=buttons[usr_lng]["back_to_acc_markup"])
        return

    await query.edit_message_text(text=texts[usr_lng]["textAccInfo"].format(
        user_data.username,
        (user_data.first_name or "") + " " + (user_data.last_name or ""),
        user_data.balance,
        texts[usr_lng]["textPriceUnit"]),
        reply_markup=buttons[usr_lng]["back_to_acc_markup"])


# Todo: get user current time(24h format) and save the difference in database
async def account_transactions(query: CallbackQuery) -> None:
    user_id = query.from_user.id
    usr_lng = await user_language(user_id)

    try:
        temp: list = query.data.split('_')
        if len(temp) == 1:
            start_index = 0
        else:
            # Extract start index from callback data
            start_index: int = int(query.data.split('_')[1])
            if start_index < 0:
                return

    except (IndexError, ValueError):
        await query.answer(texts[usr_lng]["textNotFound"], show_alert=True)
        return

    try:
        # Fetch transactions and total count
        user_transaction: list = await sync_to_async(
            lambda: list(
                Transactions.objects.filter(user_id=user_id, is_paid=True)
                .order_by('-paid_time')[start_index:start_index + number_of_transaction]
            ), thread_sensitive=True
        )()
        total_transactions = await sync_to_async(
            lambda: Transactions.objects.filter(user_id=user_id, is_paid=True).count()
        )()

        if not user_transaction:
            if start_index == 0:
                await query.edit_message_text(
                    text=texts[usr_lng]["textNoTransaction"],
                    reply_markup=buttons[usr_lng]["back_to_acc_markup"]
                )
            return

        # Calculate page info
        current_page = start_index // number_of_transaction + 1
        total_pages = (total_transactions + number_of_transaction - 1) // number_of_transaction

        # Page number
        result_data = texts[usr_lng]["textTransaction"].format(f"{current_page}/{total_pages}")
        result_data += "\n\n"
        for t in user_transaction:
            # Format paid_time using strftime
            formatted_time = t.paid_time.strftime("%Y-%m-%d %H:%M:%S")
            result_data += t.transaction_code + "\n" + texts[usr_lng]["textTransactionDetail"].format(
                t.amount,
                texts[usr_lng]["textPriceUnit"],
                formatted_time + " " + time_zone
            )

        # Pagination buttons
        transactions_keys = []

        # Add "Previous" button only if there is a previous page
        if start_index > 0:
            transactions_keys.append(
                InlineKeyboardButton(
                    texts[usr_lng]["textPrev"],
                    callback_data=f"{transactions_cb}_{start_index - number_of_transaction}"
                )
            )

        # Add "Next" button only if there is a next page
        if start_index + number_of_transaction < total_transactions:
            transactions_keys.append(
                InlineKeyboardButton(
                    texts[usr_lng]["textNext"],
                    callback_data=f"{transactions_cb}_{start_index + number_of_transaction}"
                )
            )

        # Add buttons for account and main menu navigation
        navigation_buttons = [
            [InlineKeyboardButton(texts[usr_lng]["buttonAccount"], callback_data=account_menu_cb)],
            [InlineKeyboardButton(texts[usr_lng]["buttonBackMainMenu"], callback_data=main_menu_cb)]
        ]

        # Combine all buttons
        if transactions_keys:
            transactions_markup = InlineKeyboardMarkup([transactions_keys] + navigation_buttons)
        else:
            transactions_markup = InlineKeyboardMarkup(navigation_buttons)

        await query.edit_message_text(text=result_data, reply_markup=transactions_markup)

    except Exception as e:
        logger.error(f"Error in account_info function: {e}")


async def user_purchase_products(query: CallbackQuery) -> None:
    user_id = query.from_user.id
    usr_lng = await user_language(user_id)

    try:
        temp: list = query.data.split('_')
        if len(temp) == 1:
            start_index = 0
        else:
            # Extract start index from callback data
            start_index: int = int(query.data.split('_')[1])
            if start_index < 0:
                return

    except (IndexError, ValueError):
        await query.answer(texts[usr_lng]["textNotFound"], show_alert=True)
        return

    try:
        # Fetch transactions and total count
        user_products: list = await sync_to_async(
            lambda: list(
                ProductDetail.objects.filter(is_purchased=True, buyer__id=user_id, is_delete=False)
                .order_by('-purchase_date').select_related('product')[start_index:start_index + number_of_products]
            ), thread_sensitive=True
        )()
        total_purchase = await sync_to_async(
            lambda: ProductDetail.objects.filter(is_purchased=True, buyer__id=user_id, is_delete=False).count()
        )()

        if not user_products:
            if start_index == 0:
                await query.edit_message_text(
                    text=texts[usr_lng]["textNotFound"],
                    reply_markup=buttons[usr_lng]["back_to_acc_markup"]
                )
            return

        # Calculate page info
        current_page = start_index // number_of_products + 1
        total_pages = (total_purchase + number_of_products - 1) // number_of_products

        # Page number
        result_data = texts[usr_lng]["textProducts"].format(f'{current_page}/{total_pages}')
        result_data += "\n\n"
        for p in user_products:
            product_name = await get_name(usr_lng, p.product)
            # Format paid_time using strftime
            formatted_time = p.purchase_date.strftime("%Y-%m-%d %H:%M:%S")
            result_data += texts[usr_lng]["textProductDetailList"].format(
                product_name,
                formatted_time + " " + time_zone,
                p.details,
            )

        # Pagination buttons
        products_keys = []

        # Add "Previous" button only if there is a previous page
        if start_index > 0:
            products_keys.append(
                InlineKeyboardButton(
                    texts[usr_lng]["textPrev"],
                    callback_data=f"{purchase_products_cb}_{start_index - number_of_products}"
                )
            )

        # Add "Next" button only if there is a next page
        if start_index + number_of_products < total_purchase:
            products_keys.append(
                InlineKeyboardButton(
                    texts[usr_lng]["textNext"],
                    callback_data=f"{purchase_products_cb}_{start_index + number_of_products}"
                )
            )

        # Add buttons for account and main menu navigation
        navigation_buttons = [
            [InlineKeyboardButton(texts[usr_lng]["buttonAccount"], callback_data=account_menu_cb)],
            [InlineKeyboardButton(texts[usr_lng]["buttonBackMainMenu"], callback_data=main_menu_cb)]
        ]

        # Combine all buttons
        if products_keys:
            products_markup = InlineKeyboardMarkup([products_keys] + navigation_buttons)
        else:
            products_markup = InlineKeyboardMarkup(navigation_buttons)

        await query.edit_message_text(text=result_data, reply_markup=products_markup)

    except Exception as e:
        logger.error(f"Error in account_info function: {e}")


async def change_user_language(query: CallbackQuery):
    user = await sync_to_async(UserData.objects.filter(id=query.from_user.id).first, thread_sensitive=True)()

    try:
        found = False
        for k in texts.keys():
            if found:
                user.language = k
                found = False
                break
            if k == user.language:
                found = True
        if found:
            user.language = lang1
    except:
        logger.error("can't find next language in change language")
        user.language = lang1

    await sync_to_async(user.save, thread_sensitive=True)()
    language_cache[user.id] = (user.language, timezone.now().date())

    await query.edit_message_text(text=texts[user.language]["textMenu"],
                                  reply_markup=buttons[user.language]['main_menu_markup'])


# endregion


# region ConversationHandler get amount


async def deposit_money(update: Update, context: CallbackContext):
    usr_lng = await user_language(update.effective_user.id)
    await update.message.reply_text(text=texts[usr_lng]["textAmount"],
                                    reply_markup=buttons[usr_lng]["back_menu_markup"])
    await update.message.delete()
    return ENTER_AMOUNT


# Deposit money from CallbackQuery
async def deposit_money_from_callback(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    usr_lng = await user_language(query.from_user.id)
    if query.data != deposit_cb:
        return ConversationHandler.END
    await query.edit_message_text(text=texts[usr_lng]["textAmount"], reply_markup=buttons[usr_lng]["back_menu_markup"])

    return ENTER_AMOUNT


# Todo: pass payment url just a token and on view fetch info from database
async def capture_amount(update: Update, context: CallbackContext):
    global bot_username
    # await context.bot.delete_message(update.effective_chat.id, update.effective_message.id - 1)
    user_input = update.message.text
    user_id = update.effective_user.id
    usr_lng = await user_language(user_id)

    try:
        amount = int(user_input)
        '''
        Todo : redirect to psp then redirect to bot, no need for extra pages.
        Instead of call charge_account, I need to send a link
        to payment page that created by Django and if successful, call charge_account.
        After payment done, a pop up to open telegram app desktop or mobile.
        charge_account update database and send message to telegram
        '''
        chat_id = update.effective_chat.id
        await check_create_account(update)

        # create a new transaction
        transaction = Transactions(user_id=user_id, amount=amount)
        await sync_to_async(transaction.save, thread_sensitive=True)()
        transaction.transaction_code = str(transaction.id + 1_000_000)
        await sync_to_async(transaction.save, thread_sensitive=True)()

        if not bot_username:
            bot_username = context.bot.username
        # print(bot_username)

        pay_key = [[InlineKeyboardButton(text=texts[usr_lng]["textPayButton"], url=payment_url.format(chat_id,
                                                                                                      user_id, amount,
                                                                                                      bot_link.format(
                                                                                                          bot_username),
                                                                                                      transaction.transaction_code))]]

        pay_key_markup = InlineKeyboardMarkup(pay_key)

        await update.message.reply_text(text=texts[usr_lng]["textPaymentLink"],
                                        reply_markup=pay_key_markup)
        # await charge_account(update.effective_user.id, update.effective_chat.id, amount)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(texts[usr_lng]["textInvalidAmount"],
                                        reply_markup=buttons[usr_lng]["back_menu_markup"])
        return ENTER_AMOUNT
    except Exception as e:
        logger.error(f"Error in capture_amount function: {e}")
    finally:
        await update.message.delete()


async def cancel_back_to_menu(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    await query.answer()
    await menu_from_callback(query)
    # print("Ending conversation...")  # Debug log
    return ConversationHandler.END


# endregion


# region Products
async def get_name(user_lang: str, current_object) -> str:
    try:
        current_name = current_object.name  # default is first language "en"
        if user_lang != lang1:  # name_<your language from setting.py>
            current_name = eval(f"current_object.name_{user_lang}")
            if not current_name:
                logger.error(
                    f"name {current_object.name} for language {user_lang} not founded return {current_object.name}")
                return current_object.name
        return current_name
    except:  # return main name field
        logger.error("language not founded return name base on lang1")
        return current_object.name or "None"


async def product_categories(query: CallbackQuery):
    usr_lng = await user_language(query.from_user.id)

    # Fetch categories asynchronously
    categories = await sync_to_async(list, thread_sensitive=True)(Category.objects.all())

    if not categories:
        await query.edit_message_text(text=texts[usr_lng]["textNotFound"],
                                      reply_markup=buttons[usr_lng]["back_menu_markup"])
        return  # Ensure the function exits here if no categories are found
    try:
        # Create buttons for categories
        temp_keys = []
        for i in range(0, len(categories), categories_in_row):
            row = await asyncio.gather(
                *[get_name(usr_lng, cat) for cat in categories[i:i + categories_in_row]]
            )
            temp_keys.append(
                [InlineKeyboardButton(name, callback_data=f"{select_category_cb}_{cat.id}") for name, cat in
                 zip(row, categories[i:i + categories_in_row])]
            )

        temp_keys.append(
            [InlineKeyboardButton(texts[usr_lng]["buttonBackMainMenu"], callback_data=main_menu_cb)])  # Add back button
        temp_reply_markup = InlineKeyboardMarkup(temp_keys)

        await query.edit_message_text(text=texts[usr_lng]["textProductCategories"], reply_markup=temp_reply_markup)
    except Exception as e:
        # await query.edit_message_text(textError, reply_markup=back_menu_markup)
        logger.error(f"Error in payment function: {e}")


# Todo: show available product only
async def products(query: CallbackQuery):
    usr_lng = await user_language(query.from_user.id)
    try:
        # Extract category ID from callback data
        cat_id: int = int(query.data.split('_')[1])
    except (IndexError, ValueError):
        await query.answer(texts[usr_lng]["textInvalidCategory"], show_alert=True)
        return

    # Fetch products asynchronously
    all_products = await sync_to_async(list, thread_sensitive=True)(Product.objects.filter(category__id=cat_id))

    if not all_products:
        await query.edit_message_text(text=texts[usr_lng]["textNoProductFound"],
                                      reply_markup=buttons[usr_lng]["back_to_cats_markup"])
        return

    try:
        # Create buttons for products
        temp_keys = []
        for i in range(0, len(all_products), products_in_row):
            # Gather the product names asynchronously
            names = await asyncio.gather(
                *[get_name(usr_lng, prod) for prod in all_products[i:i + products_in_row]]
            )
            # Create a row of InlineKeyboardButtons
            row = [
                InlineKeyboardButton(name, callback_data=f"{select_product_cb}_{prod.id}")
                for name, prod in zip(names, all_products[i:i + products_in_row])
            ]
            temp_keys.append(row)

        temp_keys.append(
            [InlineKeyboardButton(texts[usr_lng]["buttonBackMainMenu"], callback_data=main_menu_cb)])  # Add back button
        temp_keys.append([InlineKeyboardButton(texts[usr_lng]["textBackButton"], callback_data=categories_cb)])
        temp_reply_markup = InlineKeyboardMarkup(temp_keys)

        # Get category name
        current_cat: Category = await sync_to_async(Category.objects.filter(id=cat_id, is_delete=False).first,
                                                    thread_sensitive=True)()
        cat_name = ""
        if current_cat:
            cat_name = await get_name(usr_lng, current_cat) + " "

        await query.edit_message_text(text=texts[usr_lng]["textProductList"].format(cat_name),
                                      reply_markup=temp_reply_markup)
    except Exception as e:
        # await query.edit_message_text(textError, reply_markup=back_menu_markup)
        logger.error(f"Error in payment function: {e}")


async def product_payment_detail(query: CallbackQuery):
    usr_lng = await user_language(query.from_user.id)

    try:
        # Extract product ID from callback data
        prod_id: int = int(query.data.split('_')[1])
    except (IndexError, ValueError):
        await query.answer(texts[usr_lng]["textInvalidProduct"], show_alert=True)
        return

    # Fetch product asynchronously
    product_detail = await sync_to_async(
        ProductDetail.objects.filter(
            product_id=prod_id, is_purchased=False
        ).select_related('product__category').first, thread_sensitive=True)()

    if not product_detail:
        await query.answer(texts[usr_lng]["textProductSoldOut"], show_alert=True)
        return

    try:
        # Create inline keyboard buttons
        temp_keys = [
            [InlineKeyboardButton(texts[usr_lng]["textPayButton"],
                                  callback_data=f'{payment_cb}_{product_detail.product.price}_{product_detail.product.id}')],
            [InlineKeyboardButton(texts[usr_lng]["textBackButton"],
                                  callback_data=f'{select_category_cb}_{product_detail.product.category.id}')],
        ]
        temp_reply_markup = InlineKeyboardMarkup(temp_keys)

        # Edit message to show product details
        await query.edit_message_text(
            text=texts[usr_lng]["textPurchaseBill"].format(await get_name(usr_lng, product_detail.product),
                                                           product_detail.product.price,
                                                           texts[usr_lng]["textPriceUnit"]),
            reply_markup=temp_reply_markup
        )
    except Exception as e:
        await error_message(query=query, usr_lng=usr_lng)
        await query.answer(texts[usr_lng]["textNotFound"], show_alert=True)
        logger.error(f"Error in product_payment_detail function: {e}")


async def payment(update: Update, context: CallbackContext, query: CallbackQuery):
    usr_lng = await user_language(query.from_user.id)

    try:
        # Extract product ID from callback data
        payment_amount: int = int(query.data.split('_')[1])
        prod_id: int = int(query.data.split('_')[2])
    except (IndexError, ValueError):
        await query.answer(texts[usr_lng]["textInvalidPaymentAmount"], show_alert=True)
        return

    current_user = await sync_to_async(UserData.objects.filter(id=update.effective_user.id).first,
                                       thread_sensitive=True)()

    if not current_user:
        await query.answer(text=texts[usr_lng]["textNotUser"], show_alert=True)
        return
    if current_user.balance < payment_amount:
        await query.answer(text=texts[usr_lng]["textNotEnoughMoney"], show_alert=True)
        return

    product: ProductDetail = await sync_to_async(
        ProductDetail.objects.filter(product_id=prod_id, is_purchased=False).first, thread_sensitive=True)()

    if not product:
        await query.answer(text=texts[usr_lng]["textProductSoldOut"], show_alert=True)
        return

    try:
        current_user.balance -= payment_amount
        product.is_purchased = True
        product.buyer = current_user
        product.purchase_date = timezone.now()

        # first update product detail
        await sync_to_async(product.save, thread_sensitive=True)()
        # then update balance
        await sync_to_async(current_user.save, thread_sensitive=True)()

        await send_message_with_retry(current_bot=context.bot,
                                      chat_id=update.effective_chat.id,
                                      text=texts[usr_lng]["textProductDetail"].format(product.details))
        # await query.delete_message()
    except Exception as e:
        await error_message(update=update, usr_lng=usr_lng)
        logger.error(f"Error in payment function: {e}")


# endregion


# region Common Functions

# # Create a user account if it doesn't exist
async def check_create_account(update: Update) -> None:
    user_id = update.effective_user.id
    usr_lng = await user_language(user_id)
    found: bool = await sync_to_async(UserData.objects.filter(id=user_id).exists, thread_sensitive=True)()

    if not found:
        try:
            first_name = update.effective_user.first_name or None
            last_name = update.effective_user.last_name or None
            username = update.effective_user.username or None

            new_user = UserData(
                id=update.effective_user.id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            await sync_to_async(new_user.save, thread_sensitive=True)()
        except Exception as e:
            await update.message.reply_text(texts[usr_lng]["textError"])
            logger.error(f"Error in check_create_account function: {e}")


async def user_language(user_id: int, cache: bool = True):
    date_now = timezone.now().date()
    if user_id not in language_cache or not cache:
        user = await sync_to_async(UserData.objects.filter(id=user_id).first, thread_sensitive=True)()
        if not user:
            language_cache[user_id] = (lang1, date_now)
            return lang1
        language_cache[user_id] = (user.language, date_now)
        # print(language_cache)
        # print(sys.getsizeof(language_cache))
        return user.language
    else:
        # reset aging
        # language_cache[user_id] = (language_cache[user_id][0], date_now)
        return language_cache[user_id][0]


async def error_message(update: Update = None, query: CallbackQuery = None, usr_lng: str = "en"):
    if update:
        await update.message.reply_text(texts[usr_lng]["textError"],
                                        reply_markup=buttons[usr_lng]["main_menu_markup"])
    elif query:
        await query.edit_message_text(texts[usr_lng]["textError"],
                                      reply_markup=buttons[usr_lng]["main_menu_markup"])


async def send_message_with_retry(current_bot, chat_id, text, retry=3):
    for attempt in range(retry):
        try:
            return await current_bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            if attempt < retry - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(
                    f"Failed to send message after {retry} attempts: {e}")
                return None


# For unknown commands and texts
# async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.delete()

# endregion


# region Handlers

async def callback_query_handler(update: Update, context: CallbackContext) -> None:
    query: CallbackQuery = update.callback_query
    query_data = query.data

    if query_data == main_menu_cb:  # Main Menu
        await menu_from_callback(query)
    elif query_data == balance_cb:  # User Balance
        await user_balance_from_call_back(update, query)
    elif query_data == account_menu_cb:  # Account Menu
        await account_menu_call_back(query)
    elif query_data == account_info_cb:  # User Account Info
        await account_info(query)
    elif query_data == categories_cb:  # Product Categories
        await product_categories(query)
    elif query_data == change_lang_cb:  # Product Categories
        await change_user_language(query)
    elif query_data.startswith(transactions_cb):  # User Transactions
        await account_transactions(query)
    elif query_data.startswith(purchase_products_cb):  # User Purchase Products
        await user_purchase_products(query)
    elif query_data.startswith(f"{select_category_cb}_"):  # Selected category
        await products(query)
    elif query_data.startswith(f"{select_product_cb}_"):  # Selected product
        await product_payment_detail(query)
    elif query_data.startswith(f"{payment_cb}_"):  # Payment processing
        await payment(update, context, query)

    await query.answer()  # Stop button animation
    return


# Global Error Handler
async def error_handler(update: Update, context: CallbackContext):
    try:
        logger.error(msg="Exception while handling an update:",
                     exc_info=context.error)
        # # Notify the user (optional)
        # if update and update.effective_user:
        #     await update.effective_message.reply_text('An error occurred. The bot will continue to work.')
    except Exception as e:
        logger.error(f"Error in error_handler: {e}")


# endregion


# region etc
@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""

    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    """
    Custom CallbackContext class that makes `user_data` available for updates of type
    `WebhookUpdate`.
    """

    @classmethod
    def from_update(
            cls,
            update: object,
            application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


async def start(update: Update, context: CustomContext) -> None:
    print("START")
    """Display a message with instructions on how to use this bot."""
    payload_url = html.escape(f"{URL}/submitpayload?user_id=<your user id>&payload=<payload>")
    text = (
        f"To check if the bot is still running, call <code>{URL}/healthcheck</code>.\n\n"
        f"To post a custom update, call <code>{payload_url}</code>."
    )
    await update.message.reply_html(text=text)


async def webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Handle custom updates."""
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = (
        f"The user {chat_member.user.mention_html()} has sent a new payload. "
        f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode=ParseMode.HTML)


@csrf_exempt
async def telegram(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return HttpResponse()

    print("Telegram")
    try:
        # Log the raw incoming data for debugging
        # print(request.body)
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await ptb_application.update_queue.put(
            Update.de_json(data=json.loads(request.body), bot=ptb_application.bot)
        )
    except Exception as e:
        logger.error(f"Error in ptb_application.update_queue.put: {e}")

    return HttpResponse()


@csrf_exempt
async def custom_updates(request: HttpRequest) -> HttpResponse:
    """
    Handle incoming webhook updates by also putting them into the `update_queue` if
    the required parameters were passed correctly.
    """
    try:
        user_id = int(request.GET["user_id"])
        payload = request.GET["payload"]
    except KeyError:
        return HttpResponseBadRequest(
            "Please pass both `user_id` and `payload` as query parameters.",
        )
    except ValueError:
        return HttpResponseBadRequest("The `user_id` must be a string!")

    await ptb_application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
    return HttpResponse()


@csrf_exempt
async def health(_: HttpRequest) -> HttpResponse:
    """For the health endpoint, reply with a simple plain text message."""
    return HttpResponse("The bot is still running fine :)")


# endregion

# Set up PTB application and a web application for handling the incoming requests.
context_types = ContextTypes(context=CustomContext)
# Here we set updater to None because we want our custom webhook server to handle the updates
# and hence we don't need an Updater instance
ptb_application = (
    Application.builder().token(TOKEN).updater(None).context_types(context_types).build()
)

# register handlers
handlers = [
    # Check account or create only here
    CommandHandler("start", start_menu),
    CommandHandler("menu", start_menu),
    CommandHandler("balance", user_balance),
    ConversationHandler(
        entry_points=[
            CommandHandler("deposit", deposit_money),
            CallbackQueryHandler(
                deposit_money_from_callback, pattern=f"^{deposit_cb}$"),
        ],
        states={
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_amount)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_back_to_menu),
            # For callback button
            CallbackQueryHandler(cancel_back_to_menu,
                                 pattern=f"^{main_menu_cb}$"),
        ],
    ),
    # MessageHandler(filters.TEXT, delete_message),  # Performance issue
    CallbackQueryHandler(callback_query_handler),
]

ptb_application.add_handlers(handlers)

ptb_application.add_error_handler(error_handler)

# ptb_application.add_handler(CommandHandler("start", start))

# ptb_application.add_handler(CommandHandler("menu", start_menu))

# ptb_application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))


urlpatterns = [
    path("telegram", telegram, name="Telegram updates"),
    path("submitpayload", custom_updates, name="custom updates"),
    path("healthcheck", health, name="health check"),
]


async def main() -> None:
    """Finalize configuration and run the applications."""
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=get_asgi_application(),
            port=PORT,
            use_colors=False,
            # host="127.0.0.1",
            host="0.0.0.0",
            # lifespan="off",  # Disable lifespan protocol
        )
    )

    # Pass webhook settings to telegram
    await ptb_application.bot.set_webhook(url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES)

    # Run application and webserver together
    async with ptb_application:
        await ptb_application.start()
        await webserver.serve()
        await ptb_application.stop()


if __name__ == "__main__":
    # asyncio.run(main(), )
    # Run the bots event loop in a separate thread.
    thread = threading.Thread(target=asyncio.run, args=(main(),))
    thread.daemon = True  # Ensure the thread doesn't block app shutdown
    thread.start()

    # Block the main thread until the server shuts down
    try:
        thread.join()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
