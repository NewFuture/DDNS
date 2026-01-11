#!/usr/bin/env node
/**
 * Setup script for VitePress documentation
 * Prepares the docs directory structure before building
 */

import { copyFileSync, existsSync, mkdirSync, cpSync, readFileSync, writeFileSync, readdirSync } from 'fs';
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

// Copy README as index (Chinese version)
const readmeZh = join(rootDir, 'README.md');
if (existsSync(readmeZh)) {
  const content = readFileSync(readmeZh, 'utf8');
  // Replace /doc/ paths with / in README for clean URLs
  const modifiedContent = content
    .replace(/\(\/doc\//g, '(/')
    .replace(/src="\/doc\//g, 'src="/');
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
  // Replace /doc/ paths with / in README for clean URLs
  const modifiedContent = content
    .replace(/\(\/doc\//g, '(/')
    .replace(/src="\/doc\//g, 'src="/');
  writeFileSync(join(enDir, 'index.md'), modifiedContent);
  console.log('✓ Copied README.en.md to docs/en/index.md');
}

// Copy doc directory contents to docs root (remove /doc/ prefix from URLs)
const docDir = join(rootDir, 'doc');
if (existsSync(docDir)) {
  // Copy each item from doc/ to docs/ root
  const items = readdirSync(docDir);
  for (const item of items) {
    const sourcePath = join(docDir, item);
    const targetPath = join(docsDir, item);
    cpSync(sourcePath, targetPath, { recursive: true, force: true });
  }
  console.log('✓ Copied doc/ contents to docs/ root');
  
  // For English version, also copy the doc directory contents
  const enDir = join(docsDir, 'en');
  if (existsSync(enDir)) {
    for (const item of items) {
      const sourcePath = join(docDir, item);
      const targetPath = join(enDir, item);
      cpSync(sourcePath, targetPath, { recursive: true, force: true });
    }
    console.log('✓ Copied doc/ contents to English version');
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
