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
const rootDir = join(__dirname, '..', '..');
const docsDir = join(__dirname, '..'); // docs/ is parent directory

console.log('Setting up documentation structure...\n');

// Process README files (both Chinese and English)
function processReadme(sourcePath, targetPath, pathPrefix) {
  if (!existsSync(sourcePath)) {
    return false;
  }
  
  const content = readFileSync(sourcePath, 'utf8');
  // Replace docs/ paths with / for clean web URLs
  const modifiedContent = content
    .replace(new RegExp(`\\(${pathPrefix}`, 'g'), '(/')
    .replace(/src="docs\//g, 'src="/');
  
  const targetDir = dirname(targetPath);
  if (!existsSync(targetDir)) {
    mkdirSync(targetDir, { recursive: true });
  }
  
  writeFileSync(targetPath, modifiedContent);
  return true;
}

// Copy README as index (Chinese version) to docs/
if (processReadme(
  join(rootDir, 'README.md'),
  join(docsDir, 'index.md'),
  'docs/'
)) {
  console.log('✓ Copied README.md to docs/index.md');
}

// Copy English README if exists
if (processReadme(
  join(rootDir, 'README.en.md'),
  join(docsDir, 'en', 'index.md'),
  'docs/en/'
)) {
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
