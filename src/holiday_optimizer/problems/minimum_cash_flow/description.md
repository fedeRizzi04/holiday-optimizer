## Problem Description

When a group of friends goes on holiday together, some people end up paying for shared
expenses (accommodation, restaurants, activities) on behalf of everyone. At the end of
the trip, the group needs to settle up.

**The minimum cash flow problem** finds the **optimal set of transactions** to clear all
debts, minimising one of two objectives:

- **Total transactions** — fewer bank transfers overall
- **Maximum transactions per person** — no single person is overwhelmed with payments

### How it works

1. Each person's **net balance** is computed as what they paid minus their fair share.
   - **Positive** → they paid too little (debtor, they owe money)
   - **Negative** → they paid too much (creditor, they should receive money)
2. The optimizer decides who pays whom and how much, respecting everyone's balance.

A lot of apps can compute the balance of each person (e.g. Splitwise, Splittr, ...) but they don't always use an optimal
algorithm to compute the transactions (sometimes they use a greedy or heuristic approach). 

So you can use the balances computed by these apps and use the optimizer to compute the optimal transactions. 

### Example

| Person  | Paid  | Fair share | Balance |
|---------|-------|-----------|---------|
| Alice   | €120  | €80       | −€40    |
| Bob     | €40   | €80       | +€40    |
| Charlie | €80   | €80       |  €0     |

**Result:** Bob pays Alice €40. One transaction. 

In this optimizer you just have to input the balances of each person (positive if they owe money, negative if they should receive money) and the optimizer will compute the optimal transactions.