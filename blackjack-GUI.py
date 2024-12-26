import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import random
import json
import requests
from PIL import Image, ImageTk
from io import BytesIO
from os.path import exists

SUITS = {'Hearts': '♥', 'Diamonds': '♦', 'Spades': '♠', 'Clubs': '♣'}
FACES = {'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
SAVE_FILE = 'blackjack_save.json'
CARD_API_BASE = "https://deckofcardsapi.com/static/img/"
CARD_CODES = {
   'Hearts': {'A': 'AH', '2': '2H', '3': '3H', '4': '4H', '5': '5H', '6': '6H', '7': '7H', '8': '8H', '9': '9H', '10': '0H', 'J': 'JH', 'Q': 'QH', 'K': 'KH'},
   'Diamonds': {'A': 'AD', '2': '2D', '3': '3D', '4': '4D', '5': '5D', '6': '6D', '7': '7D', '8': '8D', '9': '9D', '10': '0D', 'J': 'JD', 'Q': 'QD', 'K': 'KD'},
   'Spades': {'A': 'AS', '2': '2S', '3': '3S', '4': '4S', '5': '5S', '6': '6S', '7': '7S', '8': '8S', '9': '9S', '10': '0S', 'J': 'JS', 'Q': 'QS', 'K': 'KS'},
   'Clubs': {'A': 'AC', '2': '2C', '3': '3C', '4': '4C', '5': '5C', '6': '6C', '7': '7C', '8': '8C', '9': '9C', '10': '0C', 'J': 'JC', 'Q': 'QC', 'K': 'KC'}
}

class Card:
   def __init__(self, suit, value):
       self.suit = suit
       self.value = value

   def __str__(self):
       val = FACES.get(self.value, self.value)
       return f"{val}{SUITS[self.suit]}"

class Deck:
   def __init__(self):
       self.cards = [Card(suit, value) for suit in SUITS 
                    for value in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']]
       random.shuffle(self.cards)

   def draw(self):
       return self.cards.pop() if self.cards else None

class BlackjackGUI:
   def __init__(self, root):
       self.root = root
       self.root.title('Blackjack')
       self.load_game()
       self.stats = {'wins': 0, 'losses': 0, 'blackjacks': 0, 'dealer_busts': 0}
       self.current_bet = 0
       self.setup_gui()

   def load_card_image(self, card):
       code = CARD_CODES[card.suit][card.value]
       url = f"{CARD_API_BASE}{code}.png"
       response = requests.get(url)
       img = Image.open(BytesIO(response.content))
       img = img.resize((100, 145), Image.LANCZOS)
       return ImageTk.PhotoImage(img)

   def setup_gui(self):
       self.root.configure(bg='#2e2e2e')
       style = ttk.Style()
       style.theme_use('clam')
       
       # Configure styles
       style.configure('TFrame', background='#2e2e2e')
       style.configure('TLabel', background='#2e2e2e', foreground='white', font=('Arial', 12))
       style.configure('Play.TButton', padding=6, background='#4CAF50')
       style.configure('Bet.TButton', padding=6, background='#2196F3')
       style.configure('Stats.TButton', padding=6, background='#9E9E9E')
       
       # Create frames
       self.stats_frame = ttk.Frame(self.root, padding="10")
       self.stats_frame.pack(fill='x')
       
       self.game_frame = ttk.Frame(self.root, padding="10")
       self.game_frame.pack(fill='both', expand=True)
       
       # Stats display
       self.stats_label = ttk.Label(self.stats_frame, text='')
       self.stats_label.pack(side='left')
       
       # Money display
       self.money_label = ttk.Label(self.game_frame, text=f'Balance: ${self.money}')
       self.money_label.pack(pady=5)
       
       # Dealer area
       self.dealer_label = ttk.Label(self.game_frame, text='Dealer cards:')
       self.dealer_label.pack()
       self.dealer_card_frame = ttk.Frame(self.game_frame)
       self.dealer_card_frame.pack()
       
       # Player area
       self.player_label = ttk.Label(self.game_frame, text='Your cards:')
       self.player_label.pack()
       self.player_card_frame = ttk.Frame(self.game_frame)
       self.player_card_frame.pack()
       
       # Button frames
       self.button_frame = ttk.Frame(self.game_frame)
       self.button_frame.pack(pady=20)
       
       play_buttons = ttk.Frame(self.button_frame)
       play_buttons.pack()
       
       utility_buttons = ttk.Frame(self.button_frame)
       utility_buttons.pack(pady=10)
       
       # Create play buttons
       play_button_configs = [
           ('hit', self.hit, 'Play.TButton'),
           ('stand', self.stand, 'Play.TButton'),
           ('double', self.double_down, 'Play.TButton'),
           ('split', self.split, 'Play.TButton')
       ]
       
       utility_button_configs = [
           ('bet', self.place_bet, 'Bet.TButton'),
           ('show_stats', self.show_stats, 'Stats.TButton')
       ]
       
       for name, command, style_name in play_button_configs:
           btn = ttk.Button(play_buttons, text=name.title(), command=command, style=style_name)
           btn.pack(side='left', padx=5)
           setattr(self, f'{name}_button', btn)
       
       for name, command, style_name in utility_button_configs:
           btn = ttk.Button(utility_buttons, text=name.title().replace('_', ' '), 
                          command=command, style=style_name)
           btn.pack(side='left', padx=5)
           setattr(self, f'{name}_button', btn)
       
       self.status_label = ttk.Label(self.game_frame, text='')
       self.status_label.pack(pady=10)
       
       self.deck = None
       self.player_hand = []
       self.dealer_hand = []
       self.game_in_progress = False
       
       self.disable_game_buttons()
       self.bet_button['state'] = 'normal'
       self.update_stats()

   def save_game(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump({'money': self.money}, f)

   def load_game(self):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.money = data.get('money', 1000)
        except (FileNotFoundError, json.JSONDecodeError):
            self.money = 1000

   def calculate_hand(self, hand):
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

   def update_stats(self):
        if self.stats['wins'] + self.stats['losses'] > 0:
            win_rate = (self.stats['wins'] / (self.stats['wins'] + self.stats['losses'])) * 100
        else:
            win_rate = 0
        self.stats_label['text'] = (
            f"Win Rate: {win_rate:.1f}% | "
            f"Blackjacks: {self.stats['blackjacks']} | "
            f"Dealer Busts: {self.stats['dealer_busts']}"
        )

   def show_stats(self):
        if self.stats['wins'] + self.stats['losses'] > 0:
            win_rate = (self.stats['wins'] / (self.stats['wins'] + self.stats['losses'])) * 100
        else:
            win_rate = 0
        stats_text = (
            f"Total Wins: {self.stats['wins']}\n"
            f"Total Losses: {self.stats['losses']}\n"
            f"Blackjacks: {self.stats['blackjacks']}\n"
            f"Dealer Busts: {self.stats['dealer_busts']}\n"
            f"Win Rate: {win_rate:.1f}%\n"
            f"Current Balance: ${self.money}"
        )
        messagebox.showinfo('Statistics', stats_text)

   def place_bet(self):
        bet = simpledialog.askinteger('Place Bet', 
                                    f'Enter bet amount (1-{self.money}):',
                                    minvalue=1, maxvalue=self.money)
        if bet:
            self.current_bet = bet
            self.start_new_hand()
            self.enable_game_buttons()

   def enable_game_buttons(self):
        self.bet_button['state'] = 'disabled'
        self.hit_button['state'] = 'normal'
        self.stand_button['state'] = 'normal'
        if self.money >= self.current_bet * 2:
            self.double_button['state'] = 'normal'
        if len(self.player_hand) == 2 and self.player_hand[0].value == self.player_hand[1].value:
            self.split_button['state'] = 'normal'

   def disable_game_buttons(self):
        for btn in [self.hit_button, self.stand_button, 
                    self.double_button, self.split_button]:
            btn['state'] = 'disabled'
        self.bet_button['state'] = 'normal'

   def hit(self):
        self.double_button['state'] = 'disabled'
        self.split_button['state'] = 'disabled'
        
        card = self.deck.draw()
        self.player_hand.append(card)
        self.update_display()
        
        if self.calculate_hand(self.player_hand) > 21:
            self.handle_bust()

   def stand(self):
        self.play_dealer_hand()
        self.end_game()

   def double_down(self):
        self.current_bet *= 2
        self.hit()
        if self.calculate_hand(self.player_hand) <= 21:
            self.stand()

   def split(self):
        messagebox.showinfo('Coming Soon', 'Split feature coming soon!')

   def start_new_hand(self):
        self.deck = Deck()
        self.player_hand = [self.deck.draw(), self.deck.draw()]
        self.dealer_hand = [self.deck.draw(), self.deck.draw()]
        self.game_in_progress = True
        self.update_display()
        
        if self.calculate_hand(self.player_hand) == 21:
            self.stats['blackjacks'] += 1
            self.money += int(self.current_bet * 1.5)
            self.status_label['text'] = 'Blackjack! 🎉'
            self.save_game()
            self.end_game()

   def play_dealer_hand(self):
        while self.calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.draw())
        self.update_display(show_dealer=True)

   def handle_bust(self):
        self.stats['losses'] += 1
        self.money -= self.current_bet
        self.status_label['text'] = 'Bust! 💥'
        self.save_game()
        self.end_game()

   def end_game(self):
        if not self.game_in_progress:
            return
            
        dealer_value = self.calculate_hand(self.dealer_hand)
        player_value = self.calculate_hand(self.player_hand)
        
        if player_value <= 21:
            if dealer_value > 21:
                self.stats['dealer_busts'] += 1
                self.stats['wins'] += 1
                self.money += self.current_bet
                self.status_label['text'] = 'Dealer busts! You win! 💰'
            elif player_value > dealer_value:
                self.stats['wins'] += 1
                self.money += self.current_bet
                self.status_label['text'] = 'You win! 🎉'
            elif player_value < dealer_value:
                self.stats['losses'] += 1
                self.money -= self.current_bet
                self.status_label['text'] = 'Dealer wins! 😢'
            else:
                self.status_label['text'] = 'Push! 🤝'
        
        self.game_in_progress = False
        self.update_display(show_dealer=True)
        self.update_stats()
        self.save_game()
        self.disable_game_buttons()

   def update_display(self, show_dealer=False):
       # Clear previous cards
       for widget in self.dealer_card_frame.winfo_children():
           widget.destroy()
       for widget in self.player_card_frame.winfo_children():
           widget.destroy()
       
       # Show player cards
       for card in self.player_hand:
           img = self.load_card_image(card)
           label = ttk.Label(self.player_card_frame, image=img)
           label.image = img
           label.pack(side='left', padx=2)
       
       # Show dealer cards
       if show_dealer:
           for card in self.dealer_hand:
               img = self.load_card_image(card)
               label = ttk.Label(self.dealer_card_frame, image=img)
               label.image = img
               label.pack(side='left', padx=2)
       else:
           # Show first card and back
           img = self.load_card_image(self.dealer_hand[0])
           label = ttk.Label(self.dealer_card_frame, image=img)
           label.image = img
           label.pack(side='left', padx=2)
           
           response = requests.get(f"{CARD_API_BASE}back.png")
           back_img = Image.open(BytesIO(response.content))
           back_img = back_img.resize((100, 145), Image.LANCZOS)
           back_photo = ImageTk.PhotoImage(back_img)
           back_label = ttk.Label(self.dealer_card_frame, image=back_photo)
           back_label.image = back_photo
           back_label.pack(side='left', padx=2)
       
       # Update labels
       self.money_label['text'] = f'Balance: ${self.money} | Bet: ${self.current_bet}'
       
def main():
   root = tk.Tk()
   root.title('Blackjack')
   root.geometry('800x600')
   BlackjackGUI(root)
   root.mainloop()

if __name__ == '__main__':
   main()