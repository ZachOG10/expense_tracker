"""
THIS IS MY FIRST PROJECT SINCE I LEARNT PYTHON.
AN EXPENSE TRACKER
This program keeps track of your income and expenses.
It helps you know exactly where your money goes.
"""
import json
import math
from datetime import datetime


def save_transactions():
    with open("transactions.json", "w") as file:
        json.dump(transactions, file)

def load_transactions():
    try:
        with open("transactions.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def get_valid_amount(prompt_text):
    while True:
        try:
            value = float(input(prompt_text))
            
            if not math.isfinite(value) or value <= 0:
                print("Amount must be a positive number. Try again.")
                continue
            return round(value, 2)
        except ValueError:
            print("That's not a valid number. Please try again.")

def get_valid_description(prompt_text):
    while True:
        description = input(prompt_text).strip()
        if description == "":
            print("Description cannot be empty. Try again.")
            continue
        return description

def get_valid_transaction_number(prompt_text, total):
    while True:
        try:
            number = int(input(prompt_text))
            if 1 <= number <= total:
                return number - 1
            print(f"Please enter a number between 1 and {total}.")
        except ValueError:
            print("That's not a valid whole number. Please try again.")

def add_transaction(transaction_type):
    transaction_amount = get_valid_amount("Enter amount: ")
    description = get_valid_description("Enter category/description: ")
    today = datetime.now().strftime("%Y-%m-%d")

    transaction = {
        "type": transaction_type,
        "amount": transaction_amount,
        "description": description,
        "date": today
    }
    transactions.append(transaction)
    save_transactions()

    print(f"{transaction_type.capitalize()} of {transaction_amount:,.2f} added.")

def view_balance():
    total_income = 0.0
    total_expense = 0.0

    for transaction in transactions:
        if transaction["type"] == "income":
            total_income += transaction["amount"]
        elif transaction["type"] == "expense":
            total_expense += transaction["amount"]

    balance = round(total_income - total_expense, 2)

    print("\n--- FINANCIAL SUMMARY ---")
    print(f"Total Income: {total_income:,.2f}")
    print(f"Total Expenses: {total_expense:,.2f}")
    print(f"Balance: {balance:,.2f}")

    if balance > 0:
        print("Your balance is positive.")
    elif balance == 0:
        print("You have broken even.")
    else:
        print("Your balance is negative.")

def view_all_transactions():
    if not transactions:
        print("No transactions recorded yet.")
    else:
        print("\n--- ALL TRANSACTIONS ---")
        for index, transaction in enumerate(transactions, start=1):
            transaction_type = transaction["type"]
            transaction_amount = transaction["amount"]
            transaction_description = transaction["description"]
            transaction_date = transaction["date"]
            print(f"{index}. {transaction_type.capitalize()} - {transaction_amount:,.2f} - {transaction_description} - {transaction_date}")

def check_budget():
    this_month = datetime.now().strftime("%Y-%m")
    total_expense = 0.0

    for transaction in transactions:
        if transaction["type"] == "expense" and transaction["date"].startswith(this_month):
            total_expense += transaction["amount"]

    total_expense = round(total_expense, 2)
    monthly_budget = get_valid_amount("Enter your monthly budget: ")

    print("\n--- BUDGET CHECK ---")
    print(f"Expenses This Month: {total_expense:,.2f}")
    print(f"Monthly Budget: {monthly_budget:,.2f}")

    if total_expense > monthly_budget:
        amount_over = round(total_expense - monthly_budget, 2)
        print(f"WARNING: You are over budget by {amount_over:,.2f}!")
    elif total_expense == monthly_budget:
        print("You have reached your monthly budget exactly.")
    else:
        amount_remaining = round(monthly_budget - total_expense, 2)
        print(f"You are within budget. Remaining: {amount_remaining:,.2f}")

def view_by_category():
    category_totals = {}

    for transaction in transactions:
        if transaction["type"] == "expense":
            category = transaction["description"].title()
            amount = transaction["amount"]

            if category in category_totals:
                category_totals[category] += amount
            else:
                category_totals[category] = amount

    print("\n--- SPENDING BY CATEGORY ---")
    if not category_totals:
        print("No expenses recorded yet.")
    else:
        for category, total in category_totals.items():
            print(f"{category}: {total:,.2f}")

def edit_or_delete():
    if not transactions:
        print("No transactions to edit or delete.")
        return

    view_all_transactions()
    chosen_index = get_valid_transaction_number("Enter transaction number: ", len(transactions))

    action = input("Type 'edit' or 'delete': ").strip().lower()

    if action == "delete":
        transactions.pop(chosen_index)
        save_transactions()
        print("Transaction deleted.")
    elif action == "edit":
        new_amount = get_valid_amount("Enter the new amount: ")
        transactions[chosen_index]["amount"] = new_amount
        save_transactions()
        print("Transaction updated.")
    else:
        print("Invalid action. No changes made.")

transactions = load_transactions()

running = True

while running:
    print("\n===== EXPENSE TRACKER =====")
    print("1. Add income")
    print("2. Add expense")
    print("3. View balance")
    print("4. View all transactions")
    print("5. Check budget")
    print("6. Exit")
    print("7. View spending by category")
    print("8. Edit/Delete a transaction")

    choice = input("Choose an option: ").strip()

    if choice == "1":
        add_transaction("income")
    elif choice == "2":
        add_transaction("expense")
    elif choice == "3":
        view_balance()
    elif choice == "4":
        view_all_transactions()
    elif choice == "5":
        check_budget()
    elif choice == "6":
        print("Goodbye!")
        running = False
        save_transactions()
    elif choice == "7":
        view_by_category()
    elif choice == "8":
        edit_or_delete()
    else:
        print("Invalid option. Please choose a number from 1 to 8.")
        