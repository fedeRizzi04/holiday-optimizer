## Problem Description

When a group travels together, assigning rooms can become more complicated than it looks.
Rooms have different capacities, people may have preferences about who they share with,
and a solution that is good for most of the group can still leave one person with a bad match.

**The room assignment problem** finds the **optimal allocation of people to rooms** while
trying to keep the least satisfied person as satisfied as possible.

### How it works

1. Each person must be assigned to exactly one room.
2. Each room can host at most the number of people allowed by its capacity.
3. The preference matrix says whether a person is happy to share a room with another person.
   - **1** -> they are happy to share
   - **0** -> they would rather not share
4. For each person, the optimizer computes a satisfaction score:
   - preferred roommate: +1
   - non-preferred roommate: -1

The objective is not just to maximize the total happiness of the group. The model first
maximizes the minimum satisfaction score, so the final assignment is more balanced and avoids
sacrificing one person for a slightly better overall total. When two assignments have the same
minimum score, it picks the one with the higher total satisfaction.

### Example

Suppose there are five people and two rooms:

| Room   | Capacity |
|--------|----------|
| Room 1 | 3        |
| Room 2 | 2        |

Alice and Bob would like to share a room. Charlie, Diana, and Eve are also comfortable
sharing together. The optimizer may return:

| Room   | People              |
|--------|---------------------|
| Room 1 | Charlie, Diana, Eve |
| Room 2 | Alice, Bob          |

This assignment respects the room capacities and keeps every person with acceptable
roommates whenever possible.
