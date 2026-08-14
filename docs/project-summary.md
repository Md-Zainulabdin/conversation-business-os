# Conversational Business OS (CBO) — What We've Built

> Non-technical summary for stakeholders.

We're building a system that lets a shopkeeper run his entire business with normal, everyday messages instead of paperwork. Right now we have a working web app, plus an AI assistant that understands plain language. Here's what exists today:

## 1. A secure log-in

- Shopkeepers create an account and log in. Each business has its own private, protected data.

## 2. Product catalog & stock

- Add the products you sell (name, what unit it's sold in — piece, pack, kg, etc., buying price, selling price).
- The system tracks your stock automatically and lets you set a "minimum level" so you know when it's time to reorder.
- Product categories (Grains, Beverages, etc.) are a shared reference list used by all accounts, not per-business data.

## 3. Customers

- Keep a list of customers so every sale can be linked to the right person.

## 4. Recording sales

- Log a sale in seconds — product, quantity, price, customer, date.
- Stock is reduced automatically the moment a sale is saved.

## 5. Recording purchases

- Log what you bought from suppliers, and stock goes up automatically.

## 6. Recording expenses

- Track rent, electricity, transport, salaries, and other costs in categories.

## 7. A dashboard

- One screen showing your overall picture — total sales, revenue, and activity over the last day, week, month, or year.

## 8. The AI assistant (the star feature)

- Instead of filling forms, you type a plain sentence and the AI figures it out. For example:
  - "Sold 20 packs of rice" → it proposes the sale, you confirm, and it's recorded.
  - "Bought 10 cartons of Coke" → same thing for a purchase.
  - "Paid 5,000 for electricity" → recorded as an expense.
  - "How much Coke stock is left?" → it tells you the current stock.
- It even handles multiple products in one message ("Sold 10 packs of rice and 20 coca-colas"), and if you say something that could match several products, it politely asks which one you meant instead of guessing.

## Where we are vs. the final vision

The long-term goal is to do all of this through WhatsApp, including voice notes — you just send a voice message and it records the transaction. That's the next phase. The web app and the "talk to the computer" brain are already built and working today.