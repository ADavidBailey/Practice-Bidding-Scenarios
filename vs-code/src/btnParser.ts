import * as fs from 'fs';
import * as path from 'path';

export interface BtnMetadata {
    bbaWorks: boolean;
    gibWorks: boolean;
    auctionFilter: string | undefined;
}

// Cache to avoid repeated file reads
const metadataCache = new Map<string, BtnMetadata>();

/**
 * Get metadata from a BTN file for a scenario.
 * Results are cached for performance.
 *
 * @param scenario Scenario name (e.g., "Smolen")
 * @param workspaceRoot Workspace root path
 * @returns Metadata object with bbaWorks, gibWorks, and auctionFilter
 */
export function getBtnMetadata(scenario: string, workspaceRoot: string): BtnMetadata {
    const cacheKey = `${workspaceRoot}:${scenario}`;

    if (metadataCache.has(cacheKey)) {
        return metadataCache.get(cacheKey)!;
    }

    const btnPath = path.join(workspaceRoot, 'btn', `${scenario}.btn`);
    const metadata: BtnMetadata = {
        bbaWorks: false,  // Default to false if not specified
        gibWorks: false,  // Default to false if not specified
        auctionFilter: undefined
    };

    if (!fs.existsSync(btnPath)) {
        return metadata;
    }

    try {
        const content = fs.readFileSync(btnPath, 'utf-8');
        const lines = content.split('\n').slice(0, 20); // Only check first 20 lines

        for (const line of lines) {
            const bbaMatch = line.match(/^#\s*bba-works:\s*(.+)$/i);
            if (bbaMatch) {
                metadata.bbaWorks = bbaMatch[1].trim().toLowerCase() === 'true';
            }

            const gibMatch = line.match(/^#\s*gib-works:\s*(.+)$/i);
            if (gibMatch) {
                metadata.gibWorks = gibMatch[1].trim().toLowerCase() === 'true';
            }

            const filterMatch = line.match(/^#\s*auction-filter:\s*(.+)$/i);
            if (filterMatch) {
                metadata.auctionFilter = filterMatch[1].trim();
            }
        }
    } catch {
        // Return defaults on error
    }

    metadataCache.set(cacheKey, metadata);
    return metadata;
}

/**
 * Clear the metadata cache.
 * Should be called when BTN files change.
 */
export function clearMetadataCache(): void {
    metadataCache.clear();
}
