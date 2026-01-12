#!/usr/bin/env node
/**
 * Setup script for VitePress documentation
 * Prepares the docs directory structure before building
 */

import { existsSync, mkdirSync, cpSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');
const docsDir = join(__dirname); // docs/ is this script's directory

console.log('Setting up documentation structure...\n');

// Copy README as index (Chinese version) to docs/
const readmeZh = join(rootDir, 'README.md');
if (existsSync(readmeZh)) {
  const content = readFileSync(readmeZh, 'utf8');
  // Replace /doc/ paths with docs/ for correct GitHub links, and then with / for clean web URLs
  const modifiedContent = content
    .replace(/\(\/doc\//g, '(/docs/')
    .replace(/src="\/doc\//g, 'src="/docs/')
    .replace(/\(\/docs\//g, '(/')
    .replace(/src="\/docs\//g, 'src="/');
  writeFileSync(join(docsDir, 'index.md'), modifiedContent);
  console.log('✓ Copied README.md to docs/index.md');
}

// Copy English README if exists
const readmeEn = join(rootDir, 'README.en.md');
if (existsSync(readmeEn)) {
  const enDir = join(docsDir, 'en');
  if (!existsSync(enDir)) {
    mkdirSync(enDir, { recursive: true });
  }
  const content = readFileSync(readmeEn, 'utf8');
  // Replace /doc/ paths with docs/ for correct GitHub links, and then with / for clean web URLs
  const modifiedContent = content
    .replace(/\(\/doc\//g, '(/docs/')
    .replace(/src="\/doc\//g, 'src="/docs/')
    .replace(/\(\/docs\//g, '(/')
    .replace(/src="\/docs\//g, 'src="/');
  writeFileSync(join(enDir, 'index.md'), modifiedContent);
  console.log('✓ Copied README.en.md to docs/en/index.md');
}

// Copy schema directory to docs/public/schema (accessible as /schema/ in build)
const schemaDir = join(rootDir, 'schema');
const publicDir = join(docsDir, 'public');
if (existsSync(schemaDir)) {
  if (!existsSync(publicDir)) {
    mkdirSync(publicDir, { recursive: true });
  }
  const targetSchemaDir = join(publicDir, 'schema');
  cpSync(schemaDir, targetSchemaDir, { recursive: true, force: true });
  console.log('✓ Copied schema/ to docs/public directory');
}

console.log('\nDocumentation structure setup complete!\n');
