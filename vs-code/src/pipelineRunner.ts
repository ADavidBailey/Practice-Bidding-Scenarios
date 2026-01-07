import * as vscode from 'vscode';
import * as path from 'path';

/**
 * Get the scenario name from a file path.
 * The scenario name is the filename without extension.
 */
function getScenarioFromPath(filePath: string | undefined): string | undefined {
    if (!filePath) {
        return undefined;
    }

    // Check if file is in PBS directory
    const dir = path.dirname(filePath);
    if (!dir.endsWith('PBS')) {
        return undefined;
    }

    // Return filename (PBS files don't have extensions)
    return path.basename(filePath);
}

/**
 * Get the current scenario from the active editor
 */
function getCurrentScenario(): string | undefined {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return undefined;
    }

    const scenario = getScenarioFromPath(editor.document.uri.fsPath);
    if (!scenario) {
        vscode.window.showWarningMessage('Current file is not a PBS scenario');
        return undefined;
    }

    return scenario;
}

/**
 * Run the pipeline with specified operations
 */
async function runPipeline(scenario: string, operations: string): Promise<void> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    const scriptPath = path.join(workspaceFolder.uri.fsPath, 'build-scripts-mac', 'pbs-pipeline-mac.py');

    // Create or reuse terminal
    let terminal = vscode.window.terminals.find(t => t.name === 'PBS Pipeline');
    if (!terminal) {
        terminal = vscode.window.createTerminal('PBS Pipeline');
    }

    terminal.show();
    terminal.sendText(`cd "${workspaceFolder.uri.fsPath}" && python3 "${scriptPath}" "${scenario}" "${operations}"`);
}

/**
 * Register a pipeline command
 */
function registerCommand(context: vscode.ExtensionContext, commandId: string, operations: string): void {
    context.subscriptions.push(
        vscode.commands.registerCommand(commandId, async () => {
            const scenario = getCurrentScenario();
            if (scenario) {
                await runPipeline(scenario, operations);
            }
        })
    );
}

/**
 * Register all pipeline commands
 */
export function registerPipelineCommands(context: vscode.ExtensionContext): void {
    // All operations
    registerCommand(context, 'pbs.runAll', '*');

    // Individual operations
    registerCommand(context, 'pbs.runDlr', 'dlr');
    registerCommand(context, 'pbs.runPbn', 'pbn');
    registerCommand(context, 'pbs.runRotate', 'rotate');
    registerCommand(context, 'pbs.runBba', 'bba');
    registerCommand(context, 'pbs.runFilter', 'filter');
    registerCommand(context, 'pbs.runFilterStats', 'filterStats');
    registerCommand(context, 'pbs.runBiddingSheet', 'biddingSheet');

    // Plus operations (from X through end)
    registerCommand(context, 'pbs.runDlrPlus', 'dlr+');
    registerCommand(context, 'pbs.runPbnPlus', 'pbn+');
    registerCommand(context, 'pbs.runRotatePlus', 'rotate+');
    registerCommand(context, 'pbs.runBbaPlus', 'bba+');
    registerCommand(context, 'pbs.runFilterPlus', 'filter+');
    registerCommand(context, 'pbs.runFilterStatsPlus', 'filterStats+');
}

/**
 * Status bar item showing current scenario
 */
let statusBarItem: vscode.StatusBarItem;

export function createStatusBar(context: vscode.ExtensionContext): void {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.command = 'pbs.runAll';
    context.subscriptions.push(statusBarItem);

    // Update status bar when active editor changes
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(updateStatusBar)
    );

    // Initial update
    updateStatusBar(vscode.window.activeTextEditor);
}

function updateStatusBar(editor: vscode.TextEditor | undefined): void {
    if (!statusBarItem) {
        return;
    }

    if (!editor) {
        statusBarItem.hide();
        return;
    }

    const scenario = getScenarioFromPath(editor.document.uri.fsPath);
    if (scenario) {
        statusBarItem.text = `$(play) PBS: ${scenario}`;
        statusBarItem.tooltip = `Click to run all operations on ${scenario}`;
        statusBarItem.show();
    } else {
        statusBarItem.hide();
    }
}
