import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { PbsButton, PbsSection, parsePbsDirectory, parseMainPbsConfig } from './pbsParser';

/**
 * Tree item representing either a section header or a button
 */
export class PbsTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly button?: PbsButton,
        public readonly isSection: boolean = false,
        public readonly sectionColor?: string
    ) {
        super(label, collapsibleState);

        if (button && button.filePath) {
            this.tooltip = this.createTooltip(button);
            this.command = {
                command: 'pbs.openPbsFile',
                title: 'Open PBS File',
                arguments: [button.filePath, button.lineNumber]
            };

            // Set icon based on background color
            // lightpink = convention not known by GIB (show warning icon)
            // lightgreen = control buttons (no icon)
            // no color = regular scenario (no icon)
            if (button.backgroundColor === 'lightpink') {
                this.iconPath = new vscode.ThemeIcon('circle-slash', new vscode.ThemeColor('errorForeground'));
            }
            // No icon for lightgreen (control buttons) or regular scenarios
        } else if (isSection) {
            // Section header styling
            if (sectionColor === 'lightblue') {
                this.iconPath = new vscode.ThemeIcon('folder', new vscode.ThemeColor('charts.blue'));
            } else if (sectionColor === 'LemonChiffon') {
                this.iconPath = new vscode.ThemeIcon('folder', new vscode.ThemeColor('charts.yellow'));
            } else if (sectionColor === 'gray') {
                this.iconPath = new vscode.ThemeIcon('question', new vscode.ThemeColor('disabledForeground'));
            } else {
                this.iconPath = new vscode.ThemeIcon('folder');
            }
        }
    }

    private createTooltip(button: PbsButton): vscode.MarkdownString {
        const md = new vscode.MarkdownString();
        md.appendMarkdown(`**${button.label}**\n\n`);

        if (button.description) {
            // Convert bridge notation to Unicode symbols for display
            const description = button.description
                .replace(/!S/g, '\u2660')  // Spade
                .replace(/!H/g, '\u2665')  // Heart
                .replace(/!D/g, '\u2666')  // Diamond
                .replace(/!C/g, '\u2663'); // Club
            md.appendText(description);
            md.appendMarkdown('\n\n');
        }

        if (button.scriptId) {
            md.appendMarkdown(`*Script: ${button.scriptId}*\n`);
        }

        if (button.filePath) {
            md.appendMarkdown(`\n---\n*Click to open file*`);
        }

        return md;
    }
}

/**
 * TreeDataProvider for the PBS Button Panel sidebar
 */
export class ButtonPanelProvider implements vscode.TreeDataProvider<PbsTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<PbsTreeItem | undefined | null | void> = new vscode.EventEmitter<PbsTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<PbsTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private sections: PbsSection[] = [];
    private buttonsByScriptId: Map<string, PbsButton> = new Map();
    private unmappedButtons: PbsButton[] = [];

    constructor(private workspaceRoot: string | undefined) {
        this.loadData().then(() => {
            this._onDidChangeTreeData.fire();
        });
    }

    refresh(): void {
        this.loadData().then(() => {
            this._onDidChangeTreeData.fire();
        });
    }

    private async loadData(): Promise<void> {
        if (!this.workspaceRoot) {
            return;
        }

        // First, load all buttons from PBS directory
        const pbsDir = path.join(this.workspaceRoot, 'PBS');
        const buttons = await parsePbsDirectory(pbsDir);

        // Index buttons by script ID and by filename (for fallback matching)
        this.buttonsByScriptId.clear();
        const buttonsByFilename = new Map<string, PbsButton>();

        for (const button of buttons) {
            if (button.scriptId) {
                this.buttonsByScriptId.set(button.scriptId, button);
            }
            if (button.filePath) {
                // Extract filename without path for fallback matching
                const filename = path.basename(button.filePath);
                buttonsByFilename.set(filename, button);
            }
        }

        // Try to load the main config file for section structure
        const mainConfigPath = path.join(this.workspaceRoot, '-PBS.txt');
        if (fs.existsSync(mainConfigPath)) {
            this.sections = parseMainPbsConfig(mainConfigPath);

            // Resolve file paths for imported buttons and track which files are mapped
            const mappedFilePaths = new Set<string>();

            for (const section of this.sections) {
                for (let i = 0; i < section.buttons.length; i++) {
                    const button = section.buttons[i];
                    if (button.scriptId && !button.filePath) {
                        // Try to resolve by scriptId first
                        let resolvedButton = this.buttonsByScriptId.get(button.scriptId);

                        // If not found and we have a targetFilename, try that
                        if (!resolvedButton && button.targetFilename) {
                            resolvedButton = buttonsByFilename.get(button.targetFilename);
                        }

                        // If not found, try to find by matching filename patterns
                        if (!resolvedButton) {
                            // Normalize the scriptId for comparison (lowercase, no underscores/dashes)
                            const normalizedScriptId = button.scriptId.toLowerCase().replace(/[_-]/g, '');

                            // Search through all filenames for a match
                            let bestMatch: PbsButton | undefined;
                            let bestMatchScore = 0;

                            for (const [filename, btn] of buttonsByFilename) {
                                const normalizedFilename = filename.toLowerCase().replace(/[_-]/g, '');

                                if (normalizedFilename === normalizedScriptId) {
                                    bestMatch = btn;
                                    break;
                                } else if (normalizedFilename.includes(normalizedScriptId)) {
                                    const score = normalizedScriptId.length / normalizedFilename.length;
                                    if (score > bestMatchScore) {
                                        bestMatchScore = score;
                                        bestMatch = btn;
                                    }
                                }
                            }

                            resolvedButton = bestMatch;
                        }

                        if (resolvedButton) {
                            section.buttons[i] = resolvedButton;
                            if (resolvedButton.filePath) {
                                mappedFilePaths.add(resolvedButton.filePath);
                            }
                        }
                    } else if (button.filePath) {
                        // Button already has a file path
                        mappedFilePaths.add(button.filePath);
                    }
                }
            }

            // Find unmapped buttons (PBS files not referenced in any section)
            this.unmappedButtons = buttons.filter(btn =>
                btn.filePath &&
                btn.label &&
                btn.label.trim() !== '' &&
                !mappedFilePaths.has(btn.filePath)
            );
        } else {
            // No main config, create a single section with all buttons
            this.sections = [{
                title: 'PBS Buttons',
                buttons: buttons,
                backgroundColor: 'lightblue'
            }];
        }
    }

    getTreeItem(element: PbsTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: PbsTreeItem): Thenable<PbsTreeItem[]> {
        if (!this.workspaceRoot) {
            vscode.window.showInformationMessage('No workspace folder open');
            return Promise.resolve([]);
        }

        if (!element) {
            // Root level - return sections plus Unmapped section if there are unmapped files
            const validSections = this.sections.filter(section =>
                section.title && section.title.trim() !== ''
            );

            const items: PbsTreeItem[] = validSections
                .map(section => new PbsTreeItem(
                    section.title,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    undefined,
                    true,
                    section.backgroundColor
                ));

            // Add Unmapped section at the bottom if there are unmapped files
            if (this.unmappedButtons.length > 0) {
                items.push(new PbsTreeItem(
                    `Unmapped (${this.unmappedButtons.length})`,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    undefined,
                    true,
                    'gray'
                ));
            }

            return Promise.resolve(items);
        }

        // Check if this is the Unmapped section
        if (element.label?.startsWith('Unmapped')) {
            return Promise.resolve(
                this.unmappedButtons
                    .filter(button => button.label && button.label.trim() !== '' && button.label !== '---')
                    .sort((a, b) => a.label.localeCompare(b.label))
                    .map(button => new PbsTreeItem(
                        button.label,
                        vscode.TreeItemCollapsibleState.None,
                        button,
                        false
                    ))
            );
        }

        // Return buttons in the section
        const section = this.sections.find(s => s.title === element.label);
        if (section) {
            return Promise.resolve(
                section.buttons
                    .filter(button => button.label && button.label.trim() !== '' && button.label !== '---')
                    .map(button => new PbsTreeItem(
                        button.label,
                        vscode.TreeItemCollapsibleState.None,
                        button,
                        false
                    ))
            );
        }

        return Promise.resolve([]);
    }
}
