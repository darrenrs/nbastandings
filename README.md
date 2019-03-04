# nbastandings

The NBA Standings Python suite currently consists of two programs that run basic predictions on the NBA season, based on <a href="https://fivethirtyeight.com">FiveThirtyEight's dataset.</a><br>It is definitely a work in progress and is not intended to be used for any serious data analysis.

## Scenarios.py

Based on the team list specified, generates a CSV file containing all permutations of game results for the team. The number of games can be specified, but it will not exceed 22 (20 is the Excel limit).

## SimSeason.py

Simulates the remainder of the season x number of times and exports it as a CSV.<br>Note: it doesn't account for tiebreakers properly.
