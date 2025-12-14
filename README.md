# 🎮 The Weakest Hint

A video game guessing quiz where players try to identify classic and popular games from intentionally bad AI-generated descriptions. 

The games are based on Wikipedia's ["List Of Video Games Considered The Best"](https://en.wikipedia.org/wiki/List_of_video_games_considered_the_best).

## Screenshots

### Dark 
![Quiz question screen showing Question 5 of 5. "Watch people die of boredom, plants burst." with four coloured buttons in dark mode](/images/dark-mode-screenshot.png)

### Light
![Quiz question screen showing Question 1 of 5. "Run until everything is a giant blob." with four coloured buttons in light mode](/images/light-mode-screenshot.png)

## Features

- AI-generated humorous descriptions using Gemini via Hugging Face
- Multiple choice questions with 4 options per round
- 5 rounds per game with score tracking
- Responsive design with dark/light mode support
- Keyboard accessible interface

## Accessibility

- Supports light and dark colour schemes based on system preferences
- High contrast colour palettes meeting WCAG AA standards
- Full keyboard navigation with visible focus indicators

## Tech Stack

- **Backend**: [FastHTML](https://www.fastht.ml/), Python 3.10+
- **Frontend**: [Tailwind CSS v3](https://v3.tailwindcss.com/), [HTMX](https://htmx.org)
- **AI**: Gemma-2-2b-it via [Hugging Face Inference API](https://huggingface.co/google/gemma-2-2b-it) to generate descriptions stored in `game_descriptions.json`  
- **Data**: [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) used to parse and pre-process games stored in `games.json`  

## Local Setup

### Running the Game
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with a SECRET_KEY: `SECRET_KEY=<your_key_here>`
4. Run the application: `python app.py`

## How to Play
1. Select "Start Quiz" to generate 5 questions
2. Read the cryptic description
3. Choose from 4 possible games
4. Get instant feedback and continue to the next question
5. See your final score and play again!

## Deployment

**Live Demo**: ["The Weakest Hint" on Hugging Face Spaces](https://huggingface.co/spaces/acosgrave/the-weakest-hint)

**Note**: The live demo version uses hidden form fields instead of sessions to work around Hugging Face Spaces' iframe cookie restrictions. The source code for that version is available in this [separate Hugging Face repository](https://huggingface.co/spaces/acosgrave/the-weakest-hint/tree/main).

## Licence

Code is licensed under the MIT License. See LICENSE file for details.
