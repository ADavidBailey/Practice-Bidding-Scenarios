import os
import re
import requests
#import hashlib
import argparse

parser = argparse.ArgumentParser(description="Extract dealer code")
parser.add_argument("--generate", type=int, default=100000000, help="Number to generate")
parser.add_argument("--produce", type=int, default=500, help="Number to produce")
parser.add_argument("--scenario", type=str, default="", help="Name of scenario")
args = parser.parse_args()
generate = args.generate
produce = args.produce
scenario = args.scenario
print("generating " + str(generate))
print("producing  " + str(produce))
print("scenario  " + str(scenario))

# Directory containing the files
PBS = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios")
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
        button_title = match.group(2).strip().replace('\\n\\','')
        return button_text, button_title
    else:
        return None, None

def extract_text_in_backticks(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        if scenario != "":
            button_text, button_title = extract_button_info(content)
            if button_title != scenario:
                print("Ignoring " + file_path)
                # if button_title:
                #     print("Button title " + button_title + " does not match scenario " + scenario)
                # else:
                #     print("Button title not found")
                return
            else:
                header = f"# button-text: {button_text}\n" 
                header += f"# button-title: {button_title}\n" 

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
            print(output_file_path)
            with open(output_file_path, 'w') as output_file:
                # Save the processed text to the .dlr file
                # seed = calculate_seed(file_path)
                # We seed based on filename, then we have reproduceale results, but different seed pr, file

                # Insert header in file
                processed_text = header + processed_text

                output_file.write(processed_text)
                # print(f'echo ./dealerv2 {output_file_path}  -s {seed} ')
                # print(f'./dealerv2 {output_file_path} -s  {seed} > ./pbn/{ os.path.splitext(os.path.basename(file_path))[0].replace(" ","-").replace("(", "").replace(")", "").replace("&", "and").replace("+", "_")}.pbn ', end="\n")

# Function to process the extracted text


def process_extracted_text(extracted_text, dealer):
    processed_text = []
    
    action = False
    #condition = False
    #generate_added = False
    #produce_added = False

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
    processed_text.append(f"generate {generate}") # from default or arg
    processed_text.append(f"produce {produce}")   # from default or arg
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

# List all files in the directory
n_files = 0
input_filepath = os.path.join(PBS + '/PBS/')
for filename in os.listdir(input_filepath):
    file_path = os.path.join(input_filepath, filename)
    
    # Check if it's a file
    if os.path.isfile(file_path) and not file_path.endswith('.DS_Store'):
        extract_text_in_backticks(file_path)
        n_files = n_files + 1
        #if n_files>2:
        #    break
print("number of .dlr files = " + str(n_files))
