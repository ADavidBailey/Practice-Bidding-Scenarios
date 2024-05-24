import os

# Directory containing the files
directory_path = './pbn'

# Regular expression pattern to match text enclosed in backticks spanning multiple lines
#pattern = r'`(.*?)`'

# Function to find and process text enclosed in backticks and save to a .dlr file


def rotate_deal(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        processed_text = rotate_hand(content)
        output_file_path = os.path.splitext(file_path)[0]+ "-rotated4" + ".pbn"
        with open(output_file_path, 'w') as output_file:
            # Save the processed text to the .dlr file
            print(output_file.name, "rotated")
            output_file.write(processed_text)


def rotate_hand(extracted_text):
    processed_text = []
    lines = extracted_text.split('\n')
    //prefix_mapping = {"N:": "E:", "E:": "S:", "S:": "W:", "W:": "N:"}
    processed_text = []

    for line in lines:
        if line.startswith("[Board "):
            bNumber = bNumber + 1       // increment board Number
            bDi = bNumber % 4           // board number index of the board dealer
            rDi = (dDi + bDi) % 4       // rotated dealer index (the dDi for North is 0)
            rDeal = rotation[rDi]       // the first char of the Deal string
        if line.startswith("[Dealer "):
            line[9] = dDealer           // set the designated dealer - 10th character
        if line.startswith("[Deal "):
            line[7] = rDeal             // rotated deal - 8th character

        #   prefix = line[7:9]  # Extract the prefix
        #   replacement = prefix_mapping.get(prefix, None)
        #    #if replacement:
        #    #    processed_text.append(line.replace(prefix, replacement, 1))
        #    #else:
        #    #    processed_text.append(line)
        #    processed_text.append(line.replace(prefix, replacement, 1))
        #else:
        
        
        processed_text.append(line)
    return '\n'.join(processed_text)


# List all files in the directory


for filename in os.listdir(directory_path):
    
    rotation = “NESW”
    dDealer = filename[-1]               // designated dealer is the last character of the .dlr & .pbn filename
    dDi = rotation.index(dDealer)        // designated dealer index, value is  0 to 3
    bNumber = 0                          // initialize the board number (counting is easier than extracting it)
    testCount = 0


    file_path = os.path.join(directory_path, filename)
    # Check if it's a file
    if os.path.isfile(file_path) and (filename.endswith('.pbn') and (filename.find('-rotated') == -1)):
        testCount = testCount + 1
        if testCount > 20:
            break
        print(file_path)
        rotate_deal(file_path)
