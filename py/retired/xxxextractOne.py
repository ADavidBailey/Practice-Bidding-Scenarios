import os
import re
import requests
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description="Extract dealer code from a single file.")
parser.add_argument("--file_path", type=str, required=True, help="Path to the input file.")
args = parser.parse_args()

# Extract arguments
file_path = args.file_path
print("Processing file: " + file_path)

# Directory to save output file
PBS = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios")
output_dir = os.path.join(PBS, 'dlr')
os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

# Regular expression pattern to match text enclosed in backticks spanning multiple lines
pattern = r'`(.*?)`'

# From CHATGPT
def extract_button_and_title(text):
    pattern = r"Button,(.*?),\\n\\--- (.*)"
    match = re.search(pattern, text)
    if match:
        button_text = match.group(1).strip()
        scenario_title = match.group(2).strip()
        return button_text, scenario_title
    return None, None

def extract_text_in_backticks(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        quotes_pattern = r',\s*"([^"]+)"'
        quotes_matches = re.findall(quotes_pattern, content)
        
        dealer = "south"
        if quotes_matches:
            if quotes_matches[0] == "N":
                dealer = "north"
            elif quotes_matches[0] == "S":
                dealer = "south"
            elif quotes_matches[0] == "E":
                dealer = "east"
            elif quotes_matches[0] == "W":
                dealer = "west"
        
        matches = re.findall(pattern, content, re.DOTALL)
        for i, match in enumerate(matches, 1):
            processed_text = process_extracted_text(match, dealer)
            output_file_path = os.path.splitext(os.path.basename(file_path))[0] + ".dlr"
            output_file_path = os.path.join(output_dir, output_file_path).replace('\\', '/')
            with open(output_file_path, 'w') as output_file:
                output_file.write(processed_text)

def process_extracted_text(extracted_text, dealer):
    processed_text = []
    action = False
    lines = extracted_text.split('\n')

    # Ignore all dealer, generate, or produce statements
    lines = [line for line in lines if not line.startswith(("dealer ", "generate ", "produce ", "printoneline"))]

    processed_text.append(f"# {os.path.basename(file_path)}")
    processed_text.append(f"generate {generate}")
    processed_text.append(f"produce {produce}")
    processed_text.append(f"dealer {dealer}")

    for line in lines:
        if line.startswith("action"):
            action = True

        if line.startswith("Import"):
            split_string = line.replace("github.com", "raw.githubusercontent.com").replace("blob/", "").split(',')
            url = split_string[1]
            response = requests.get(url)
            if response.status_code == 200:
                content = response.text
                processed_text.append(content)
        else:
            processed_text.append(line)

    if not action:
        processed_text.append("action printpbn\n")
    else:
        processed_text.append("printpbn\n")

    return '\n'.join(processed_text)

# Process the provided file
if os.path.isfile(file_path) and not file_path.endswith('.DS_Store'):
    extract_text_in_backticks(file_path)
    print("Processing completed.")
else:
    print(f"File does not exist or is not valid: {file_path}")
