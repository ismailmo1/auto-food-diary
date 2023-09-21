#!/usr/bin/env python

"""
Bot to identify food pics from Telegram messages.

Usage:
Send food pic to bot, tries to identify food and reply with predictions.
"""
from collections import Counter
import logging
from dotenv import load_dotenv
from os import getenv
from super_gradients.training import models
from super_gradients.common.object_names import Models
from model.predict import predict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
TELEGRAM_TOKEN = getenv("TELEGRAM_TOKEN")

# initialise model
model = None
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("send me food pics")


def sizeof_fmt(num) -> str:
    """return human readable file size

    e.g.

    ```
    sizeof_fmt(168963795964)
    >>> '157.4GB'
    ```
    Args:
        num (int): size of file in bytes

    Returns:
        str: human readable file size
    """
    # from Fred Cirera
    # https://web.archive.org/web/20111010015624/http://blogmag.net/blog/read/38/Print_human_readable_file_size
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """download image and reply with prediction label"""
    logger.info("photo received")
    # largest photo is last index
    file_id = update.message.photo[-1].file_id
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(f"{file_id}.jpeg")
    logger.info(f"downloaded file of size {sizeof_fmt(new_file.file_size)}")

    await update.message.reply_text(f"hang on, let me figure out what this is...")

    predicted_foods = predict_food(f"{file_id}.jpeg")
    # group foods
    food_counts = Counter(predicted_foods)
    food_count_msg = "\n".join(
        [f"{count} {food}" for food, count in food_counts.items()]
    )
    await update.message.reply_text(
        f"Oh nice! I can see you have a nice meal of:\n{food_count_msg}"
    )


def predict_food(image_url: str) -> list[str]:
    """
    return a prediction of a food label from an image url

    Args:
        image_url (str): absolute url to image to run prediction on

    Returns:
        list[str]: predicted foods
    """
    logger.info(f"predicting food label for {image_url}")
    foods = predict(image_url, model)
    # TODO: return annotated image
    return foods


def add_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))


def initialise_model() -> None:
    """load model with pretrained weights"""
    # HACK: i dont like this - see if theres a better convention for this
    global model
    if model is None:
        model = models.get(Models.YOLO_NAS_S, pretrained_weights="coco")


def main() -> None:
    # load model once on initial app load
    initialise_model()
    # build application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    add_handlers(application)

    # start bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
