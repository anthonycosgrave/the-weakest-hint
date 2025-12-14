# === IMPORTS AND SETUP ===
import os
from dotenv import load_dotenv
from fasthtml.common import *
import random
import json

# Load environment variables from .env file
load_dotenv()
secret_key = os.getenv('SECRET_KEY')

# === GAME DATA AND QUESTION GENERATION ===
def load_games():
    """Load games list from JSON file."""
    with open('games.json', 'r') as f:
        return json.load(f)

def load_descriptions():
    """Load pre-generated game descriptions."""
    with open('game_descriptions.json', 'r') as f:
        return json.load(f)

def create_questions():
    """
    Generate 5 quiz questions with multiple choice answers.
    
    Each question includes:
    - One correct answer (the target game)
    - One game from the same genre (to increase difficulty)
    - Two games from different genres (as decoys)
    
    All choices are randomly shuffled.
    """
    available_games = load_games().copy()
    questions = []

    for i in range(5):
        # Select random game for this question
        idx = random.randint(0, len(available_games) - 1)
        # Remove selected game from available pool to avoid duplicates
        random_game = available_games.pop(idx)
        game_title = random_game['game']
        game_genre = random_game['genre']

        # Try to find a game from the same genre for a "challenging" wrong answer option
        same_genre_games = [g for g in available_games if g['genre'] == game_genre]

        if same_genre_games:
            same_genre_choice = random.choice(same_genre_games)['game']
        else:
            # Fallback to different genre if no same-genre games available
            diff_genre_games = [g for g in available_games if g['genre'] != game_genre]
            same_genre_choice = random.choice(diff_genre_games)['game']
        
        # Select 2 games from different genres as additional wrong answers
        diff_genre_games = [g for g in available_games if g['genre'] != game_genre]
        # Is O(1)
        idx1 = random.randint(0, len(diff_genre_games) - 1)
        # Is O(n) = elements have to be moved after pop()
        first_choice = diff_genre_games.pop(idx1)
        idx2 = random.randint(0, len(diff_genre_games) - 1)
        second_choice = diff_genre_games.pop(idx2)
        diff_genre_choices = [first_choice['game'], second_choice['game']]

        # pick random description for this game
        description = random.choice(descriptions[game_title])

        # Combine all choices and randomise order
        all_choices = [game_title, same_genre_choice] + diff_genre_choices
        random.shuffle(all_choices)
        
        questions.append({
            'description': description,
            'correct_answer': game_title,
            'choices': all_choices
        })

    return questions

# load game descriptions
descriptions = load_descriptions()

# === APP INITIALISATION ===
app, rt = fast_app(pico=False,
                    hdrs=(
                        # Tailwind CSS for styling
                        Script(src="https://cdn.tailwindcss.com"),
                        Link(rel="stylesheet", href="/static/styles.css"),
                    ),
                    # set the default document language to English
                   htmlkw={"lang": "en"},
                   secret_key=secret_key
                   )

app.title = "The Weakest Hint"

# Autofocus new content after htmx swaps to maintain keyboard navigation flow.
# tabindex=-1 allows programmatic focus without adding element to tab order.
focus_attrs = {"tabindex":-1, "autofocus":True}

# === UI COMPONENTS ===
def StartButton():
    """
    Start button with loading state animation.
    Shows "Start Quiz" initially, then "Creating questions..." during request.
    """
    cls = (
        "bg-blue-600 text-white px-8 py-5 rounded text-xl font-semibold "
        "mx-auto block w-fit hover:bg-blue-700 active:ring-4 active:ring-blue-500 active: ring-offset-4 "
        # remove the default browser ':focus-visible' style, replace it with a 4px focus ring
        "focus-visible:outline-none focus-visible:ring-4 "
        # with a 4px offset to make it clear it has keyboard focus
        "focus-visible:ring-blue-500 focus-visible:ring-offset-4 "
        "transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
    )

    # The joy of native Button elements is they are keyboard accessible by default, they
    # can be triggered using Space or Enter! 
    return Button(
        Span("Start Quiz", cls="btn-text"),
        Span(
            Span(cls="loading loading-spinner loading-sm"),
                "Creating questions...",
                cls="btn-loading hidden"
            ),
            hx_get="/generate_questions",
            hx_target="#quiz-content",
            hx_swap="outerHTML settle:0.2s",
            hx_sync="this:replace",
            hx_disabled_elt="this",
            cls = cls
        )

def AnswerButton(choice, idx):
    """
    Coloured answer button with accessibility support.
    Each of the 4 buttons gets a different colour (green, purple, orange, pink).
    Includes high-contrast colours for both light and dark modes.
    """
    # High contrast colour combinations for light/dark mode accessibility
    color_names = ['green', 'purple', 'orange', 'pink']
    color = color_names[idx]
    color_cls = (
        f"bg-{color}-700 text-white active:ring-{color}-500 "
        f"dark:bg-{color}-{500 if color == 'green' else 400} dark:text-black "
        f"hover:bg-{color}-800 dark:hover:bg-{color}-{600 if color == 'green' else 500} "
        f"focus-visible:ring-{color}-500"
    )

    # Fixed height ensures uniform button sizes regardless of text length
    base_cls = (
        "px-6 py-3 rounded text-lg font-semibold focus-visible:ring-4 "
        "focus-visible:ring-offset-4 focus-visible:outline-none "
        "active:ring-4 active:ring-offset-4 transition-shadow "
        "h-24 flex items-center justify-center"
    )

    return Button(
        choice,
        hx_post='/answer',
        hx_vals=f'{{"choice_idx": {idx}}}',  # Pass button index to identify which answer was chosen
        hx_target='#quiz-content',
        hx_swap="outerHTML swap:0.2s settle:0.2s",
        cls=f"{base_cls} {color_cls}"
    )

def ActionButton(text, hx_get_url, **kwargs):
    """
    Reusable blue button component for navigation actions.
    Used for "Next Question", "Play Again", and "See Results" buttons.
    """
    base_cls = (
        "bg-blue-600 text-white px-8 py-5 rounded text-xl font-semibold "
        "hover:bg-blue-700 mx-auto block w-fit transition-shadow "
        "active:ring-4 active:ring-blue-500 active:ring-offset-4 "
        "focus-visible:outline-none focus-visible:ring-4 "
        "focus-visible:ring-offset-4 focus-visible:ring-blue-500"
    )

    return Button(
        text,
        hx_get=hx_get_url,
        hx_target='#quiz-content',
        hx_swap="outerHTML swap:0.2s settle:0.2s",
        cls=base_cls,
        **kwargs
    )

def NextButton():
    """Navigate to next question."""
    return ActionButton("Next Question", '/question')

def PlayAgainButton():
    """Restart the quiz from the beginning."""
    return ActionButton("Play Again!", '/')

def SeeResultsButton():
    """Show final results after last question."""
    return ActionButton("See Results", '/results')

# === ROUTES ===
@rt('/')
def get(session, request):
    """
    Home page / start screen.
    Clears any existing session data and displays the quiz title and start button.
    """
    # Clear session to ensure fresh start
    session.clear()
    
    # Main content section that will be swapped by htmx
    content = Section(
            Span("🎮", cls="text-4xl font-bold block text-center"),
            H1("The Weakest Hint", cls="text-4xl font-bold text-center"),
            P("Can you guess the video game from a bad one-line description?", cls="text-3xl font-bold text-center focus:outline-none", **focus_attrs),
            StartButton(),
            cls="space-y-14",
            id="quiz-content"
        )
    
    # Return just the Section for htmx requests (partial updates),
    # but wrap it in Main for full page loads to maintain proper layout.
    # This prevents duplicate Main elements when "Play Again" is clicked.
    if 'HX-Request' in request.headers:
        return content
    else:
        return Body(Main(content, cls='max-w-[720px] min-h-[500px] mx-auto mt-32 my-8 p-8 rounded-2xl shadow-2xl'))

@rt('/generate_questions')
def get(session):
    """
    Generate quiz questions and initialise session state.
    Called when user clicks "Start Quiz" button.
    """
    # Create 5 random questions with LLM-generated descriptions
    questions = create_questions()
    
    # Initialise session tracking variables
    session['CURRENT_QUESTION_IDX'] = 0  # Track which question we're on
    session['SCORE'] = 0                  # Track correct answers
    session['QUESTIONS'] = questions      # Store all questions for the session
    
    # Display the first question
    return render_question(questions[0], 0)

def render_question(q_data, q_index):
    """
    Render a question with its 4 multiple choice answers.
    Answers are displayed in a 2x2 grid layout.
    """
    
    return Section(
        H1(f"Question {q_index + 1} of 5", cls="text-4xl font-bold text-center"),
        P(I(f"{q_data['description']}."), cls="text-3xl font-bold text-center focus:outline-none"),
        # keyboard accessiblity flow
        P("Is it...", cls="text-2xl font-bold text-center focus:outline-none", **focus_attrs),
        # Answer buttons in 2x2 grid layout
        Div(
            *[AnswerButton(choice, i) for i, choice in enumerate(q_data['choices'])],
            cls="grid grid-cols-2 gap-4"
        ),
        cls="space-y-14",
        id="quiz-content"
    )

@rt('/question')
def get(session):
    """
    Display current question based on session state.
    Used when navigating between questions via "Next Question" button.
    """
    # Get current question index from session
    q_idx = session.get('CURRENT_QUESTION_IDX', 0)
    # Render the question at that index
    return render_question(session['QUESTIONS'][q_idx], q_idx)

@rt('/answer')
def post(session, choice_idx: int):
    """
    Process user's answer and show feedback.
    Updates score if correct, then shows either next question button or results button.
    """
    # Get current question data
    q_idx = session.get('CURRENT_QUESTION_IDX', 0)
    q = session['QUESTIONS'][q_idx]
    
    # Check if the chosen answer (by index) matches the correct answer
    chosen_answer = q['choices'][choice_idx]
    is_correct = (chosen_answer == q['correct_answer'])
    
    # Prepare feedback message based on correctness
    if is_correct:
        session['SCORE'] = session.get('SCORE', 0) + 1
        heading = "Correct!"
        message = f"'{q['correct_answer']}' is the right answer!"
    else:
        heading = "Incorrect!"
        message = f"The correct answer is '{q['correct_answer']}'."

    # Determine what to show next: another question or final results
    if q_idx + 1 < len(session['QUESTIONS']):
        # More questions remaining - show feedback and "Next Question" button
        session['CURRENT_QUESTION_IDX'] = q_idx + 1
        return Section(
            H1(heading, cls="text-4xl font-bold text-center"),
            P(message, cls="text-3xl font-bold text-center py-8 focus:outline-none", **focus_attrs),
            P(NextButton(), cls="py-8"),
            cls="space-y-14",
            id="quiz-content"
        )
    else:
        # Last question - show feedback and "See Results" button
        session['CURRENT_QUESTION_IDX'] = q_idx + 1
        return Section(
            H1(heading, cls="text-4xl font-bold text-center"),
            P(message, cls="text-3xl font-bold text-center py-8 focus:outline-none", **focus_attrs),
            P(SeeResultsButton(), cls="py-8"),
            cls="space-y-14",
            id="quiz-content"
        )

@rt('/results')
def results(session):
    """
    Display final quiz results with score and performance message.
    Message and emoji vary based on how many questions were answered correctly.
    """
    score = session.get('SCORE', 0)
    total = 5
    
    # Build results message
    if score == total:
        emoji = "🏆"
        message = "Every answer landed like a headshot. Boom!"
    elif score >= 4:
        emoji = "🌟"
        message = "One slip, but the rest were clean combos."
    elif score >= 3:
        emoji = "👾"
        message = "Not quite a speed run."
    elif score >= 2:
        emoji = "🕹️"
        message = "Button masher!"
    else:
        emoji = "📺"
        message = "Every expert was once a beginner."
    
    return Section(
        Span(emoji, cls="text-3xl font-bold block text-center"),
        H1(f"{score} out of {total}", cls="text-4xl font-bold text-center"),
        P(message, cls="text-2xl font-bold text-center focus:outline-none", **focus_attrs),
        PlayAgainButton(),
        cls="space-y-14",
        id="quiz-content"
    )

serve()
