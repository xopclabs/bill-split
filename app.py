import numpy as np
import pandas as pd

# TODO: Regex checking

names = ''
aliases = {}
paid = {}
shopping_cart = None
transactions = None


def parse_entry(entry):
    entry = entry.split()
    # Finding boundary for item name
    for i, s in enumerate(entry):
        if s[0].isnumeric():
            break
    # If string doesn't meet the requirements, return None
    if i + 1 >= len(entry):
        return None
    # Creating return dictionary
    parsed_entry = dict(zip(shopping_cart.columns, len(shopping_cart.columns)*[0.0,]))
    # Parsing name
    parsed_entry['name'] = ' '.join(entry[:i])
    # Parsing price
    parsed_entry['price'] = float(entry[i])
    # Parsing quantites for each person
    for i in range(i + 1, len(entry)):
        # Skipping numbers
        if entry[i][0].isnumeric():
            continue
        # Get person's name
        person = entry[i]
        # Check for alias use
        if person not in names:
            if person in aliases.keys():
                person = aliases[person]
            else:
                return None
        # Get quantity (default to 1 if not specified)
        if i + 1 < len(entry) and entry[i + 1][0].isnumeric():
            quantity = float(entry[i + 1])
        else:
            quantity = 1.0
        # Add item to return dict
        parsed_entry[person] = quantity
    return parsed_entry


def set_debts():
    global transactions

    def calculate_item_impact(row):
        for n in names:
            row[n] = row[n] * row['price_per_unit']
        return row

    # Calculate price per unit
    shopping_cart['price_per_unit'] = shopping_cart.price / shopping_cart[[*names]].sum(axis=1)
    # Calculate personal cart sum for each person
    debts = shopping_cart[[*names] + ['price_per_unit']].apply(calculate_item_impact, axis=1)
    print('Personal sum:')
    print(debts[[*names]].sum(axis=0))
    debts = debts[[*names]].sum(axis=0) - pd.Series(paid)
    debts.index = [s + '_debt' for s in debts.index]
    debts = debts.to_dict()
    for c in ['from', 'to', 'amount', *[s + '_debt_after' for s in names]]:
        debts[c] = np.nan
    # Append debts
    transactions = transactions.append(debts, ignore_index=True)


def compute_transaction():
    global transactions

    # Get selection of dataframe containing last debts state
    debts = transactions[[s + '_debt' for s in names]].tail(1)
    # Get sender and receiver names and amount
    from_name = debts.idxmax(axis=1).values[0]
    to_name = debts.idxmin(axis=1).values[0]
    amount = min(abs(debts[from_name].values[0]), abs(debts[to_name].values[0]))
    # Calculate money transfer
    last_row = len(transactions) - 1
    debts.loc[last_row, from_name] -= amount
    debts.loc[last_row, to_name] += amount
    # Update dataframe
    cols_to_update = ['from', 'to', 'amount', *[s + '_debt_after' for s in names]]
    updated_data = [
        from_name.split('_')[0],
        to_name.split('_')[0],
        amount,
        *debts.iloc[0].to_list()
    ]
    transactions.loc[len(transactions) - 1, cols_to_update] = updated_data
    # Create new transaction if needed
    if not is_resolved():
        transactions = transactions.append(transactions.iloc[last_row], ignore_index=True)
        last_row = len(transactions) - 1
        transactions.loc[last_row, [s + '_debt_after' for s in names]] = len(names)*[np.nan,]
        transactions.loc[last_row, [s + '_debt' for s in names]] = debts.iloc[0].values
        transactions.loc[last_row, ['from', 'to', 'amount']] = ['', '', 0.0]


def is_resolved():
    last_debt_state = transactions.iloc[-1][[s + '_debt_after' for s in names]]
    return np.isclose(last_debt_state.to_list(), 0.0).all()


def print_transaction(transaction):
    cols = ('from', 'to', 'amount')
    transaction = dict(zip(cols, [transaction[c] for c in cols]))
    print(f'{transaction["from"]} -> {transaction["to"]} [{transaction["amount"]:.0f}]')


if __name__ == '__main__':
    # Entering names
    names = input('Enter names of people sharing the bills: ')
    names = names.split()
    if len(set([n[0] for n in names])) == len(names):
        aliases = dict(zip([n[0].lower() for n in names], names))
    else:
        aliases = dict(zip([n[:2].lower() for n in names], names))
    print('Created the following aliases for names:', end=' ')
    for n, a in aliases.items():
        print(f'{a} - {n}', end=' ')
    print()

    # Creating dataframes
    shopping_cart = pd.DataFrame(columns=['name', 'price'] + names)
    transactions = pd.DataFrame(columns=['from', 'to', 'amount'] + [s + '_debt' for s in names] + [s + '_debt_after' for s in names])

    # Entering shopping list
    print('Entering shopping list...')
    print('Syntax: "[name] [price] [{person (quantity)}...{}]"')
    print('Example: "Какахи Максима 313 m", "БЗМЖ Пуддинг 149.97 Artyom 2 Maxim 1"')
    while True:
        list_entry = input('Item: ')
        if list_entry == '':
            print('_')
            break
        parsed_entry = parse_entry(list_entry)
        if parsed_entry is None:
            print('Wrong syntax! Try again.')
            continue
        shopping_cart = shopping_cart.append(parsed_entry, ignore_index=True)
    print(shopping_cart)

    # Entering an amount that each person paid
    print('Entering how much everyone paid...')
    print('Syntax: "{[name] [price]}...{}"')
    while paid == {}:
        paid = dict(zip(names, len(names)*[0.0,]))
        paid_list = input().split()
        if len(paid_list) < 2:
            print('Specify at least one person that paid for the items. Try again.')
            paid = {}
            break
    for i, s in enumerate(paid_list):
        # Skip numbers
        if s[0].isnumeric():
            continue
        # Check for alias use
        if s not in names:
            if s in aliases.keys():
                s = aliases[s]
            else:
                print(f'Alias {s} not recognized')
                paid = {}
                break
        paid[s] = float(paid_list[i + 1])

    # Calculate debt for each person
    set_debts()
    print(transactions[[s+'_debt' for s in names]])

    # Do magic
    while not is_resolved():
        compute_transaction()
    for _, transaction in transactions.iterrows():
        print_transaction(transaction)
