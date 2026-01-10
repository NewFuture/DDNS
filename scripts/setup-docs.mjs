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

// Copy README as index and fix paths
const readmeZh = join(rootDir, 'README.md');
if (existsSync(readmeZh)) {
  let content = readFileSync(readmeZh, 'utf-8');
  // Remove /doc/ prefix from paths since doc/ is now the web root
  content = content.replace(/\/doc\//g, '/');
  writeFileSync(join(docsDir, 'index.md'), content);
  console.log('✓ Copied README.md to docs/index.md (paths fixed)');
}

// Copy English README if exists and fix paths
const readmeEn = join(rootDir, 'README.en.md');
if (existsSync(readmeEn)) {
  const enDir = join(docsDir, 'en');
  if (!existsSync(enDir)) {
    mkdirSync(enDir, { recursive: true });
  }
  let content = readFileSync(readmeEn, 'utf-8');
  // Remove /doc/ prefix from paths
  content = content.replace(/\/doc\//g, '/');
  writeFileSync(join(enDir, 'index.md'), content);
  console.log('✓ Copied README.en.md to docs/en/index.md (paths fixed)');
}

// Copy doc directory contents to root (doc/ becomes web root)
const docDir = join(rootDir, 'doc');
if (existsSync(docDir)) {
  // Copy doc contents directly to docs root
  cpSync(docDir, docsDir, { recursive: true, force: true });
  console.log('✓ Copied doc/ contents to docs root');
  
  // For English version, also copy the doc directory
  const enDir = join(docsDir, 'en');
  if (existsSync(enDir)) {
    cpSync(docDir, enDir, { recursive: true, force: true });
    console.log('✓ Copied doc/ contents to English version');
  }
}

// Copy schema directory to public (so it's available in the built site)
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
