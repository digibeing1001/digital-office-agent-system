#!/usr/bin/env node
/** Guided multi-Bot registration using Feishu's official registerApp OAuth flow. */

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

function fail(message) {
  process.stderr.write(`${JSON.stringify({ error: message })}\n`);
  process.exit(2);
}

function argumentsOf(argv) {
  const value = { only: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === '--confirm-create') value.confirm = true;
    else if (item === '--manifest' || item === '--output' || item === '--sdk-root') value[item.slice(2).replace('-', '_')] = argv[++index];
    else if (item === '--only') value.only.push(argv[++index]);
    else fail(`unknown argument: ${item}`);
  }
  if (!value.manifest) fail('--manifest is required');
  value.output ||= path.resolve('.digital-office/feishu-bot-inventory.json');
  value.sdk_root ||= path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../feishu-bootstrap');
  return value;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeInventory(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
  try { fs.chmodSync(file, 0o600); } catch { /* Windows ACL is managed by the user profile. */ }
}

function cli(profile, args, input) {
  const command = process.platform === 'win32' ? 'lark-cli.cmd' : 'lark-cli';
  const result = spawnSync(command, profile ? ['--profile', profile, ...args] : args, {
    input, encoding: 'utf8', windowsHide: true, shell: process.platform === 'win32',
  });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout || `lark-cli exited ${result.status}`);
  return result.stdout;
}

async function sdkFrom(root) {
  const require = createRequire(path.resolve(root, 'package.json'));
  try { return require('@larksuiteoapi/node-sdk'); }
  catch { fail(`Feishu SDK not installed. Run: npm --prefix "${root}" install`); }
}

async function main() {
  const args = argumentsOf(process.argv.slice(2));
  const manifest = readJson(path.resolve(args.manifest));
  const known = new Set(manifest.agents.map((agent) => agent.agent_id));
  for (const id of args.only) if (!known.has(id)) fail(`unknown agent: ${id}`);
  const selected = manifest.agents.filter((agent) => !args.only.length || args.only.includes(agent.agent_id));
  const plan = {
    action: 'register_feishu_agent_bots', count: selected.length,
    agents: selected.map((agent) => ({ agent_id: agent.agent_id, profile: agent.profile })),
    requires_online_confirmation_per_agent: true,
    app_secret_storage: 'lark-cli profile credential store; never inventory or stdout',
  };
  if (!args.confirm) {
    process.stdout.write(`${JSON.stringify({ dry_run: true, ...plan }, null, 2)}\n`);
    return;
  }

  const lark = await sdkFrom(args.sdk_root);
  const inventory = fs.existsSync(args.output) ? readJson(args.output) : {
    version: '1.0.0', kind: 'digital-office-feishu-bot-inventory', team_id: manifest.team_id, agents: {},
  };
  for (const agent of selected) {
    if (inventory.agents[agent.agent_id]?.status === 'ready') {
      process.stderr.write(`[skip] ${agent.agent_id} already ready in inventory\n`);
      continue;
    }
    process.stderr.write(`[authorize] ${agent.agent_id}\n`);
    const created = await lark.registerApp({
      createOnly: true,
      source: 'digital-office-agent-team',
      appPreset: {
        name: agent.display_name || `Digital Office ${agent.agent_id}`,
        desc: `Project specialist Agent: ${agent.agent_id}`,
      },
      onQRCodeReady(info) {
        process.stderr.write(`[confirm:${agent.agent_id}] ${info.url} (expires in ${info.expireIn}s)\n`);
      },
      onStatusChange(info) { process.stderr.write(`[${agent.agent_id}] ${info.status}\n`); },
    });
    cli(null, ['profile', 'add', '--name', agent.profile, '--app-id', created.client_id, '--app-secret-stdin'], `${created.client_secret}\n`);
    const botInfo = JSON.parse(cli(agent.profile, ['api', 'GET', '/open-apis/bot/v3/info', '--json']));
    const bot = botInfo.bot || botInfo.data?.bot || botInfo.data || {};
    inventory.agents[agent.agent_id] = {
      status: 'ready', profile: agent.profile, app_id: created.client_id,
      open_id: bot.open_id || bot.bot?.open_id || '',
      app_id_env: agent.app_id_env, open_id_env: agent.open_id_env,
    };
    writeInventory(args.output, inventory);
    process.stderr.write(`[ready] ${agent.agent_id}\n`);
  }
  process.stdout.write(`${JSON.stringify({ status: 'ready', inventory: path.resolve(args.output), agents: Object.keys(inventory.agents) }, null, 2)}\n`);
}

main().catch((error) => fail(error?.message || String(error)));
