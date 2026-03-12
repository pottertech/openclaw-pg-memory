#!/usr/bin/env node
/**
 * pg-memory Compaction Hook for OpenClaw
 * Simplified version - calls Python handler directly
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

export async function handleCompactionStart(params) {
  console.log('[pg-memory] 🧠 Pre-compaction save starting...');
  
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
    // NOTE: Token management handled by token-guardian
    // pg-memory only handles memory persistence
    timestamp: new Date().toISOString()
  };
  
  await runHandler('pre-compaction', data);
  console.log('[pg-memory] ✅ Pre-compaction complete');
  return params;
}

export async function handleCompactionEnd(params) {
  console.log('[pg-memory] 🧠 Post-compaction context restore...');
  
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
  
  await runHandler('post-compaction', data);
  console.log('[pg-memory] ✅ Post-compaction complete');
  return params;
}

export default { handleCompactionStart, handleCompactionEnd };
