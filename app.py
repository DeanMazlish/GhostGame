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
        session['player1_wins'] = 0
        session['player2_wins'] = 0
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
    player1_wins = session.get('player1_wins', 0)
    player2_wins = session.get('player2_wins', 0)

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
            if fragment in WORDS and len(fragment) >= 4:  # Assuming minimum word length is 4
                # Challenger wins immediately
                challenger = get_player_name(challenger_key)
                message = f"The fragment '{fragment}' is a complete word. {challenger} (Challenger) wins!"
                # Update win tally
                if challenger_key == 'player1':
                    session['player1_wins'] += 1
                else:
                    session['player2_wins'] += 1
                reset_game()
                session['message'] = message
                return redirect(url_for('game'))
            else:
                # Proceed to challenge the opponent
                session['challenge'] = True
                session['challenged_player'] = challenged_player_key
                return redirect(url_for('challenge'))
        elif action == 'start_new_game':
            # Reset game but keep the same players and their win tallies
            reset_game()
            session['fragment'] = ''
            session['current_player'] = 'player1'
            session['message'] = ''
            return redirect(url_for('game'))
        elif action == 'new_game_with_new_players':
            # Clear all session data and redirect to index for new players
            session.clear()
            return redirect(url_for('index'))

    return render_template('game.html',
                           player1=player1,
                           player2=player2,
                           fragment=fragment,
                           current_player=get_player_name(session['current_player']),
                           message=message,
                           challenge_pending=challenge_pending,
                           fragment_length=len(fragment),
                           player1_wins=player1_wins,
                           player2_wins=player2_wins)

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
    player1_wins = session.get('player1_wins', 0)
    player2_wins = session.get('player2_wins', 0)

    if request.method == 'POST':
        suffix = request.form.get('suffix', '').strip().upper()
        if not suffix:
            flash('Please enter the letters to complete the word.')
            return redirect(url_for('challenge'))

        # Ensure that the suffix does not contain spaces or invalid characters
        if not suffix.isalpha():
            flash('Please enter only alphabetic characters for the suffix.')
            return redirect(url_for('challenge'))

        # Concatenate fragment and suffix to form the complete word
        complete_word = fragment + suffix

        # Check if the complete word exists in the dictionary and is longer than the fragment
        if complete_word in WORDS and len(complete_word) > len(fragment):
            # Challenged player provided a valid word
            message = f"{challenged_player} completed the word to form '{complete_word}', which is valid. {challenger} (Challenger) loses!"
            # Update win tally for challenged player
            if challenged_player_key == 'player1':
                session['player1_wins'] += 1
            else:
                session['player2_wins'] += 1
        else:
            # Challenged player failed to provide a valid word
            message = f"{challenged_player} failed to complete the word with '{complete_word}'. {challenger} (Challenger) wins!"
            # Update win tally for challenger
            if challenger_key == 'player1':
                session['player1_wins'] += 1
            else:
                session['player2_wins'] += 1

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
