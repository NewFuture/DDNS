#!/usr/bin/env node
/**
 * Setup script for VitePress documentation
 * Prepares the doc directory structure before building
 */

import { copyFileSync, existsSync, mkdirSync, cpSync, readFileSync, writeFileSync, readdirSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');
const docDir = join(__dirname); // doc/ is this script's directory

console.log('Setting up documentation structure...\n');

// Copy README as index (Chinese version) to doc/
const readmeZh = join(rootDir, 'README.md');
if (existsSync(readmeZh)) {
  const content = readFileSync(readmeZh, 'utf8');
  // Replace /doc/ paths with / in README for clean URLs
  const modifiedContent = content
    .replace(/\(\/doc\//g, '(/')
    .replace(/src="\/doc\//g, 'src="/');
  writeFileSync(join(docDir, 'index.md'), modifiedContent);
  console.log('✓ Copied README.md to doc/index.md');
}

// Copy English README if exists
const readmeEn = join(rootDir, 'README.en.md');
if (existsSync(readmeEn)) {
  const enDir = join(docDir, 'en');
  if (!existsSync(enDir)) {
    mkdirSync(enDir, { recursive: true });
  }
  const content = readFileSync(readmeEn, 'utf8');
  // Replace /doc/ paths with / in README for clean URLs
  const modifiedContent = content
    .replace(/\(\/doc\//g, '(/')
    .replace(/src="\/doc\//g, 'src="/');
  writeFileSync(join(enDir, 'index.md'), modifiedContent);
  console.log('✓ Copied README.en.md to doc/en/index.md');
  
  // For English version, create symlinks to doc content directories
  const items = readdirSync(docDir);
  for (const item of items) {
    if (item === 'en' || item === '.vitepress' || item === 'index.md' || 
        item === 'setup-docs.mjs' || item === 'public') continue;
    
    const sourcePath = join(docDir, item);
    const targetPath = join(enDir, item);
    
    if (statSync(sourcePath).isDirectory() || item.endsWith('.md')) {
      cpSync(sourcePath, targetPath, { recursive: true, force: true });
    }
  }
  console.log('✓ Copied doc/ contents to doc/en/ for English version');
}

// Copy schema directory to doc/public/schema (accessible as /schema/ in build)
const schemaDir = join(rootDir, 'schema');
const publicDir = join(docDir, 'public');
if (existsSync(schemaDir)) {
  if (!existsSync(publicDir)) {
    mkdirSync(publicDir, { recursive: true });
  }
  const targetSchemaDir = join(publicDir, 'schema');
  cpSync(schemaDir, targetSchemaDir, { recursive: true, force: true });
  console.log('✓ Copied schema/ to doc/public directory');
}

// Copy install.sh to doc/public (accessible as /install.sh in build)
const installSh = join(rootDir, 'install.sh');
if (existsSync(installSh)) {
  if (!existsSync(publicDir)) {
    mkdirSync(publicDir, { recursive: true });
  }
  copyFileSync(installSh, join(publicDir, 'install.sh'));
  console.log('✓ Copied install.sh to doc/public directory');
}

console.log('\nDocumentation structure setup complete!\n');
