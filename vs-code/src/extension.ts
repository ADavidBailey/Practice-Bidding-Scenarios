import * as vscode from 'vscode';
import { ButtonPanelProvider } from './buttonPanelProvider';
import { ButtonGridProvider } from './buttonGridProvider';
import { registerPipelineCommands, createStatusBar } from './pipelineRunner';

export function activate(context: vscode.ExtensionContext) {
    console.log('Practice Bidding Scenarios extension is now active');

    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

    // Create the button panel provider (tree view)
    const buttonPanelProvider = new ButtonPanelProvider(workspaceRoot);

    // Register the tree view
    const treeView = vscode.window.createTreeView('pbsButtonPanel', {
        treeDataProvider: buttonPanelProvider,
        showCollapseAll: true
    });

    // Create the button grid provider (webview)
    const buttonGridProvider = new ButtonGridProvider(context.extensionUri, workspaceRoot);

    // Register the webview view provider
    const webviewProvider = vscode.window.registerWebviewViewProvider(
        ButtonGridProvider.viewType,
        buttonGridProvider
    );

    // Register refresh command for tree view
    const refreshCommand = vscode.commands.registerCommand('pbs.refreshButtonPanel', () => {
        buttonPanelProvider.refresh();
        vscode.window.showInformationMessage('PBS Tree View refreshed');
    });

    // Register refresh command for button grid
    const refreshGridCommand = vscode.commands.registerCommand('pbs.refreshButtonGrid', () => {
        buttonGridProvider.refresh();
        vscode.window.showInformationMessage('PBS Button Grid refreshed');
    });

    // Register open file command
    const openFileCommand = vscode.commands.registerCommand('pbs.openPbsFile', async (filePath: string, lineNumber?: number) => {
        if (!filePath) {
            return;
        }

        try {
            const document = await vscode.workspace.openTextDocument(filePath);
            const editor = await vscode.window.showTextDocument(document);

            // Set language mode to 'pbs' for files in the PBS directory
            if (filePath.includes('/PBS/')) {
                await vscode.languages.setTextDocumentLanguage(document, 'pbs');
            }

            if (lineNumber && lineNumber > 0) {
                const position = new vscode.Position(lineNumber - 1, 0);
                editor.selection = new vscode.Selection(position, position);
                editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to open file: ${filePath}`);
        }
    });

    // Watch for PBS file changes
    const pbsWatcher = vscode.workspace.createFileSystemWatcher('**/PBS/*');
    pbsWatcher.onDidChange(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
    });
    pbsWatcher.onDidCreate(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
    });
    pbsWatcher.onDidDelete(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
    });

    // Also watch the main config file
    const configWatcher = vscode.workspace.createFileSystemWatcher('**/-PBS.txt');
    configWatcher.onDidChange(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
    });

    context.subscriptions.push(
        treeView,
        webviewProvider,
        refreshCommand,
        refreshGridCommand,
        openFileCommand,
        pbsWatcher,
        configWatcher
    );

    // Register pipeline commands and status bar
    registerPipelineCommands(context);
    createStatusBar(context);
}

export function deactivate() {}
