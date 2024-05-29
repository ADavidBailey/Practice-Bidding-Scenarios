import os
    
# Directory containing the input files

# Regular expression pattern to match text enclosed in backticks spanning multiple lines
#pattern = r'`(.*?)`'

# Function to find and process text enclosed in backticks and save to a .dlr file


def rotate_deal(file_path):
     with open(file_path, 'r') as file:
        content = file.read()
        processed_text = rotate_hand(content)
        output_file_path = os.path.splitext(file_path)[0] + ".pbn"
        output_file_path = os.path.join("./pbnr4", output_file_path).replace('\\', '/')
        print(output_file_path)

        with open(output_file_path, 'w') as output_file:
            # Save the processed text to the ./pbnr4/ ... .pbn file
            print(output_file.name, " rotated")
            output_file.write(processed_text)


def rotate_hand(extracted_text):
    processed_text = []
    lines = extracted_text.split('\n')
    processed_text = []
    bN = 0

    for line in lines:
        if line.startswith("[Dealer "):
            line = line[:9] + dDealer + '"]'
            print(line)
        if line.startswith("[Deal "):
            bN = bN + 1                 # increment board Number
            bDi = (bN % 4) - 1          # rotated dealer index (the dDi for North is 0)
            rDeal = rotation[bDi]       # the first char of the Deal string
            line = line[:6] + rDeal + line[7:]              # rotated deal - 8th character
            print(line)
        processed_text.append(line)
    return '\n'.join(processed_text)


# List all files in the directory
in_directory_path = './pbnTest'     # Read pbn files
out_directory_path = './pbnr4'      # Write r4pbn files
testCount = 0
rotation = "NESW"
for filename in os.listdir(in_directory_path):
    

    file_path = os.path.join(in_directory_path, filename)
    # Check if it's a file
    if os.path.isfile(file_path) and (filename.endswith('.pbn')):
        testCount = testCount + 1
        if testCount > 5:
            break
        dDealer = filename[-5]               # designated dealer is the last character of the .dlr & .pbn filename
        dDi = rotation.index(dDealer)        # designated dealer index, value is  0 to 3
        print(file_path)
        print(filename," Dealer=",dDealer," Dealer Index=",str(dDi))
        rotate_deal(file_path)
