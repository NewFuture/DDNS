#!/usr/bin/env node
/**
 * Setup script for VitePress documentation
 * Prepares the docs directory structure before building
 */

import { copyFileSync, existsSync, mkdirSync, cpSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');

console.log('Setting up documentation structure...\n');

// Create docs directory if it doesn't exist
const docsDir = join(rootDir, 'docs');
if (!existsSync(docsDir)) {
  mkdirSync(docsDir, { recursive: true });
}

// Copy README as index (without modifying paths)
const readmeZh = join(rootDir, 'README.md');
if (existsSync(readmeZh)) {
  copyFileSync(readmeZh, join(docsDir, 'index.md'));
  console.log('✓ Copied README.md to docs/index.md');
}

// Copy English README if exists (without modifying paths)
const readmeEn = join(rootDir, 'README.en.md');
if (existsSync(readmeEn)) {
  const enDir = join(docsDir, 'en');
  if (!existsSync(enDir)) {
    mkdirSync(enDir, { recursive: true });
  }
  copyFileSync(readmeEn, join(enDir, 'index.md'));
  console.log('✓ Copied README.en.md to docs/en/index.md');
}

// Copy doc directory (keep structure intact for /doc/ paths in README)
const docDir = join(rootDir, 'doc');
if (existsSync(docDir)) {
  // Copy to docs/doc/ to preserve /doc/ paths
  const targetDocDir = join(docsDir, 'doc');
  cpSync(docDir, targetDocDir, { recursive: true, force: true });
  console.log('✓ Copied doc/ directory');
  
  // For English version, also copy the doc directory
  const enDir = join(docsDir, 'en');
  if (existsSync(enDir)) {
    const enDocDir = join(enDir, 'doc');
    cpSync(docDir, enDocDir, { recursive: true, force: true });
    console.log('✓ Copied doc/ to English version');
  }
}

// Copy schema directory to public/schema (accessible as /schema/ in build)
const schemaDir = join(rootDir, 'schema');
const publicDir = join(docsDir, 'public');
if (existsSync(schemaDir)) {
  if (!existsSync(publicDir)) {
    mkdirSync(publicDir, { recursive: true });
  }
  const targetSchemaDir = join(publicDir, 'schema');
  cpSync(schemaDir, targetSchemaDir, { recursive: true, force: true });
  console.log('✓ Copied schema/ to public directory');
}

console.log('\nDocumentation structure setup complete!\n');
