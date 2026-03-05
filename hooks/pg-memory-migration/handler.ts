#!/usr/bin/env node
/**
 * pg-memory Migration Hook
 * 
 * Automatically migrates markdown memory files to PostgreSQL
 * when /new or /reset is run.
 */

import { createSubsystemLogger } from '../../subsystem-nlluZawe.js';
import { resolveAgentWorkspaceDir } from '../../agent-scope-DWsn5rte.js';
import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import fs from 'node:fs/promises';

const execAsync = promisify(exec);
const log = createSubsystemLogger('hooks/pg-memory-migration');

// Path to migration script
const MIGRATION_SCRIPT = path.join(
  process.env.HOME || process.env.USERPROFILE || '',
  '.openclaw/workspace/repos/openclaw-pg-memory/scripts/migrate-markdown-to-pgmemory.py'
);

// Path to log file
const LOG_FILE = path.join(
  process.env.HOME || process.env.USERPROFILE || '',
  '.openclaw/workspace/logs/pg-memory-migration.log'
);

/**
 * Check if migration script exists
 */
async function isMigrationScriptAvailable() {
  try {
    await fs.access(MIGRATION_SCRIPT);
    return true;
  } catch {
    return false;
  }
}

/**
 * Run migration script
 */
async function runMigration() {
  const command = `python3 ${MIGRATION_SCRIPT}`;
  
  try {
    log.info('🦞 Starting pg-memory migration...');
    
    const { stdout, stderr } = await execAsync(command, {
      env: { ...process.env },
      cwd: path.dirname(MIGRATION_SCRIPT)
    });

    // Log output
    if (stdout) {
      log.info(stdout);
      // Also append to log file
      await fs.appendFile(LOG_FILE, `[${new Date().toISOString()}] ${stdout}\n`);
    }
    
    if (stderr) {
      log.warn(stderr);
      await fs.appendFile(LOG_FILE, `[${new Date().toISOString()}] WARN: ${stderr}\n`);
    }
    
    log.info('✅ pg-memory migration complete');
    return true;
    
  } catch (error) {
    const errorMsg = `Migration failed: ${error.message}`;
    log.error(errorMsg);
    await fs.appendFile(LOG_FILE, `[${new Date().toISOString()}] ERROR: ${errorMsg}\n`);
    return false;
  }
}

/**
 * Handle /new command
 */
export async function handleCommandNew(params) {
  log.info('🦞 pg-memory migration hook triggered by /new');

  // Check if migration script exists
  if (!await isMigrationScriptAvailable()) {
    log.warn('Migration script not found, skipping');
    return params;
  }

  // Run migration in background (don't block /new)
  runMigration().catch(err => {
    log.error(`Background migration failed: ${err.message}`);
  });

  return params;
}

/**
 * Handle /reset command
 */
export async function handleCommandReset(params) {
  log.info('🦞 pg-memory migration hook triggered by /reset');

  // Check if migration script exists
  if (!await isMigrationScriptAvailable()) {
    log.warn('Migration script not found, skipping');
    return params;
  }

  // Run migration in background (don't block /reset)
  runMigration().catch(err => {
    log.error(`Background migration failed: ${err.message}`);
  });

  return params;
}

// Export handlers
export default {
  handleCommandNew,
  handleCommandReset
};
