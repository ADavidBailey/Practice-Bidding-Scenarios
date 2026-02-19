import * as vscode from 'vscode';
import * as path from 'path';
import { ButtonPanelProvider } from './buttonPanelProvider';
import { ButtonGridProvider } from './buttonGridProvider';
import { CurrentScenarioProvider, ScenarioTreeItem } from './currentScenarioProvider';
import { PendingReleaseProvider } from './pendingReleaseProvider';
import { registerPipelineCommands, createStatusBar } from './pipelineRunner';
import { ActivityLogger } from './activityLogger';
import { getBtnMetadata, clearMetadataCache } from './btnParser';

// Export logger instance for use by other modules (e.g., pipelineRunner)
export let activityLogger: ActivityLogger | undefined;

/**
 * Check if a path contains a PBS directory (case-insensitive)
 */
function containsPbsDir(filePath: string): boolean {
    return filePath.includes('/PBS/') || filePath.includes('/pbs/');
}

/**
 * Artifact directories that contain scenario outputs
 */
const ARTIFACT_DIRS = [
    'btn', 'pbs-test', 'PBS', 'pbs', 'dlr', 'pbn', 'pbn-rotated-for-4-players',
    'bba', 'bba-filtered', 'bba-filtered-out', 'bba-summary', 'bidding-sheets',
    'lin', 'lin-rotated-for-4-players', 'quiz'
];

/**
 * Get scenario name from a file path
 */
function getScenarioFromPath(filePath: string | undefined): string | undefined {
    if (!filePath) {
        return undefined;
    }

    const dir = path.dirname(filePath);
    const dirName = path.basename(dir);

    if (!ARTIFACT_DIRS.includes(dirName)) {
        return undefined;
    }

    const fileName = path.basename(filePath);

    // For PBS files (legacy), there's no extension
    if (dirName.toLowerCase() === 'pbs') {
        return fileName;
    }

    // Remove extension
    const baseName = fileName.replace(/\.(btn|pbs|pbn|dlr|pdf|html|txt|lin)$/i, '');

    // Handle bidding sheet names
    const biddingSheetMatch = baseName.match(/^(.+?)\s+Bidding Sheets?$/i);
    if (biddingSheetMatch) {
        return biddingSheetMatch[1];
    }

    return baseName;
}

/**
 * Update the pbs.bbaWorks context variable based on current editor
 */
function updateBbaWorksContext(editor: vscode.TextEditor | undefined, workspaceRoot: string | undefined): void {
    if (!workspaceRoot || !editor) {
        vscode.commands.executeCommand('setContext', 'pbs.bbaWorks', false);
        return;
    }

    const scenario = getScenarioFromPath(editor.document.uri.fsPath);
    if (!scenario) {
        // Not a scenario file - default to false (hide BBA options)
        vscode.commands.executeCommand('setContext', 'pbs.bbaWorks', false);
        return;
    }

    const metadata = getBtnMetadata(scenario, workspaceRoot);
    vscode.commands.executeCommand('setContext', 'pbs.bbaWorks', metadata.bbaWorks);
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Practice Bidding Scenarios extension is now active');

    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

    // Initialize activity logger and start session
    activityLogger = new ActivityLogger(workspaceRoot);
    activityLogger.startSession();

    // Register dispose callback to end session when extension deactivates
    context.subscriptions.push({
        dispose: () => {
            if (activityLogger) {
                activityLogger.endSession();
            }
        }
    });

    // Log file saves for activity tracking
    const saveWatcher = vscode.workspace.onDidSaveTextDocument(document => {
        if (activityLogger) {
            activityLogger.logFileSave(document);
        }
    });
    context.subscriptions.push(saveWatcher);

    // Create the current scenario provider (shows focused scenario with artifact status)
    const currentScenarioProvider = new CurrentScenarioProvider(workspaceRoot);

    // Register the current scenario tree view
    const currentScenarioView = vscode.window.createTreeView('pbsCurrentScenario', {
        treeDataProvider: currentScenarioProvider,
        showCollapseAll: false
    });

    // Create the pending release provider (shows scenarios awaiting release)
    const pendingReleaseProvider = new PendingReleaseProvider(workspaceRoot);

    // Register the pending release tree view
    const pendingReleaseView = vscode.window.createTreeView('pbsPendingRelease', {
        treeDataProvider: pendingReleaseProvider,
        showCollapseAll: false,
        canSelectMany: true
    });

    // Update bbaWorks context when active editor changes
    const editorChangeListener = vscode.window.onDidChangeActiveTextEditor(editor => {
        updateBbaWorksContext(editor, workspaceRoot);
    });
    context.subscriptions.push(editorChangeListener);

    // Initial context update
    updateBbaWorksContext(vscode.window.activeTextEditor, workspaceRoot);

    // Watch for BTN file changes to clear metadata cache and update context
    const btnWatcher = vscode.workspace.createFileSystemWatcher('**/btn/*.btn');
    btnWatcher.onDidChange(() => {
        clearMetadataCache();
        updateBbaWorksContext(vscode.window.activeTextEditor, workspaceRoot);
    });
    btnWatcher.onDidCreate(() => {
        clearMetadataCache();
        updateBbaWorksContext(vscode.window.activeTextEditor, workspaceRoot);
    });
    btnWatcher.onDidDelete(() => {
        clearMetadataCache();
        updateBbaWorksContext(vscode.window.activeTextEditor, workspaceRoot);
    });
    context.subscriptions.push(btnWatcher);

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

    // Register refresh command for pending release view
    const refreshPendingReleaseCommand = vscode.commands.registerCommand('pbs.refreshPendingRelease', () => {
        pendingReleaseProvider.refresh();
        vscode.window.showInformationMessage('Pending Release refreshed');
    });

    // Register rebuild artifact command (for right-click context menu)
    const rebuildArtifactCommand = vscode.commands.registerCommand('pbs.rebuildArtifact', async (item: ScenarioTreeItem) => {
        if (item?.artifactInfo?.command) {
            await vscode.commands.executeCommand(item.artifactInfo.command);
        }
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
            if (containsPbsDir(filePath)) {
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

    // Watch for PBS file changes (both cases)
    const pbsWatcher = vscode.workspace.createFileSystemWatcher('**/{PBS,pbs}/*');
    pbsWatcher.onDidChange(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
        currentScenarioProvider.refresh();
    });
    pbsWatcher.onDidCreate(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
        currentScenarioProvider.refresh();
    });
    pbsWatcher.onDidDelete(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
        currentScenarioProvider.refresh();
    });

    // Also watch the main config file
    const configWatcher = vscode.workspace.createFileSystemWatcher('**/-PBS.txt');
    configWatcher.onDidChange(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
    });

    // Watch artifact directories for current scenario status updates
    const artifactWatcher = vscode.workspace.createFileSystemWatcher('**/{dlr,pbn,pbn-rotated-for-4-players,bba,bba-filtered,bidding-sheets,quiz}/*');
    artifactWatcher.onDidChange(() => currentScenarioProvider.refresh());
    artifactWatcher.onDidCreate(() => currentScenarioProvider.refresh());
    artifactWatcher.onDidDelete(() => currentScenarioProvider.refresh());

    // Watch Bidding Scenarios folder for package artifact status updates
    const packageWatcher = vscode.workspace.createFileSystemWatcher('**/Bidding Scenarios/**/*');
    packageWatcher.onDidChange(() => currentScenarioProvider.refresh());
    packageWatcher.onDidCreate(() => currentScenarioProvider.refresh());
    packageWatcher.onDidDelete(() => currentScenarioProvider.refresh());

    // Watch pbs-test directory for pending release updates
    const pbsTestWatcher = vscode.workspace.createFileSystemWatcher('**/pbs-test/*.pbs');
    pbsTestWatcher.onDidChange(() => {
        pendingReleaseProvider.refresh();
        buttonPanelProvider.refresh();
        currentScenarioProvider.refresh();
    });
    pbsTestWatcher.onDidCreate(() => {
        pendingReleaseProvider.refresh();
        buttonPanelProvider.refresh();
        currentScenarioProvider.refresh();
    });
    pbsTestWatcher.onDidDelete(() => {
        pendingReleaseProvider.refresh();
        buttonPanelProvider.refresh();
        currentScenarioProvider.refresh();
    });

    context.subscriptions.push(
        currentScenarioView,
        pendingReleaseView,
        treeView,
        webviewProvider,
        refreshCommand,
        refreshGridCommand,
        refreshPendingReleaseCommand,
        rebuildArtifactCommand,
        openFileCommand,
        pbsWatcher,
        configWatcher,
        artifactWatcher,
        packageWatcher,
        pbsTestWatcher
    );

    // Register pipeline commands and status bar
    registerPipelineCommands(context);
    createStatusBar(context);

    // Explicit startup refresh to catch changes made while VS Code was closed
    // Small delay ensures views are fully registered before refreshing
    setTimeout(() => {
        buttonPanelProvider.refresh();
        buttonGridProvider.refresh();
        currentScenarioProvider.refresh();
        pendingReleaseProvider.refresh();
        console.log('PBS Dashboard refreshed on startup');
    }, 500);
}

export function deactivate() {}
