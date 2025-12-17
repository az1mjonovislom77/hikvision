from aiogram import types, Router, F
from aiogram.filters import Command
from asgiref.sync import sync_to_async
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from django.template.defaultfilters import first

from person.models import Employee

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqam", request_contact=True)]],
        resize_keyboard=True
    )

    await message.answer("Salom.! Telefon raqamingizni kiriting.", reply_markup=keyboard)



@router.message(F.contact)
async def get_contact(message: types.Message):
    phone = message.contact.phone_number

    employee = await sync_to_async(
        lambda : Employee.objects.filter(phone_number=phone).first()
    )()

    if not employee:
        await message.answer("Rahmat! Sizning raqamingizga telefon raqamingiz mavjud emas.")
        return

    file_path = employee.face_image.path if employee.face_image else None
    begin_time = employee.begin_time if employee.begin_time else None
    end_time = employee.end_time

    photo = FSInputFile(file_path)

    await message.answer_photo(photo=photo, caption="siz haqingizda ma'lumot.!")
    await message.answer(f"kirgan vaqtingiz: {begin_time}")
    if end_time:
        await message.answer(f"halicha chiqqaningiz yo'q")
        return
    await message.answer(f"chiqqan vaqtingiz: {end_time}")





    # await message.answer(f"siz haqingizda: {employee}")



