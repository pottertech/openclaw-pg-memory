#!/usr/bin/env node
/**
 * pg-memory Capture Hook for OpenClaw
 * 
 * PURPOSE: Capture memory to PostgreSQL before compaction, restore from stored memory after.
 * 
 * OWNERSHIP:
 * - This hook handles MEMORY PERSISTENCE ONLY
 * - Token management, overflow protection, and compaction decisions are owned by openclaw-token-guardian
 * - This hook does NOT decide when compaction happens, monitor tokens, or prevent overflow
 * 
 * For token management, install: openclaw-token-guardian
 */

import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import fs from 'node:fs/promises';

const execAsync = promisify(exec);

const MEMORY_HANDLER = path.join(
  process.env.HOME || '',
  '.openclaw/workspace/skills/pg-memory/scripts/memory_handler.py'
);

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function runHandler(mode, data) {
  return new Promise((resolve) => {
    const proc = execAsync(`python3 ${MEMORY_HANDLER} ${mode}`, {
      env: { ...process.env, PG_MEMORY_DEBUG: '1' },
      input: JSON.stringify(data)
    });
    
    proc.then(({ stdout, stderr }) => {
      if (stdout) console.log(`[pg-memory] ${stdout}`);
      if (stderr) console.warn(`[pg-memory] ${stderr}`);
      resolve(true);
    }).catch((err) => {
      console.error(`[pg-memory] Error: ${err.message}`);
      resolve(false);
    });
  });
}

/**
 * Capture memory to PostgreSQL before compaction
 * NOTE: Compaction decision made by token-guardian. This only handles persistence.
 */
export async function handleCaptureStart(params) {
  console.log('[pg-memory] 🧠 Capturing memory to PostgreSQL...');
  
  if (!await fileExists(MEMORY_HANDLER)) {
    console.warn('[pg-memory] Handler not found, skipping');
    return params;
  }
  
  const data = {
    session_key: params.sessionKey || 'unknown',
    session_id: params.sessionId || 'unknown',
    exchanges: params.exchanges || [],
    observations: params.observations || [],
    tool_calls: params.toolCalls || [],
    metadata: {
      provider: params.provider,
      channel_id: params.channelId,
      user: params.user
    },
    // Token management handled by token-guardian
    // pg-memory only handles durable persistence
    timestamp: new Date().toISOString()
  };
  
  await runHandler('capture', data);
  console.log('[pg-memory] ✅ Memory captured to PostgreSQL');
  return params;
}

/**
 * Restore memory from PostgreSQL after compaction
 * NOTE: Restoration timing decided by token-guardian. This only loads persisted memory.
 */
export async function handleRestoreEnd(params) {
  console.log('[pg-memory] 🧠 Restoring memory from PostgreSQL...');
  
  if (!await fileExists(MEMORY_HANDLER)) {
    console.warn('[pg-memory] Handler not found, skipping');
    return params;
  }
  
  const data = {
    session_key: params.sessionKey || 'unknown',
    session_id: params.sessionId || 'unknown',
    metadata: {
      provider: params.provider,
      channel_id: params.channelId,
      user: params.user
    },
    timestamp: new Date().toISOString()
  };
  
  await runHandler('restore', data);
  console.log('[pg-memory] ✅ Memory restored from PostgreSQL');
  return params;
}

// Backwards compatibility aliases (deprecated)
export const handleCompactionStart = handleCaptureStart;
export const handleCompactionEnd = handleRestoreEnd;

export default { handleCaptureStart, handleRestoreEnd, handleCompactionStart, handleCompactionEnd };
