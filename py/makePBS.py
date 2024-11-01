import os
import json
import argparse

description = "Create a /pbs from BBO dealerCode & BBOalert wrapper"
parser = argparse.ArgumentParser(description=description)
parser.add_argument("--scenario", type=str, required=True, help="Name of scenario is required")
args = parser.parse_args()
scenario = args.scenario

def getFilePath(folder, filename):
    filePath = os.path.join('..', folder, filename)
    if os.path.isfile(filePath):
        return filePath
    else:
        raise FileNotFoundError(f"Required file does not exist: {filePath}")

# filepaths
try:
    bboFile = getFilePath('bbo', scenario + '.json')
    dlrFile = getFilePath('dlr', scenario + '.dlr')
    pbsFile = os.path.join('..', 'pbs-test', scenario)

    # Read data from buttonContent
    with open(bboFile, 'r') as jf:
        data = json.load(jf)
        jsName = data.get("jsName", "")
        dealer = data.get("dealer", "S")
        rotate = data.get("rotate", "true")
        buttonText = data.get("ButtonText", scenario)
        scenarioTitle = data.get("scenarioTitle", scenario)
        
        chats = [data.get(f"chat{i}", "") for i in range(1, 11)]
        buttonChat = '\n'.join(filter(None, chats))  # Filters out empty chat lines

    # Read data from dlrFile
    with open(dlrFile, 'r') as f:
        dealerCode = f.read().strip()
        dealerCode = dealerCode.split('printpbn')[0]

    # Construct pbs file content for the scenario
    pbsContent = (
        f"Script,{jsName}\n"
        f"setDealerCode(`\n"
        f"{dealerCode}\n"
        f"`, \"{dealer}\", {rotate})\n"
        f"Script\n"
        f"Button,{buttonText}\n"
        f"{scenarioTitle}\n"
        f"{buttonChat}\n"
        f"%{jsName}%"
    )

    # Write to pbs file
    os.makedirs(os.path.dirname(pbsFile), exist_ok=True)  # Ensure the directory exists
    with open(pbsFile, 'w') as pbs:
        pbs.write(pbsContent)

    print(f"{pbsFile} created successfully.")

except FileNotFoundError as e:
    print(e)
