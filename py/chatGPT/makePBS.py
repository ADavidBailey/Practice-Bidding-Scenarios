import os
import json
import argparse

description = "Create a /pbs from BBO dealerCode & BBOalert wrapper)"
parser = argparse.ArgumentParser(description=description)
parser.add_argument("--scenario", type=str, help="Name of scenario is required")
args = parser.parse_args()
scenario = str(args.scenario)
print("scenario " + scenario)

def getFilePath(pathName)
    filePath = os.path.join('..', pathName, scenario)

    if os.path.isfile(filePath):
        return(filePath)
    else:
        print(f"Scenario does not exist: {scenario}")
        break

# filepaths
bboFile = getFilePath('bbo')
print('bboFile: ' + bboFile)
dlrFile = getFilePath('dlr')
print('dlrFile: ' + dlrFile)
pbsFile = getFilePath('pbsTEST')
print('pbsFile: ' + pbsFile)

# Read data from buttonContent
with open(bboFile, 'r') as jf:
    data = json.load(jf)
    jsName = data.get("jsName")
    dealer = data.get("dealer","S")
    rotate = data.get("rotate","Y")
    buttonText = data.get("ButtonText", scenario)
    buttonTitle = data.get("ButtonTitle", "--- " + buttonText)
    buttonChat = data.get("ButtonChat", "")

# Construct pbs file for scenario
pbsContent = (
    f'Script,{jsName} setDealerCode(`'
    f'{dealerCode}'
    f'`,"{dealer}","{rotate}") Script Button,{buttonText},\n\'
    f'--- {buttonTitle}\n\'
    f"\n{buttonChat}"
    f"%"{jsName}"%"
)

# Write to pbs\scenario
with open(pbsFile, 'w') as pbs:
    pbs.write(pbsContent)

print(f"{pbsFile} created successfully.")
