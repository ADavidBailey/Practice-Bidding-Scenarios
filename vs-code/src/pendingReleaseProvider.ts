import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { PbsButton, parsePbsDirectory } from './pbsParser';

/**
 * Tree item for pending release scenarios
 */
export class PendingReleaseItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly button: PbsButton
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);

        this.contextValue = 'pendingRelease';
        this.iconPath = new vscode.ThemeIcon('file-code');

        if (button.filePath) {
            this.tooltip = new vscode.MarkdownString(`**${button.label}**\n\n\`${button.filePath}\`\n\n*Click to open*`);
            this.command = {
                command: 'pbs.openPbsFile',
                title: 'Open PBS File',
                arguments: [button.filePath, button.lineNumber]
            };
        }
    }
}

/**
 * Provider for the Pending Release top-level view
 * Shows scenarios in pbs-test that are awaiting release to pbs-release
 */
export class PendingReleaseProvider implements vscode.TreeDataProvider<PendingReleaseItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<PendingReleaseItem | undefined | null | void> = new vscode.EventEmitter<PendingReleaseItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<PendingReleaseItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private pendingButtons: PbsButton[] = [];
    private disposables: vscode.Disposable[] = [];

    constructor(private workspaceRoot: string | undefined) {
        // Watch for changes in pbs-test directory
        if (workspaceRoot) {
            const pbsTestWatcher = vscode.workspace.createFileSystemWatcher(
                new vscode.RelativePattern(workspaceRoot, 'pbs-test/*.pbs')
            );
            pbsTestWatcher.onDidChange(() => this.refresh());
            pbsTestWatcher.onDidCreate(() => this.refresh());
            pbsTestWatcher.onDidDelete(() => this.refresh());
            this.disposables.push(pbsTestWatcher);
        }

        this.loadData();
    }

    refresh(): void {
        this.loadData();
        this._onDidChangeTreeData.fire();
    }

    private async loadData(): Promise<void> {
        if (!this.workspaceRoot) {
            this.pendingButtons = [];
            return;
        }

        const pbsTestDir = path.join(this.workspaceRoot, 'pbs-test');
        this.pendingButtons = await parsePbsDirectory(pbsTestDir);
    }

    dispose(): void {
        this.disposables.forEach(d => d.dispose());
    }

    getTreeItem(element: PendingReleaseItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: PendingReleaseItem): Promise<PendingReleaseItem[]> {
        if (element) {
            // No children for items
            return [];
        }

        // Root level - return all pending release items
        await this.loadData();

        return this.pendingButtons
            .filter(button => button.label && button.label.trim() !== '' && button.label !== '---')
            .sort((a, b) => a.label.localeCompare(b.label))
            .map(button => new PendingReleaseItem(button.label, button));
    }
}
