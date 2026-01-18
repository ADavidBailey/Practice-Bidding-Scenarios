import * as fs from 'fs';
import * as path from 'path';

export interface PbsButton {
    label: string;
    description: string;
    scriptId: string;
    targetFilename?: string;  // Target filename from Import URL for matching
    backgroundColor?: string;
    width?: string;
    filePath: string;
    lineNumber: number;
}

export interface PbsSection {
    title: string;
    buttons: PbsButton[];
    backgroundColor?: string;
}

/**
 * Parse a Button definition from a PBS file.
 * Button format: Button,<label>,<description with \n\>,<styling>
 *
 * Examples:
 *   Button,1m-1x-2m,\n\
 *   --- 1m-1x-2m\n\
 *   %OneMinorTwoMinor%
 *
 *   Button,15-17 NT (Lev),\n\
 *   ---  15-17 Notrump Opening\n\
 *   ...description...\n\
 *   %Notrump%,backgroundColor=lightpink
 */
export function parseButtonDefinition(content: string, filePath: string, startLine: number): PbsButton | null {
    // Find the Button line
    const lines = content.split('\n');
    let buttonContent = '';
    let inButton = false;
    let buttonLineNumber = 0;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith('Button,')) {
            inButton = true;
            buttonLineNumber = startLine + i;
            buttonContent = line;
            // Check if it continues (ends with \n\)
            if (!line.trimEnd().endsWith('\\n\\')) {
                break;
            }
        } else if (inButton) {
            buttonContent += '\n' + line;
            if (!line.trimEnd().endsWith('\\n\\')) {
                break;
            }
        }
    }

    if (!buttonContent) {
        return null;
    }

    return parseButtonLine(buttonContent, filePath, buttonLineNumber);
}

/**
 * Parse a single button line (may span multiple lines with \n\ continuation)
 */
export function parseButtonLine(buttonContent: string, filePath: string, lineNumber: number): PbsButton | null {
    // Remove the "Button," prefix
    if (!buttonContent.startsWith('Button,')) {
        return null;
    }

    const content = buttonContent.substring(7);

    // Join multi-line content (remove \n\ continuations)
    const normalizedContent = content.replace(/\\n\\\s*\n/g, '\\n');

    // Split by comma, but be careful with commas in the description
    // Format: label,description,styling
    const firstCommaIndex = normalizedContent.indexOf(',');
    if (firstCommaIndex === -1) {
        // Just a label, no description (section header or separator)
        const label = normalizedContent.trim();
        if (label === '') {
            return null; // Empty, skip
        }
        // Return the button (including '---' placeholders)
        return {
            label: label,
            description: '',
            scriptId: '',
            filePath,
            lineNumber
        };
    }

    const label = normalizedContent.substring(0, firstCommaIndex).trim();
    const rest = normalizedContent.substring(firstCommaIndex + 1);

    // Extract the script ID (looks like %ScriptName%)
    const scriptIdMatch = rest.match(/%([^%]+)%/);
    const scriptId = scriptIdMatch ? scriptIdMatch[1] : '';

    // Extract styling (after the last % or after the script ID)
    let styling = '';
    let description = rest;

    if (scriptIdMatch) {
        const afterScriptId = rest.substring(rest.lastIndexOf('%' + scriptIdMatch[1] + '%') + scriptIdMatch[0].length);
        if (afterScriptId.startsWith(',')) {
            styling = afterScriptId.substring(1).trim();
        }
        // Description is everything before the script ID
        description = rest.substring(0, rest.indexOf('%' + scriptIdMatch[1] + '%'));
    } else {
        // No script ID - check if rest contains styling (e.g., ",width=100% backgroundColor=lightblue")
        // Format could be: ,styling or description,styling
        const lastCommaIndex = rest.lastIndexOf(',');
        if (lastCommaIndex !== -1) {
            const possibleStyling = rest.substring(lastCommaIndex + 1).trim();
            // Check if it looks like styling (contains = sign)
            if (possibleStyling.includes('=')) {
                styling = possibleStyling;
                description = rest.substring(0, lastCommaIndex);
            }
        }
    }

    // Clean up description - replace \n with actual newlines for display
    description = description
        .replace(/\\n/g, '\n')
        .replace(/,\s*$/, '')
        .trim();

    // Parse styling from the full rest string as fallback (for section headers like ",,width=100% backgroundColor=lightblue")
    const bgMatch = styling.match(/backgroundColor=(\w+)/) || rest.match(/backgroundColor=(\w+)/);
    const widthMatch = styling.match(/width=(\d+%?)/) || rest.match(/width=(\d+%?)/);

    return {
        label,
        description,
        scriptId,
        backgroundColor: bgMatch ? bgMatch[1] : undefined,
        width: widthMatch ? widthMatch[1] : undefined,
        filePath,
        lineNumber
    };
}

/**
 * Parse all PBS files in a directory and extract button definitions
 */
export async function parsePbsDirectory(pbsDir: string): Promise<PbsButton[]> {
    const buttons: PbsButton[] = [];

    if (!fs.existsSync(pbsDir)) {
        return buttons;
    }

    const files = fs.readdirSync(pbsDir);

    for (const file of files) {
        const filePath = path.join(pbsDir, file);
        const stat = fs.statSync(filePath);

        if (stat.isFile()) {
            try {
                const content = fs.readFileSync(filePath, 'utf-8');
                const button = parseButtonFromFile(content, filePath);
                if (button) {
                    buttons.push(button);
                }
            } catch (error) {
                console.error(`Error parsing ${filePath}:`, error);
            }
        }
    }

    return buttons;
}

/**
 * Parse a single PBS file and extract its button definition
 */
export function parseButtonFromFile(content: string, filePath: string): PbsButton | null {
    const lines = content.split('\n');

    // Find the Button definition (usually at the end)
    for (let i = lines.length - 1; i >= 0; i--) {
        if (lines[i].startsWith('Button,')) {
            // Collect all continuation lines
            let buttonContent = lines[i];
            let j = i;
            while (buttonContent.trimEnd().endsWith('\\n\\') && j + 1 < lines.length) {
                j++;
                buttonContent += '\n' + lines[j];
            }

            const button = parseButtonLine(buttonContent, filePath, i + 1);
            if (button && button.label && button.label !== '---') {
                return button;
            }
        }
    }

    return null;
}

/**
 * Parse the main PBS configuration file (-PBS.txt) to understand the panel structure
 */
export function parseMainPbsConfig(configPath: string): PbsSection[] {
    const sections: PbsSection[] = [];

    if (!fs.existsSync(configPath)) {
        return sections;
    }

    const content = fs.readFileSync(configPath, 'utf-8');
    const lines = content.split('\n');

    // First pass: collect import declarations with URLs (scriptId -> targetFilename mapping)
    const importDeclarations: Map<string, string> = new Map();
    for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('Import,')) {
            const parts = trimmedLine.split(',');
            if (parts.length >= 3) {
                const scriptId = parts[1].trim();
                const url = parts[2].trim();
                // Extract filename from URL like .../PBS/GIB_1N
                const urlMatch = url.match(/\/PBS\/([^/]+)$/);
                if (urlMatch) {
                    importDeclarations.set(scriptId, urlMatch[1]);
                }
            }
        }
    }

    let currentSection: PbsSection | null = null;

    // Second pass: process sections and buttons
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // Skip comments and empty lines
        if (line.startsWith('//') || line.startsWith('#') || line === '') {
            continue;
        }

        // Section header button (has backgroundColor=lightblue or LemonChiffon)
        if (line.startsWith('Button,')) {
            const button = parseButtonLine(line, configPath, i + 1);
            if (button) {
                // Check if it's a section header (lightblue or LemonChiffon background)
                if (button.backgroundColor === 'lightblue' || button.backgroundColor === 'LemonChiffon') {
                    if (currentSection) {
                        sections.push(currentSection);
                    }
                    currentSection = {
                        title: button.label,
                        buttons: [],
                        backgroundColor: button.backgroundColor
                    };
                } else if (button.label === '---') {
                    // Placeholder button - add it to the current section
                    if (currentSection) {
                        currentSection.buttons.push(button);
                    }
                } else if (currentSection) {
                    // Regular button in current section
                    currentSection.buttons.push(button);
                }
            }
        }

        // Import statement - this references a PBS file
        if (line.startsWith('Import,')) {
            const parts = line.split(',');
            if (parts.length >= 2 && currentSection) {
                const scriptId = parts[1].trim();
                // Look up target filename from declarations, or extract from URL if present
                let targetFilename = importDeclarations.get(scriptId) || '';
                if (!targetFilename && parts.length >= 3) {
                    const url = parts[2].trim();
                    const urlMatch = url.match(/\/PBS\/([^/]+)$/);
                    if (urlMatch) {
                        targetFilename = urlMatch[1];
                    }
                }
                // Create a placeholder button for the import
                currentSection.buttons.push({
                    label: scriptId,
                    description: '',
                    scriptId: scriptId,
                    targetFilename: targetFilename,  // Store target filename for matching
                    filePath: '',  // Will be resolved later
                    lineNumber: i + 1
                });
            }
        }
    }

    if (currentSection) {
        sections.push(currentSection);
    }

    return sections;
}
