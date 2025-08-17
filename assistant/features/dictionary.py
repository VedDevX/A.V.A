import requests  # Import the 'requests' library to make HTTP requests (like calling an API) and fetch data

# ===============================
# FUNCTION: get_meaning()
# ===============================
def get_meaning(word: str) -> str:
    """
    Fetch meaning of a given word using the Free Dictionary API.
    API Used: https://api.dictionaryapi.dev/
    
    Parameters:
        word (str): The word whose meaning you want to fetch.
    
    Returns:
        str: The first meaning of the word if found,
             otherwise returns "Meaning not found."
    """

    # 1. Construct the API URL dynamically for the word
    # Example: if word="umbrella", the URL becomes:
    # https://api.dictionaryapi.dev/api/v2/entries/en/umbrella
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    try:
        # 2. Send a GET request to the API
        # - requests.get() makes an HTTP GET call to the API
        # - timeout=5 means wait at most 5 seconds for a response
        # - .json() converts the JSON response from the API into a Python dictionary/list
        res = requests.get(url, timeout=5).json()
        
        # 3. Extract the first definition from the JSON response
        # The API returns a structured JSON like this:
        # res[0] → First result (there may be multiple results)
        # ["meanings"][0] → First meaning category (like noun, verb, etc.)
        # ["definitions"][0]["definition"] → The actual meaning text
        return res[0]["meanings"][0]["definitions"][0]["definition"]
    
    except Exception:
        # 4. If:
        # - The API is down
        # - The word is not found
        # - The JSON structure is different/unexpected
        # Then we safely return this message instead of crashing the program
        return "Meaning not found."
