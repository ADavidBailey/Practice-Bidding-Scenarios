import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

// Define all artifacts in pipeline order with their dependencies
const ARTIFACTS = [
    {
        name: 'dlr',
        shortName: 'dlr',
        getPath: (s: string, r: string) => path.join(r, 'dlr', `${s}.dlr`),
        getSourcePath: (s: string, r: string) => path.join(r, 'PBS', s),
        command: 'pbs.runDlr'
    },
    {
        name: 'pbn',
        shortName: 'pbn',
        getPath: (s: string, r: string) => path.join(r, 'pbn', `${s}.pbn`),
        getSourcePath: (s: string, r: string) => path.join(r, 'dlr', `${s}.dlr`),
        command: 'pbs.runPbn'
    },
    {
        name: 'rotate',
        shortName: 'rot',
        getPath: (s: string, r: string) => path.join(r, 'pbn-rotated-for-4-players', `${s}.pbn`),
        getSourcePath: (s: string, r: string) => path.join(r, 'pbn', `${s}.pbn`),
        command: 'pbs.runRotate'
    },
    {
        name: 'bba',
        shortName: 'bba',
        getPath: (s: string, r: string) => path.join(r, 'bba', `${s}.pbn`),
        getSourcePath: (s: string, r: string) => path.join(r, 'pbn', `${s}.pbn`),
        command: 'pbs.runBba'
    },
    {
        name: 'filter',
        shortName: 'flt',
        getPath: (s: string, r: string) => path.join(r, 'bba-filtered', `${s}.pbn`),
        getSourcePath: (s: string, r: string) => path.join(r, 'bba', `${s}.pbn`),
        command: 'pbs.runFilter'
    },
    {
        name: 'sheet',
        shortName: 'sheet',
        getPath: (s: string, r: string) => path.join(r, 'bidding-sheets', `${s} Bidding Sheets.pdf`),
        getSourcePath: (s: string, r: string) => path.join(r, 'bba-filtered', `${s}.pbn`),
        command: 'pbs.runBiddingSheet'
    }
];

type ArtifactStatus = 'fresh' | 'stale' | 'missing';

interface ArtifactInfo {
    name: string;
    shortName: string;
    status: ArtifactStatus;
    command: string;
    artifactPath: string;
}

/**
 * Extract scenario name from a file path in any pipeline directory
 */
function getScenarioFromPath(filePath: string): string | undefined {
    const dirName = path.dirname(filePath);
    const baseName = path.basename(filePath);
    const parentDir = path.basename(dirName);

    // Check each known directory type
    if (parentDir === 'PBS') {
        // PBS files have no extension
        return baseName;
    }

    if (parentDir === 'dlr') {
        // dlr/Scenario.dlr
        return baseName.replace(/\.dlr$/, '');
    }

    if (parentDir === 'pbn' || parentDir === 'pbn-rotated-for-4-players' ||
        parentDir === 'bba' || parentDir === 'bba-filtered') {
        // pbn/Scenario.pbn
        return baseName.replace(/\.pbn$/, '');
    }

    if (parentDir === 'bidding-sheets') {
        // bidding-sheets/Scenario Bidding Sheets.pdf or .html
        return baseName
            .replace(/ Bidding Sheets\.(pdf|html)$/, '')
            .replace(/\.pbn$/, '');
    }

    return undefined;
}

/**
 * Tree item for the current scenario view
 */
export class ScenarioTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly isRoot: boolean = false,
        public readonly artifactInfo?: ArtifactInfo
    ) {
        super(label, collapsibleState);

        if (isRoot) {
            this.iconPath = new vscode.ThemeIcon('file-code');
            this.contextValue = 'scenario';
        } else if (artifactInfo) {
            // Set icon based on status
            switch (artifactInfo.status) {
                case 'fresh':
                    this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('testing.iconPassed'));
                    break;
                case 'stale':
                    this.iconPath = new vscode.ThemeIcon('sync', new vscode.ThemeColor('testing.iconQueued'));
                    break;
                case 'missing':
                    this.iconPath = new vscode.ThemeIcon('close', new vscode.ThemeColor('testing.iconFailed'));
                    break;
            }

            // Set command to open the artifact file (if it exists)
            if (artifactInfo.status !== 'missing') {
                this.command = {
                    command: 'pbs.openPbsFile',
                    title: `Open ${artifactInfo.name}`,
                    arguments: [artifactInfo.artifactPath]
                };
            }

            // Tooltip with path and status
            const statusText = artifactInfo.status === 'fresh' ? 'Up to date' :
                artifactInfo.status === 'stale' ? 'Needs rebuild' : 'Not yet built';
            const clickAction = artifactInfo.status === 'missing' ? '' : '\n\n*Click to open*';
            this.tooltip = new vscode.MarkdownString(`**${artifactInfo.name}**\n\n${statusText}\n\n\`${artifactInfo.artifactPath}\`${clickAction}`);
            this.contextValue = 'artifact';
        }
    }
}

/**
 * Provider for the current scenario tree view
 */
export class CurrentScenarioProvider implements vscode.TreeDataProvider<ScenarioTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ScenarioTreeItem | undefined | null | void> = new vscode.EventEmitter<ScenarioTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ScenarioTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private currentScenario: string | undefined;
    private disposables: vscode.Disposable[] = [];

    constructor(private workspaceRoot: string | undefined) {
        // Update when active editor changes
        this.disposables.push(
            vscode.window.onDidChangeActiveTextEditor(editor => {
                this.updateCurrentScenario(editor);
            })
        );

        // Initial update
        this.updateCurrentScenario(vscode.window.activeTextEditor);
    }

    private updateCurrentScenario(editor: vscode.TextEditor | undefined): void {
        const oldScenario = this.currentScenario;

        if (editor) {
            const newScenario = getScenarioFromPath(editor.document.uri.fsPath);
            // Only update if we found a valid scenario (keep previous when switching to non-scenario files)
            if (newScenario) {
                this.currentScenario = newScenario;
            }
        }

        // Only refresh if scenario changed
        if (oldScenario !== this.currentScenario) {
            this._onDidChangeTreeData.fire();
        }
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    dispose(): void {
        this.disposables.forEach(d => d.dispose());
    }

    getTreeItem(element: ScenarioTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ScenarioTreeItem): Thenable<ScenarioTreeItem[]> {
        if (!this.workspaceRoot || !this.currentScenario) {
            return Promise.resolve([]);
        }

        if (!element) {
            // Root level - return the scenario header
            return Promise.resolve([
                new ScenarioTreeItem(
                    `Scenario: ${this.currentScenario}`,
                    vscode.TreeItemCollapsibleState.Expanded,
                    true
                )
            ]);
        }

        if (element.isRoot) {
            // First add the PBS source file
            const pbsPath = path.join(this.workspaceRoot!, 'PBS', this.currentScenario!);
            const pbsExists = fs.existsSync(pbsPath);
            const pbsItem = new ScenarioTreeItem(
                'PBS',
                vscode.TreeItemCollapsibleState.None,
                false,
                undefined  // No artifactInfo - this is the source
            );
            pbsItem.iconPath = new vscode.ThemeIcon('file-code');
            pbsItem.contextValue = 'source';
            if (pbsExists) {
                pbsItem.command = {
                    command: 'pbs.openPbsFile',
                    title: 'Open PBS source',
                    arguments: [pbsPath]
                };
                pbsItem.tooltip = new vscode.MarkdownString(`**PBS Source**\n\n\`${pbsPath}\`\n\n*Click to open*`);
            } else {
                pbsItem.tooltip = new vscode.MarkdownString(`**PBS Source**\n\nNot found: \`${pbsPath}\``);
            }

            // Then add artifact children
            const artifacts = ARTIFACTS.map(artifact => {
                const info = this.getArtifactInfo(artifact, this.currentScenario!, this.workspaceRoot!);
                return new ScenarioTreeItem(
                    info.shortName,
                    vscode.TreeItemCollapsibleState.None,
                    false,
                    info
                );
            });
            return Promise.resolve([pbsItem, ...artifacts]);
        }

        return Promise.resolve([]);
    }

    private getArtifactInfo(artifact: typeof ARTIFACTS[0], scenario: string, root: string): ArtifactInfo {
        const artifactPath = artifact.getPath(scenario, root);
        const sourcePath = artifact.getSourcePath(scenario, root);

        let status: ArtifactStatus = 'missing';

        if (fs.existsSync(artifactPath)) {
            // Artifact exists - check if fresh or stale
            if (fs.existsSync(sourcePath)) {
                const artifactMtime = fs.statSync(artifactPath).mtimeMs;
                const sourceMtime = fs.statSync(sourcePath).mtimeMs;
                status = artifactMtime >= sourceMtime ? 'fresh' : 'stale';
            } else {
                // No source to compare against - consider fresh
                status = 'fresh';
            }
        }

        return {
            name: artifact.name,
            shortName: artifact.shortName,
            status,
            command: artifact.command,
            artifactPath
        };
    }
}
