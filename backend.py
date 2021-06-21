import numpy as np
import pandas as pd


class Splitter:

    def __init__(self, names):
        self.names = names.split()
        self.shopping_cart = pd.DataFrame(columns=['name', 'price'] + self.names)
        self.transactions = pd.DataFrame(columns=['from', 'to', 'amount']
                                          + [s + '_debt' for s in self.names]
                                          + [s + '_debt_after' for s in self.names]
                                          )
        self.paid = None

    def _calculate_item_impact(self, row):
        for n in self.names:
            row[n] = row[n] * row['price_per_unit']
        return row

    def _set_debts(self):
        # Calculate price per unit
        self.shopping_cart['price_per_unit'] = self.shopping_cart.price / self.shopping_cart[[*self.names]].sum(axis=1)
        # Calculate personal cart sum for each person
        debts = self.shopping_cart[[*self.names] + ['price_per_unit']].apply(self._calculate_item_impact, axis=1)
        debts = debts[[*self.names]].sum(axis=0) - pd.Series(self.paid)
        debts.index = [s + '_debt' for s in debts.index]
        debts = debts.to_dict()
        for c in ['from', 'to', 'amount', *[s + '_debt_after' for s in self.names]]:
                debts[c] = np.nan
        # Append debts
        self.transactions = self.transactions.append(debts, ignore_index=True)


    def _update_personal_sum(self):
        debts = self.shopping_cart[[*self.names] + ['price_per_unit']].apply(self._calculate_item_impact, axis=1)
        return debts[[*self.names]].sum(axis=0).to_dict()

    def _compute_transaction(self):
        # Get selection of dataframe containing last debts state
        debts = self.transactions[[s + '_debt' for s in self.names]].tail(1)
        # Get sender and receiver self.names and amount
        from_name = debts.idxmax(axis=1).values[0]
        to_name = debts.idxmin(axis=1).values[0]
        amount = min(abs(debts[from_name].values[0]), abs(debts[to_name].values[0]))
        # Calculate money transfer
        last_row = len(self.transactions) - 1
        debts.loc[last_row, from_name] -= amount
        debts.loc[last_row, to_name] += amount
        # Update dataframe
        cols_to_update = ['from', 'to', 'amount', *[s + '_debt_after' for s in self.names]]
        updated_data = [
            from_name.split('_')[0],
            to_name.split('_')[0],
            amount,
            *debts.iloc[0].to_list()
        ]
        self.transactions.loc[len(self.transactions) - 1, cols_to_update] = updated_data
        # Create new transaction if needed
        if not self._is_resolved():
            self.transactions = self.transactions.append(self.transactions.iloc[last_row], ignore_index=True)
            last_row = len(self.transactions) - 1
            self.transactions.loc[last_row, [s + '_debt_after' for s in self.names]] = len(self.names)*[np.nan,]
            self.transactions.loc[last_row, [s + '_debt' for s in self.names]] = debts.iloc[0].values
            self.transactions.loc[last_row, ['from', 'to', 'amount']] = ['', '', 0.0]

    def _is_resolved(self):
        last_debt_state = self.transactions.iloc[-1][[s + '_debt_after' for s in self.names]]
        return np.isclose(last_debt_state.to_list(), 0.0).all()

    def add_item(self, item):
        self.shopping_cart = self.shopping_cart.append(item, ignore_index=True)

    def run(self):
        while not self._is_resolved():
            self._compute_transaction()
