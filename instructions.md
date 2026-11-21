# Project: Ingredient Scanner Telegram Bot (Romanian Cosmetics & Pharmacy)

## Tech Stack
- Python 3.10+
- aiogram 3.x (Strictly use v3.x syntax: Routers, async handlers with decorators).
- aiosqlite (Strictly async database operations to avoid blocking the event loop).
- python-dotenv (For environment variable management).

## Core Logic & Architecture
1. The bot receives a photo of a cosmetic, skincare, or pharmacy product ingredient list.
2. Extract text using OCR (Create an async placeholder function for the OCR API logic; I will implement the actual API call later).
3. Cross-reference the extracted ingredients with a local SQLite database of known components.
4. Generate a safety report for the user featuring:
   - A Traffic-Light visual score (🔴 Red: Dangerous/Allergen, 🟡 Yellow: Moderate/Caution, 🟢 Green: Safe).
   - A numerical safety score.
   - A detailed breakdown of the analyzed ingredients.

## Code Requirements
- All functions must be fully asynchronous.
- Load tokens securely using `os.getenv("BOT_TOKEN")`. Do not hardcode secrets.
- Encapsulate SQLite database operations in a separate class or module.
- Implement basic standard logging.