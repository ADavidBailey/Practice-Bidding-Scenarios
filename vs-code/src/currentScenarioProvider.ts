import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { getBtnMetadata, clearMetadataCache } from './btnParser';

/**
 * Find the PBS directory (handles both 'PBS' and 'pbs' case)
 */
function findPbsDir(workspaceRoot: string): string {
    const upperPath = path.join(workspaceRoot, 'PBS');
    const lowerPath = path.join(workspaceRoot, 'pbs');
    if (fs.existsSync(upperPath)) {
        return upperPath;
    }
    if (fs.existsSync(lowerPath)) {
        return lowerPath;
    }
    return upperPath; // default to uppercase if neither exists
}

/**
 * Check if a directory name is a PBS directory (case-insensitive)
 */
function isPbsDir(dirName: string): boolean {
    return dirName.toLowerCase() === 'pbs';
}

/**
 * Check if a directory name is a btn directory
 */
function isBtnDir(dirName: string): boolean {
    return dirName.toLowerCase() === 'btn';
}

/**
 * Find the first packaged PBN file for a scenario in the Bidding Scenarios hierarchy.
 * Scans Bidding Scenarios/{section}/{scenario}/ for {scenario}.pbn.
 * Returns the path (which may not exist yet if package hasn't been run).
 */
function findPackagePath(scenario: string, root: string): string {
    const bsDir = path.join(root, 'Bidding Scenarios');
    if (fs.existsSync(bsDir)) {
        try {
            const sections = fs.readdirSync(bsDir).sort();
            for (const section of sections) {
                const scenarioDir = path.join(bsDir, section, scenario);
                if (fs.existsSync(scenarioDir)) {
                    return path.join(scenarioDir, `${scenario}.pbn`);
                }
            }
        } catch { /* ignore read errors */ }
    }
    // Not yet packaged — return a path in a placeholder location
    return path.join(bsDir, '_', scenario, `${scenario}.pbn`);
}

// Define all artifacts in pipeline order with their dependencies
// requiresBba indicates artifacts that need bba-works=true to be shown
const ARTIFACTS = [
    {
        name: 'dlr',
        shortName: 'dlr',
        requiresBba: false,
        getPath: (s: string, r: string) => path.join(r, 'dlr', `${s}.dlr`),
        getSourcePath: (s: string, r: string) => path.join(r, 'btn', `${s}.btn`),
        command: 'pbs.runDlr'
    },
    // PBS is handled specially in getChildren() to show pbs-test and pbs-release separately
    {
        name: 'pbn',
        shortName: 'pbn',
        requiresBba: false,
        getPath: (s: string, r: string) => path.join(r, 'pbn', `${s}.pbn`),
        getSourcePath: (s: string, r: string) => path.join(r, 'dlr', `${s}.dlr`),
        command: 'pbs.runPbn'
    },
    {
        name: 'rotate',
        shortName: 'rot',
        requiresBba: false,
        getPath: (s: string, r: string) => path.join(r, 'pbn-rotated-for-4-players', `${s}.pbn`),
        getSourcePath: (s: string, r: string) => path.join(r, 'pbn', `${s}.pbn`),
        command: 'pbs.runRotate'
    },
    {
        name: 'bba',
        shortName: 'bba',
        requiresBba: true,
        getPath: (s: string, r: string) => path.join(r, 'bba', `${s}.pbn`),
        getSourcePath: (s: string, r: string) => path.join(r, 'pbn', `${s}.pbn`),
        command: 'pbs.runBba'
    },
    {
        name: 'filter',
        shortName: 'flt',
        requiresBba: true,
        getPath: (s: string, r: string) => path.join(r, 'bba-filtered', `${s}.pbn`),
        getSourcePath: (s: string, r: string) => path.join(r, 'bba', `${s}.pbn`),
        command: 'pbs.runFilter'
    },
    {
        name: 'sheet',
        shortName: 'sheet',
        requiresBba: true,
        getPath: (s: string, r: string) => path.join(r, 'bidding-sheets', `${s} Bidding Sheets.pdf`),
        getSourcePath: (s: string, r: string) => path.join(r, 'bba-filtered', `${s}.pbn`),
        command: 'pbs.runBiddingSheet'
    },
    {
        name: 'quiz',
        shortName: 'quiz',
        requiresBba: true,
        getPath: (s: string, r: string) => path.join(r, 'quiz', `${s}.pdf`),
        getSourcePath: (s: string, r: string) => path.join(r, 'bba-filtered', `${s}.pbn`),
        command: 'pbs.runQuiz'
    },
    {
        name: 'package',
        shortName: 'pkg',
        requiresBba: false,
        getPath: (s: string, r: string) => findPackagePath(s, r),
        getSourcePath: (s: string, r: string) => {
            // Package copies from bba-filtered (with pbn fallback), so compare against actual source
            const filtered = path.join(r, 'bba-filtered', `${s}.pbn`);
            if (fs.existsSync(filtered)) { return filtered; }
            return path.join(r, 'pbn', `${s}.pbn`);
        },
        command: 'pbs.runPackage'
    }
];

type ArtifactStatus = 'fresh' | 'stale' | 'missing';

// Tolerance for timestamp comparison (ms). Git checkout/commit resets file
// timestamps to the same second with random sub-second ordering, which can
// make a downstream artifact appear older than its source even though both
// were written in the same pipeline run.
const FRESHNESS_TOLERANCE_MS = 1000;

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
    if (isPbsDir(parentDir)) {
        // PBS files have no extension
        return baseName;
    }

    if (isBtnDir(parentDir)) {
        // btn/Scenario.btn
        return baseName.replace(/\.btn$/, '');
    }

    if (parentDir === 'pbs-test') {
        // pbs-test/Scenario.pbs
        return baseName.replace(/\.pbs$/, '');
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

    if (parentDir === 'quiz') {
        // quiz/Scenario.pbn or quiz/Scenario.pdf
        return baseName.replace(/\.(pbn|pdf)$/, '');
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
            this.resourceUri = vscode.Uri.file(artifactInfo.artifactPath);
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

        // Watch for BTN file changes to clear metadata cache
        if (workspaceRoot) {
            const btnWatcher = vscode.workspace.createFileSystemWatcher(
                new vscode.RelativePattern(workspaceRoot, 'btn/*.btn')
            );
            btnWatcher.onDidChange(() => {
                clearMetadataCache();
                this.refresh();
            });
            btnWatcher.onDidCreate(() => {
                clearMetadataCache();
                this.refresh();
            });
            btnWatcher.onDidDelete(() => {
                clearMetadataCache();
                this.refresh();
            });
            this.disposables.push(btnWatcher);
        }

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
            // First add the BTN source file
            const btnPath = path.join(this.workspaceRoot!, 'btn', `${this.currentScenario!}.btn`);
            const btnExists = fs.existsSync(btnPath);
            const btnItem = new ScenarioTreeItem(
                'BTN',
                vscode.TreeItemCollapsibleState.None,
                false,
                undefined  // No artifactInfo - this is the source
            );
            btnItem.iconPath = new vscode.ThemeIcon('file-code');
            btnItem.contextValue = 'source';
            btnItem.resourceUri = vscode.Uri.file(btnPath);
            if (btnExists) {
                btnItem.command = {
                    command: 'pbs.openPbsFile',
                    title: 'Open BTN source',
                    arguments: [btnPath]
                };
                btnItem.tooltip = new vscode.MarkdownString(`**BTN Source**\n\n\`${btnPath}\`\n\n*Click to open*`);
            } else {
                btnItem.tooltip = new vscode.MarkdownString(`**BTN Source**\n\nNot found: \`${btnPath}\``);
            }

            // Get scenario metadata to filter artifacts
            const metadata = getBtnMetadata(this.currentScenario!, this.workspaceRoot!);

            // Filter artifacts based on bbaWorks
            const visibleArtifacts = ARTIFACTS.filter(artifact =>
                !artifact.requiresBba || metadata.bbaWorks
            );

            // Build artifact children
            const items: ScenarioTreeItem[] = [];

            for (const artifact of visibleArtifacts) {
                const info = this.getArtifactInfo(artifact, this.currentScenario!, this.workspaceRoot!);
                items.push(new ScenarioTreeItem(
                    info.shortName,
                    vscode.TreeItemCollapsibleState.None,
                    false,
                    info
                ));

                // After DLR, insert PBS test/release entries
                if (artifact.name === 'dlr') {
                    const pbsItems = this.getPbsArtifactItems(this.currentScenario!, this.workspaceRoot!);
                    items.push(...pbsItems);
                }
            }

            return Promise.resolve([btnItem, ...items]);
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
                status = artifactMtime >= sourceMtime - FRESHNESS_TOLERANCE_MS ? 'fresh' : 'stale';
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

    /**
     * Build tree items for PBS artifacts (pbs-test and/or pbs-release).
     * Shows each that exists, with labels to distinguish them.
     * If neither exists, shows a single "pbs" as missing.
     */
    private getPbsArtifactItems(scenario: string, root: string): ScenarioTreeItem[] {
        const dlrPath = path.join(root, 'dlr', `${scenario}.dlr`);
        const testPath = path.join(root, 'pbs-test', `${scenario}.pbs`);
        const releasePath = path.join(root, 'pbs-release', `${scenario}.pbs`);
        const testExists = fs.existsSync(testPath);
        const releaseExists = fs.existsSync(releasePath);

        if (!testExists && !releaseExists) {
            // Neither exists - show single missing entry
            return [new ScenarioTreeItem(
                'pbs',
                vscode.TreeItemCollapsibleState.None,
                false,
                {
                    name: 'pbs',
                    shortName: 'pbs',
                    status: 'missing',
                    command: 'pbs.runPbsOp',
                    artifactPath: testPath
                }
            )];
        }

        const items: ScenarioTreeItem[] = [];

        if (testExists) {
            const status = this.getFileStatus(testPath, dlrPath);
            items.push(new ScenarioTreeItem(
                'pbs-test',
                vscode.TreeItemCollapsibleState.None,
                false,
                {
                    name: 'pbs-test',
                    shortName: 'pbs-test',
                    status,
                    command: 'pbs.runPbsOp',
                    artifactPath: testPath
                }
            ));
        }

        if (releaseExists) {
            const status = this.getFileStatus(releasePath, dlrPath);
            items.push(new ScenarioTreeItem(
                'pbs-release',
                vscode.TreeItemCollapsibleState.None,
                false,
                {
                    name: 'pbs-release',
                    shortName: 'pbs-release',
                    status,
                    command: 'pbs.runRelease',
                    artifactPath: releasePath
                }
            ));
        }

        return items;
    }

    /**
     * Get freshness status of a file relative to its source.
     */
    private getFileStatus(filePath: string, sourcePath: string): ArtifactStatus {
        if (!fs.existsSync(filePath)) {
            return 'missing';
        }
        if (fs.existsSync(sourcePath)) {
            const fileMtime = fs.statSync(filePath).mtimeMs;
            const sourceMtime = fs.statSync(sourcePath).mtimeMs;
            return fileMtime >= sourceMtime - FRESHNESS_TOLERANCE_MS ? 'fresh' : 'stale';
        }
        return 'fresh';
    }
}
