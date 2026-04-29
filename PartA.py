import sys

def tokenize(file_path):
    """
    Reads a text file and returns a list of alphanumeric tokens.

    Runtime complexity: O(n) where n is the number of characters in the file.
    Each character is read once, and tokenization is done in a single pass through the file.
    """
    tokens = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            current_token = []

            # Read the file character by character
            while True:
                char = file.read(1)
                if not char: # End of word
                    break
                if char.isalnum():
                    current_token.append(char.lower()) # Convert to lowercase for case-insensitivity
                else:
                    if current_token:
                        yield ''.join(current_token)
                        current_token = []
            
            if current_token:
                yield ''.join(current_token)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    return tokens


def computeWordFrequencies(tokens):
    """
    Counts occurrences of each unique token in the token list.

    Runtime complexity: O(n) where n is the number of tokens.
    Each token is processed once to update the frequency count in the dictionary.
    Dictionary operations (get and set) are on average O(1), making the overall complexity linear with respect to the number of tokens.
    """
    frequencies = {}
    for token in tokens:
        frequencies[token] = frequencies.get(token, 0) + 1 # Increment the count for the token, initializing to 0 if it doesn't exist
    return frequencies


def printFrequency(frequencies):
    """
    Prints tokens ordered by decreasing frequency.
    Format: <token> - <frequency>

    Runtime complexity: O(n log n) where n is the number of unique tokens.
    Sorting the frequency map takes O(n log n) time, where n is the number of unique tokens.
    The subsequent printing of the sorted list is O(n). Thus, the overall complexity is dominated by the sorting step.
    """
    # Sort the frequency map by number of occurrences (descending) and then by alphabetical order (ascending)
    sorted_freq = sorted(frequencies.items(), key=lambda x: (-x[1], x[0]))
    for token, frequency in sorted_freq:
        print(f"{token} - {frequency}")



def main():
    if len(sys.argv) < 2:
        print("Error: No file argument provided.") # Check if a file argument is provided
        return
    
    file_path = sys.argv[1]
    token_list = tokenize(file_path)
    freq_map = computeWordFrequencies(token_list)
    printFrequency(freq_map)

if __name__ == "__main__":
    main()