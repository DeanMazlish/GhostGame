from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load words into a set for quick lookup
with open('words.txt', 'r') as file:
    WORDS = set(word.strip().upper() for word in file.readlines())

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        player1 = request.form.get('player1').strip()
        player2 = request.form.get('player2').strip()
        if not player1 or not player2:
            flash('Please enter names for both players.')
            return redirect(url_for('index'))
        session['player1'] = player1
        session['player2'] = player2
        session['fragment'] = ''
        session['current_player'] = 'player1'
        session['message'] = ''
        session['challenge'] = False  # Indicates if a challenge is pending
        session['challenged_player'] = None
        return redirect(url_for('game'))
    return render_template('index.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    if 'player1' not in session or 'player2' not in session:
        flash('Please start a new game.')
        return redirect(url_for('index'))

    player1 = session['player1']
    player2 = session['player2']
    fragment = session.get('fragment', '')
    current_player_key = session['current_player']
    message = session.get('message', '')
    challenge_pending = session.get('challenge', False)
    challenged_player_key = session.get('challenged_player', None)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_letter':
            letter = request.form.get('letter', '').strip().upper()
            if not letter.isalpha() or len(letter) != 1:
                flash('Please enter a single alphabetic character.')
                return redirect(url_for('game'))
            fragment += letter
            session['fragment'] = fragment
            # Switch player after adding a letter
            session['current_player'] = 'player2' if current_player_key == 'player1' else 'player1'
            session['message'] = ''
        elif action == 'challenge':
            challenger_key = current_player_key
            challenged_player_key = get_opponent_player_key(challenger_key)
            if len(fragment) < 4:
                # Proceed with challenge even if fragment is less than 4 letters
                pass  # Frontend handles the popup
            if fragment in WORDS and len(fragment) >= 4:  # Assuming minimum word length is 4
                # Challenger wins immediately
                challenger = get_player_name(challenger_key)
                message = f"The fragment '{fragment}' is a complete word. {challenger} (Challenger) wins!"
                reset_game()
                session['message'] = message
                return redirect(url_for('game'))
            else:
                # Proceed to challenge the opponent
                session['challenge'] = True
                session['challenged_player'] = challenged_player_key
                return redirect(url_for('challenge'))

    return render_template('game.html',
                           player1=player1,
                           player2=player2,
                           fragment=fragment,
                           current_player=get_player_name(session['current_player']),
                           message=message,
                           challenge_pending=challenge_pending,
                           fragment_length=len(fragment))

@app.route('/challenge', methods=['GET', 'POST'])
def challenge():
    if not session.get('challenge', False):
        flash('No challenge is currently pending.')
        return redirect(url_for('game'))

    player1 = session['player1']
    player2 = session['player2']
    fragment = session.get('fragment', '')
    challenged_player_key = session.get('challenged_player', None)
    challenged_player = get_player_name(challenged_player_key)
    challenger_key = get_opponent_player_key(challenged_player_key)
    challenger = get_player_name(challenger_key)
    message = session.get('message', '')

    if request.method == 'POST':
        word = request.form.get('word', '').strip().upper()
        if not word:
            flash('Please enter a word.')
            return redirect(url_for('challenge'))

        # Check if the word starts with the fragment
        if not word.startswith(fragment):
            flash(f"The word '{word}' does not start with the fragment '{fragment}'.")
            return redirect(url_for('challenge'))

        # Check if the word exists in the dictionary and meets minimum length
        if word in WORDS and len(word) >= 4:
            # Challenged player provided a valid word
            message = f"{challenged_player} provided the word '{word}', which is valid. {challenger} (Challenger) loses!"
        else:
            # Challenged player failed to provide a valid word
            message = f"{challenged_player} failed to provide a valid word starting with '{fragment}'. {challenger} (Challenger) wins!"

        # Reset the game after challenge
        reset_game()
        session['message'] = message
        return redirect(url_for('game'))

    return render_template('challenge.html',
                           challenged_player=challenged_player,
                           fragment=fragment,
                           challenger=challenger,
                           message=message)

def get_player_name(player_key):
    return session.get(player_key, 'Player')

def get_opponent_player_key(current_player_key):
    return 'player2' if current_player_key == 'player1' else 'player1'

def reset_game():
    session['fragment'] = ''
    session['current_player'] = 'player1'
    session['message'] = ''
    session['challenge'] = False
    session['challenged_player'] = None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
