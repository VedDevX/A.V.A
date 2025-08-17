# =======================================================================
# Chatbot Module
# =======================================================================
# This module contains all the logic for:
# - Matching user input to predefined intents
# - Handling typos with fuzzy matching
# - Detecting dictionary queries (like "define umbrella")
# - Detecting calculator queries and to-do commands
# - Returning appropriate bot responses
# =======================================================================

import random  # Used to randomly select a reply from a list of responses
import re      # Used to define regex patterns and search text
from difflib import get_close_matches  # Used for typo-tolerance (e.g., "helo" -> "hello")

# Import dictionary, calculator and todo features from assistant/features package.
# These are functions that live in other files and are re-used here.
from assistant.features.dictionary import get_meaning
from assistant.features.calculator import evaluate
from assistant.features.todo import add_task, get_tasks, remove_task, mark_done


# =======================================================================
# INTENTS (patterns + responses)
# =======================================================================
# Intents are like categories of conversation.
# Each intent has:
#   - "patterns": example user phrases we want to recognize
#   - "responses": replies the assistant will randomly pick from
# NOTE: We keep this data-driven so the matching logic below is generic.
intents = {
    # ---------------- Small Talk ----------------
    "greet": {
        # patterns -> list of example phrases that signal a greeting intent
        "patterns": [
            "hi", "hello", "hey", "good morning", "good evening",
            "morning", "gm", "good afternoon", "afternoon",
            "good night", "night", "hiya", "yo", "sup",
            "hey there", "what’s up", "whats up", "wassup", "wazzup",
            "long time no see", "nice to meet you", "pleased to meet you",
            "howdy", "greetings", "salutations",
            "hola", "bonjour", "namaste", "salaam", "ciao", "aloha",
            "hiya buddy", "hi assistant", "hello friend", "yo assistant",
            "are you there", "anyone there", "knock knock", "hi bot",
            "hello ai", "hello there", "hi there"
        ],
        # responses -> possible replies the bot can use for this intent
        "responses": [
            "Hello! How can I help you today?",
            "Hey there!",
            "Hi, what’s up?",
            "Hello friend! How are you doing?",
            "Greetings! How may I help?",
            "Hi there, nice to see you!",
            "Hey! I’m here to assist you."
        ]
    },

    "goodbye": {
        # patterns to recognize user saying goodbye
        "patterns": [
            "bye", "goodbye", "see you", "see ya", "later",
            "talk to you later", "catch you later", "farewell",
            "take care", "see you soon", "bye bye",
            "good night", "nighty night", "adios", "ciao"
        ],
        # possible responses when user says goodbye
        "responses": [
            "Goodbye!",
            "See you later!",
            "Bye! Take care.",
            "Catch you later!",
            "Farewell, friend!",
            "Bye bye 👋"
        ]
    },

    "thanks": {
        # patterns for gratitude
        "patterns": [
            "thanks", "thank you", "thx", "ty", "thanks a lot",
            "thank you very much", "many thanks", "appreciate it",
            "thanks so much", "cheers", "much obliged"
        ],
        # responses to say when user thanks the bot
        "responses": [
            "You're welcome!",
            "Glad I could help!",
            "Anytime!",
            "No problem at all!",
            "My pleasure!",
            "Don’t mention it 🙂"
        ]
    },

    "how_are_you": {
        # patterns asking how bot is doing
        "patterns": [
            "how are you", "how are you doing", "how’s it going",
            "how do you do", "you good", "are you okay",
            "what’s up with you", "how have you been"
        ],
        # responses describing bot state
        "responses": [
            "I’m doing great! How about you?",
            "I’m fine, thanks for asking.",
            "I’m feeling awesome today!",
            "I’m all good — ready to help you!",
            "I’m doing well, how are you doing?"
        ]
    },

    "who_are_you": {
        # patterns where user asks identity of the bot
        "patterns": [
            "who are you", "what are you", "what is your name",
            "who am i talking to", "identify yourself"
        ],
        # responses telling who the bot is
        "responses": [
            "I’m your AI Virtual Assistant 🤖",
            "I’m Ava, your personal AI helper!",
            "I’m your assistant, here to chat and help you."
        ]
    },

    "feelings": {
        # patterns where user share feelings or mood
        "patterns": [
            "i am sad", "i feel lonely", "i’m happy", "i am excited",
            "i feel bored", "i’m angry", "i feel nervous",
            "i feel good", "i feel great"
        ],
        # responses that show empathy or encouragement
        "responses": [
            "I hear you. Do you want to talk about it?",
            "That’s great to hear! 🎉",
            "I’m here for you whenever you need me.",
            "It’s okay to feel that way sometimes.",
            "I’m glad you’re sharing your feelings with me."
        ]
    },

    "compliment": {
        # patterns indicating the user complimented the bot
        "patterns": [
            "you are smart", "you are nice", "you are awesome",
            "you are cool", "you are funny", "you are helpful",
            "good job", "well done"
        ],
        # friendly, grateful responses to compliments
        "responses": [
            "Aww, thank you! 😊",
            "That means a lot!",
            "Glad you think so!",
            "You’re awesome too!"
        ]
    },

    "insult": {
        # patterns where user insults the bot
        "patterns": [
            "you are stupid", "you are dumb", "you are useless",
            "you are bad", "you are annoying", "you are boring"
        ],
        # calm, non-escalating responses to insults
        "responses": [
            "That’s not very nice 😔",
            "I’m still learning, please be patient with me.",
            "I’m sorry you feel that way."
        ]
    },
}


# =======================================================================
# Precompile regex patterns for speed
# =======================================================================
# Converting simple patterns into compiled regex objects makes matching faster.
# We wrap each pattern with word-boundaries (\b) so "hi" matches "hi" but not "ship".
_compiled_intents = {
    intent: {
        # For each plain pattern string, create a case-insensitive regex like r"\bhello\b"
        "patterns": [re.compile(rf"\b{re.escape(p)}\b", re.IGNORECASE) for p in data["patterns"]],
        # Keep responses as-is
        "responses": data["responses"]
    }
    for intent, data in intents.items()
}


# =======================================================================
# Build dictionary for typo tolerance
# =======================================================================
# This mapping collects single-word patterns and the intent they belong to.
# It is used later with difflib.get_close_matches to tolerate typos like "helo".
_single_word_to_intent = {}
for intent, data in intents.items():
    for p in data["patterns"]:
        # Only consider single-word patterns (no spaces) for this simple typo handling
        if " " not in p:
            _single_word_to_intent[p] = intent


# =======================================================================
# Smart fallback replies (randomized)
# =======================================================================
# If nothing else matches, pick a friendly fallback response to keep the
# conversation natural instead of always saying "Sorry".
_fallback_responses = [
    "Sorry, I didn’t get that. Could you rephrase?",
    "Hmm, I’m not sure I understood you 🤔",
    "I didn’t quite catch that, can you try again?",
    "I’m still learning! Can you say it differently?",
    "Could you clarify what you mean?",
    "Oops, that went over my head. Can you explain again?"
]


# =======================================================================
# Helper Function: Normalize text
# =======================================================================
def _normalize(s: str) -> str:
    """
    Clean the input text:
    - Lowercase the string
    - Remove punctuation and special characters (keeps letters/numbers/spaces)
    - Trim leading/trailing whitespace
    Example: "Hello!!" -> "hello"
    """
    # re.sub replaces any char not a-z,0-9 or whitespace with empty string
    return re.sub(r"[^a-z0-9\s]+", "", s.lower()).strip()


# =======================================================================
# Detect dictionary queries
# =======================================================================
def _is_dictionary_query(user_msg: str):
    """
    Check if the user is asking for a meaning/definition.
    Examples:
      - "meaning of apple"
      - "what does umbrella mean"
      - "define car"
      - "definition of computer"

    If matched -> return the extracted word/phrase
    Else -> return None
    """
    # regex patterns used to extract the target word/phrase
    patterns = [
        r"meaning of (.+)",
        r"what does (.+) mean",
        r"define (.+)",
        r"definition of (.+)"
    ]
    for pat in patterns:
        # search case-insensitively in the raw user_msg
        match = re.search(pat, user_msg, re.IGNORECASE)
        if match:
            # return the captured group (strip extra spaces)
            return match.group(1).strip()
    return None


# =======================================================================
# Detect Calculator queries
# =======================================================================
def _is_calculator_query(user_msg_raw: str):
    """
    Detect calculator queries from the raw (lowercased) message so operators remain.
    Returns a clean math expression string or None.

    Supports forms like:
      - "what is 5+7"
      - "calculate 12 * 8"
      - "2 + 2"
    """
    # Work on a lowercased version to make phrase detection simpler
    msg = user_msg_raw.lower()

    # 1) Phrasal queries that contain an expression after a verb
    phrasal = [
        r"^\s*what\s+is\s+(.+)$",
        r"^\s*calculate\s+(.+)$",
        r"^\s*solve\s+(.+)$",
    ]
    for pat in phrasal:
        m = re.search(pat, msg)
        if m:
            # group(1) is the expression part after the phrase ("what is", etc.)
            expr = m.group(1)
            # Keep only characters that are valid in math expressions:
            # digits, + - * / % . parentheses and spaces
            expr = re.sub(r"[^0-9+\-*/%.()\s]", "", expr)
            expr = expr.strip()
            # Ensure there's at least one operator so plain numbers are not treated as expressions
            if re.search(r"[+\-*/%]", expr):
                return expr

    # 2) If the whole message looks like a math expression (digits + ops + spaces)
    if re.fullmatch(r"[0-9+\-*/%.()\s]+", msg):
        # require at least one operator to avoid treating single numbers like "22" as expressions
        if re.search(r"[+\-*/%]", msg):
            return msg.strip()

    # Not a calculator query
    return None


# =======================================================================
# Detect To-DO queries
# =======================================================================
def _is_todo_query(user_msg: str):
    """
    Returns a tuple (command, arg) if a todo command is detected:
    - ("add", "buy milk")      for "add task buy milk"
    - ("show", None)           for "show task" or "show tasks"
    - ("remove", "brush teeth") for "remove task brush teeth"
    - ("done", 2)              for "mark done 2" (task id)
    """
    # Work with a normalized lowercase string for consistent checks
    user_msg = user_msg.strip().lower()

    # If message starts with "add task ", return ("add", <title>)
    if user_msg.startswith("add task "):
        return ("add", user_msg[9:].strip())

    # Match "show task" or "show tasks" (question mark in regex is optional s)
    elif re.match(r"show tasks?", user_msg):
        return ("show", None)

    # If user wants to remove by name or id: take everything after "remove task "
    elif user_msg.startswith("remove task "):
        # Extract substring after the command
        task_name = user_msg[12:].strip()
        if task_name:
            # return the task identifier (string) — removal logic handles both id & title
            return ("remove", task_name)

    # If message starts with "mark done <number>" treat as numeric id
    elif user_msg.startswith("mark done "):
        m = re.match(r"mark done (\d+)", user_msg)
        if m:
            return ("done", int(m.group(1)))

    # Not a todo command
    return None


# =======================================================================
# MAIN FUNCTION: get_response()
# =======================================================================
def get_response(user_msg: str) -> str:
    """
    Main brain of the assistant.
    Input: user message (string)
    Output: chatbot reply (string)
    """

    # 1. Handle completely empty input (None, empty string, whitespace-only)
    if not user_msg or not user_msg.strip():
        return "Please say something so I can help."

    # 2. Keep two forms of the message:
    #    raw_lower -> full lowercased text (keeps operators and punctuation)
    #    normalized -> cleaned text used for intent matching (no punctuation)
    raw_lower = user_msg.lower()
    normalized = _normalize(user_msg)
    # If normalized is empty (e.g., user typed only symbols like "!!!") respond accordingly
    if not normalized:
        return "Please say something so I can help."

    # 3. Try to match explicit intents first using compiled regex patterns
    for intent, data in _compiled_intents.items():
        for pattern in data["patterns"]:
            # pattern.search checks if the regex appears anywhere in the user message
            if pattern.search(user_msg):
                # If matched, return a random response from that intent
                return random.choice(data["responses"])

    # 4. Dictionary lookup detection (e.g., "meaning of umbrella")
    word = _is_dictionary_query(normalized)
    if word:
        # get_meaning calls the dictionary feature and returns a string
        meaning = get_meaning(word)
        # If meaning exists return it, otherwise inform user it wasn't found
        return meaning if meaning else f"Sorry, I couldn’t find the meaning of '{word}'."

    # 5. Calculator detection (e.g., "2 + 2" or "what is 5+7")
    expr = _is_calculator_query(raw_lower)
    if expr:
        # evaluate runs the safe-eval logic in features/calculator.py
        result = evaluate(expr)
        return f"The result is: {result}"

    # 6. To-do commands (add/show/remove/mark done)
    todo_cmd = _is_todo_query(user_msg)
    if todo_cmd:
        cmd, arg = todo_cmd
        if cmd == "add":
            # add_task returns a message string (success/error)
            return add_task(arg)
        elif cmd == "show":
            # get_tasks returns a list of task dicts; we format them for display
            tasks_list = get_tasks()
            if not tasks_list:
                return "No tasks found."
            # Format: "1. [Pending] Buy milk"
            formatted = [f"{t['id']}. [{'Done' if t['status']=='done' else 'Pending'}] {t['title']}" for t in tasks_list]
            # Join with newline so frontend can display multiple lines
            return "\n".join(formatted)
        elif cmd == "remove":
            # remove_task in features expects an integer id OR the module may accept title;
            # here we attempt numeric removal first; if arg is not numeric, try removing by title.
            try:
                # If arg looks like an integer string, convert and call remove_task(id)
                task_id = int(arg)
                return remove_task(task_id)
            except Exception:
                # Otherwise try to remove by title (string). Some implementations of remove_task
                # accept title, but if not, you may need to implement that logic inside features.todo.
                # For now call remove_task with arg and let the feature handle it or return "Task not found".
                return remove_task(arg)
        elif cmd == "done":
            # Marking done. Try numeric id first.
            try:
                task_id = int(arg)
                return mark_done(task_id)
            except Exception:
                # If arg was not numeric, attempt to find by title using tasks API (if supported there)
                return mark_done(arg)

    # 7. Typos / fuzzy matching (single tokens)
    tokens = normalized.split()
    vocab = list(_single_word_to_intent.keys())  # list of known single-word patterns
    if tokens:
        for t in tokens:
            # get_close_matches finds nearest word from vocab for token t
            match = get_close_matches(t, vocab, n=1, cutoff=0.80)
            if match:
                # If a close match was found, map it back to the intent and respond
                intent = _single_word_to_intent[match[0]]
                return f"(Did you mean **{match[0]}**?)\n{random.choice(intents[intent]['responses'])}"

    # 8. Typos / fuzzy matching on whole message (helps when multiple words)
    all_patterns = [p for data in intents.values() for p in data["patterns"]]
    match = get_close_matches(normalized, all_patterns, n=1, cutoff=0.75)
    if match:
        # Find which intent this best-matching pattern belongs to
        for intent, data in intents.items():
            if match[0] in data["patterns"]:
                return f"(Did you mean **{match[0]}**?)\n{random.choice(data['responses'])}"

    # 9. Nothing matched -> return a randomized friendly fallback reply
    return random.choice(_fallback_responses)
