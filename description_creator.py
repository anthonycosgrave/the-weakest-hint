import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import json
import time

load_dotenv()

# Initialise Hugging Face client for LLM access
client = InferenceClient(
    provider="auto",
    api_key=os.getenv('HF_READ_API_KEY')
)

def load_games():
    with open('games.json', 'r') as f:
        return json.load(f)

# === LLM INTERACTION ===
def hf_connect(content):
    """Send prompt to Hugging Face LLM and return response."""
    response = client.chat_completion(
        model="google/gemma-2-2b-it",
        messages=[{"role": "user", "content": content}]
    )
    return response

def clean_description(description):
    """
    Clean up LLM response to ensure it's concise and properly formatted.
    
    Handles common issues:
    - Removes wrapping quotation marks
    - Strips incomplete endings (e.g. "and", "a", "the")
    - Limits to 7 words maximum
    - Ensures minimum 4 words or uses fallback
    """
    # Words that shouldn't appear at the end of a description
    bad_endings = {'a', 'an', 'the', 'and', 'or', 'to', 'at', 'on', 'in', 'with', 'for', 'by', 'of'}
    
    # Take only the first line and first sentence
    line = description.split('\n')[0]
    first_sentence = line.split('. ')[0]
    first_sentence = first_sentence.replace('*', '')
    
    # Remove quotation marks that wrap the entire description
    if (first_sentence.startswith('"') and first_sentence.endswith('"')) or \
       (first_sentence.startswith("'") and first_sentence.endswith("'")):
        first_sentence = first_sentence[1:-1]
    
    # Split into words and limit to 7
    words = first_sentence.split()
    words = words[:7]
    
    # Remove trailing words that leave the description incomplete
    # Keep at least 4 words to maintain meaning
    while len(words) > 4 and words[-1].lower().rstrip(',.!?') in bad_endings:
        words.pop()
    
    # If too short after cleaning, use generic fallback
    if len(words) < 4:
        return "Mystery game with secrets"
    
    # Capitalise first word for proper formatting
    if words:
        words[0] = words[0].capitalize()
    
    return ' '.join(words).strip()

def generate_game_description(game):
    """
    Generate a humorous 5-word description for a game using LLM.
    Returns cleaned description or fallback on error.
    """
    # Detailed prompt with examples to guide the LLM's output style
    prompt=f"""In exactly 5 words, describe the core mechanics of '{game}' in a hilarious and quirky way.

        Rules:
        - Your response must be exactly 5 words
        - Must be a complete thought within those 5 words, not cut off mid-sentence
        - Do not wrap your response in quotation marks
        - Use only plain text, no special characters, no emojis or formatting
        - Do not use the game's name, character names, genre labels, or words from the title
        - Include unique details to distinguish it from similar games

        Examples:
        Minesweeper - Guessing with explosive consequences
        Doom - Angry metal shotguns demon confetti
        Halo - Space monks argue with bullets
        Pong - Two lines chasing one ball
        Left 4 Dead - Friendships tested by screaming zombies
        Pac-Man - Circle in relentless fruit binge
        Asteroids - Blast rocks make smaller problems

        Respond with only the 5-word description based on the rules provided. Do not return anything else."""
    try:
        r = hf_connect(prompt)
        return clean_description(r.choices[0].message.content)
    except Exception as e:
        # Log error for debugging but don't crash the game
        print(f"\n{game}: ERROR - {e}")
        return "Mystery game with secrets"
    

def generate_descriptions_for_all_games():
    games = load_games()
    
    # Load existing descriptions if file exists (for resuming)
    # HF has at times chucked up errors so to handle interruptions
    try:
        with open('game_descriptions.json', 'r') as f:
            descriptions = json.load(f)
    except FileNotFoundError:
        descriptions = {}
    
    for game in games:
        game_title = game['game']
        
        # If we had to resume: Skip if already done!
        if game_title in descriptions:
            print(f"Skipping {game_title} - already exists")
            continue
        
        game_descriptions = []
        retry_count = 0
        max_retries = 3  # Stop after 3

        print(f"For {game_title} ...")
        while len(game_descriptions) < 5:
            desc = generate_game_description(game_title)
            
            if desc == "Mystery game with secrets":
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"Max retries reached for {game_title} - stopping")
                    break
                print(f"Rate limited - sleeping 60s... (attempt {retry_count}/{max_retries})")
                time.sleep(60)
                continue
    
            game_descriptions.append(desc)
            retry_count = 0  # Reset on success
            time.sleep(5)
        
        # # Save after each game
        descriptions[game_title] = game_descriptions
        with open('game_descriptions.json', 'w') as f:
            json.dump(descriptions, f, indent=2)
        
        print(f"Completed {game_title}")
        time.sleep(30)  # Rate limit protection

def fix_mystery_descriptions():
    """Replace 'mystery game with secrets' descriptions with new ones."""
    with open('game_descriptions.json', 'r') as f:
        descriptions = json.load(f)
    
    for game_title, descs in descriptions.items():
        # Find indices of mystery descriptions
        mystery_indices = [i for i, d in enumerate(descs) if d == "Mystery game with secrets"]
        
        if not mystery_indices:
            continue
        
        print(f"Fixing {len(mystery_indices)} descriptions for {game_title}")
        
        for idx in mystery_indices:
            new_desc = generate_game_description(game_title)
            
            # Retry if we get another mystery
            retry_count = 0
            while new_desc == "Mystery game with secrets" and retry_count < 5:
                print(f"  Rate limited - sleeping 60s...")
                time.sleep(60)
                new_desc = generate_game_description(game_title)
                retry_count += 1
            
            descriptions[game_title][idx] = new_desc
            time.sleep(5)
        
        # Save after each game
        with open('game_descriptions.json', 'w') as f:
            json.dump(descriptions, f, indent=2)
    
    print("All mystery descriptions fixed!")


if __name__ == "__main__":
    generate_descriptions_for_all_games()
    # Or: fix_mystery_descriptions()
