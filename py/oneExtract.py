import os
import re
import requests
import argparse

parser = argparse.ArgumentParser(description="Extract dealer code")
parser.add_argument("--scenario", type=str, default="*", help="Name of scenario (omit for all)")
args = parser.parse_args()
scenario = args.scenario

# Directory containing the files
PBS = ".."
# Regular expression pattern to match text enclosed in backticks spanning multiple lines
pattern = r'`(.*?)`'

# Function to find and process text enclosed in backticks and save to a .dlr file

def extract_button_info(pbs_content):
    # Regular expression to match the button lines
    pattern = r'Button,([^,]+),\\n\\\n--- ([^\n]+)'
    match = re.search(pattern, pbs_content)
    if match:
        button_text = match.group(1).strip().replace('\\n\\','')
        scenario_title = match.group(2).strip().replace('\\n\\','')
        return button_text, scenario_title
    else:
        return None, None

def extract_text_in_backticks(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        button_text, scenario_title = extract_button_info(content)
        header = f"# button-text: {button_text}\n" 
        header += f"# scenario-title: {scenario_title}\n" 

        # Pattern to find text in double quotes following a comma and a space
        quotes_pattern = r',\s*"([^"]+)"'
        quotes_matches = re.findall(quotes_pattern, content)
        dealer = "south"
        if len(quotes_matches) > 0:
            if quotes_matches[0] == "N":
                dealer = "north"
            if quotes_matches[0] == "S":
                dealer = "south"
            if quotes_matches[0] == "E":
                dealer = "east"
            if quotes_matches[0] == "W":
                dealer = "west"
        suffix = ".dlr"

        matches = re.findall(pattern, content, re.DOTALL)
        for i, match in enumerate(matches, 1):
            # Process the extracted text
            processed_text = process_extracted_text(match, dealer)
            
            output_file_path = os.path.splitext(os.path.basename(file_path))[0] + suffix
            output_file_path = os.path.join(PBS + '/dlr', output_file_path).replace('\\', '/')
            with open(output_file_path, 'w') as output_file:
                # Save the processed text to the .dlr file

                # Insert header in file
                processed_text = header + processed_text

                output_file.write(processed_text)

# Function to process the extracted text

def process_extracted_text(extracted_text, dealer):
    processed_text = []
    
    action = False

    lines = extracted_text.split('\n')

    # Ignore all dealer, generate, or produce statements
    for line in lines[:]:  # Iterate through a copy of the original list           
        if line.startswith("dealer "):
            lines.remove(line)
        if line.startswith("generate "):
            lines.remove(line)             
        if line.startswith("produce "):
            lines.remove(line)
        if line.startswith("printoneline"):
            lines.remove(line)
    
    # The first 4 lines of each .dlr file...
    processed_text.append(f"# {filename}")
    processed_text.append(f"dealer {dealer}")     # from setDealerCode

    for line in lines[:]:  # Iterate through a copy of the original list
        if line.startswith("action"):
            action = True  # append or create

        if line.startswith("Import"):
            # Splitting the string by comma to get the URL
            split_string = line.replace("github.com","raw.githubusercontent.com").replace("blob/", "").split(',')
            url = split_string[1]  # Assuming the URL is at index 1 after splitting
            # Fetching the content from the URL
            response = requests.get(url)            
            # Checking if the request was successful (status code 200)           
            if response.status_code == 200:
                content = response.text  # Content of the URL
                processed_text.append(content)
            lines.remove(line)
        else:
            processed_text.append(line)
            lines.remove(line)    

    if not action:
        processed_text.append("action printpbn\n")
    else:
        processed_text.append("printpbn\n")
    return '\n'.join(processed_text)


if scenario != "*":
    # Do a single scenario
    filename = scenario
    file_path = os.path.join('..', 'pbs', filename)
    if os.path.isfile(file_path):
        extract_text_in_backticks(file_path)
else:
    # List all files in the directory
    n_files = 0
    for filename in os.listdir(os.path.join('..', 'pbs')):
        file_path = os.path.join('..', 'pbs', filename)
    
        # Check if it's a file
        if os.path.isfile(file_path) and not file_path.endswith('.DS_Store'):
            extract_text_in_backticks(file_path)
            n_files = n_files + 1
            #if n_files>2:
            #    break
    print("number of .dlr files = " + str(n_files))
