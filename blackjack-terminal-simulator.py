import random
import json
from os.path import exists

SUITS = {'Hearts': '♥', 'Diamonds': '♦', 'Spades': '♠', 'Clubs': '♣'}
FACES = {'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
SAVE_FILE = 'blackjack_save.json'
# Add at top of file
class Stats:
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.blackjacks = 0
        self.dealer_busts = 0
        self.total_money_won = 0
        self.hands_played = 0
class Card:
   def __init__(self, suit, value):
       self.suit = suit
       self.value = value

   def __str__(self):
       val = FACES.get(self.value, self.value)
       return f"{val}{SUITS[self.suit]}"

class Deck:
   def __init__(self):
       self.cards = [Card(suit, value) for suit in SUITS for value in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']]
       random.shuffle(self.cards)

   def draw(self):
       return self.cards.pop() if self.cards else None

def calculate_hand(hand):
   value = 0
   aces = 0
   for card in hand:
       if card.value in ['J', 'Q', 'K']:
           value += 10
       elif card.value == 'A':
           aces += 1
       else:
           value += int(card.value)
   for _ in range(aces):
       value += 11 if value + 11 <= 21 else 1
   return value

def play_split_hand(original_card, deck, bet, money):
   hand = [original_card, deck.draw()]
   result = play_hand(hand, deck, bet, True)
   return result, bet if result > 0 else -bet

def play_hand(player_hand, deck, bet, stats, is_split=False):
   dealer_hand = [deck.draw(), deck.draw()]
   
   while True:
       print(f"\nYour hand: {' '.join(str(card) for card in player_hand)} ({calculate_hand(player_hand)})")
       print(f"Dealer shows: {dealer_hand[0]}")
       
       if calculate_hand(player_hand) == 21:
           stats.blackjacks += 1
           return 1.5 * bet if not is_split else bet
           
       options = ['h', 's']
       if len(player_hand) == 2 and not is_split:
           can_split = player_hand[0].value == player_hand[1].value
           if can_split:
               options.append('p')
           options.append('d')
           
       try:
           action = input(f"Options ({'/'.join(options)}): ").lower()
           if action not in options:
               print("Invalid option!")
               continue
               
           if action == 'h':
               player_hand.append(deck.draw())
               if calculate_hand(player_hand) > 21:
                   print(f"Bust! {' '.join(str(card) for card in player_hand)} ({calculate_hand(player_hand)})")
                   stats.losses += 1
                   return -1
                   
           elif action == 'd':
               player_hand.append(deck.draw())
               print(f"Double down: {' '.join(str(card) for card in player_hand)} ({calculate_hand(player_hand)})")
               if calculate_hand(player_hand) > 21:
                   stats.losses += 1
                   return -2
               bet *= 2
               action = 's'
               
           if action == 'p':
               split_results = []
               for card in player_hand:
                   result, bet_result = play_split_hand(card, deck, bet/2, stats)
                   split_results.append(bet_result)
               return sum(split_results)
               
           if action == 's':
               while calculate_hand(dealer_hand) < 17:
                   dealer_hand.append(deck.draw())
               
               dealer_value = calculate_hand(dealer_hand)
               player_value = calculate_hand(player_hand)
               
               print(f"\nYour final hand: {' '.join(str(card) for card in player_hand)} ({player_value})")
               print(f"Dealer's hand: {' '.join(str(card) for card in dealer_hand)} ({dealer_value})")
               
               if dealer_value > 21:
                   print("Dealer busts! 💥")
                   stats.dealer_busts += 1
                   stats.wins += 1
                   return bet
               elif player_value > dealer_value:
                   print("You win! 🎉")
                   stats.wins += 1
                   return bet
               elif player_value < dealer_value:
                   print("Dealer wins! 😢")
                   stats.losses += 1
                   return -bet
               else:
                   print("Push! 🤝")
                   return 0
                   
       except ValueError:
           print("Invalid input!")
           continue

def save_game(money):
   with open(SAVE_FILE, 'w') as f:
       json.dump({'money': money}, f)

def load_game():
   if exists(SAVE_FILE):
       with open(SAVE_FILE, 'r') as f:
           data = json.load(f)
           return data.get('money') if data.get('money', 0) > 0 else 1000
   return 1000

def play_blackjack():
   money = load_game()
   stats = Stats()
   print(f"\n💰 Welcome to Blackjack! Starting money: ${money}")
   
   while money > 0:
       print(f"\nCurrent balance: ${money}")
       try:
           bet = int(input("Enter bet (0 to quit): $"))
           if bet == 0:
               break
           if bet > money:
               print("Insufficient funds!")
               continue
           
           deck = Deck()
           player_hand = [deck.draw(), deck.draw()]
           result = play_hand(player_hand, deck, bet, stats)
           money += result
           save_game(money)
           
           stats.hands_played += 1
           stats.total_money_won += result
           
           if stats.hands_played % 5 == 0:
               print(f"\n📊 Stats after {stats.hands_played} hands:")
               print(f"Win rate: {(stats.wins/stats.hands_played)*100:.1f}%")
               print(f"Blackjacks: {stats.blackjacks}")
               print(f"Dealer busts: {stats.dealer_busts}")
               print(f"Money won/lost: ${stats.total_money_won}")
           
       except ValueError:
           print("Invalid bet amount!")
           continue
       except KeyboardInterrupt:
           print("\nGame saved! Goodbye!")
           save_game(money)
           break
           
   print(f"\nThanks for playing! Final balance: ${money}")

if __name__ == "__main__":
   play_blackjack()