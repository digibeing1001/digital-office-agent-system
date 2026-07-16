#!/usr/bin/env node
/** Guided, resumable multi-team Bot registration using Feishu registerApp OAuth. */

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

function fail(message) {
  process.stderr.write(`${JSON.stringify({ error: message })}\n`);
  process.exit(2);
}

function argumentsOf(argv) {
  const value = { manifests: [], only: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === '--confirm-create') value.confirm = true;
    else if (item === '--manifest') value.manifests.push(argv[++index]);
    else if (['--output', '--sdk-root', '--lark-cli', '--notify-chat-id', '--notify-profile', '--event-file'].includes(item)) {
      value[item.slice(2).replaceAll('-', '_')] = argv[++index];
    } else if (item === '--only') value.only.push(argv[++index]);
    else fail(`unknown argument: ${item}`);
  }
  if (!value.manifests.length) fail('at least one --manifest is required');
  if (Boolean(value.notify_chat_id) !== Boolean(value.notify_profile)) {
    fail('--notify-chat-id and --notify-profile must be supplied together');
  }
  value.output ||= path.resolve('.digital-office/feishu-bot-inventory.json');
  value.sdk_root ||= path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../feishu-bootstrap');
  value.lark_cli ||= process.platform === 'win32' ? 'lark-cli.cmd' : 'lark-cli';
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

function appendEvent(args, event, details = {}) {
  if (!args.event_file) return;
  const file = path.resolve(args.event_file);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file, `${JSON.stringify({
    schema_version: '1.0', time: new Date().toISOString(), event, ...details,
  })}\n`, { mode: 0o600 });
  try { fs.chmodSync(file, 0o600); } catch { /* Windows ACL is managed by the user profile. */ }
}

function cli(executable, profile, args, input) {
  const result = spawnSync(executable, profile ? ['--profile', profile, ...args] : args, {
    input, encoding: 'utf8', windowsHide: true, shell: process.platform === 'win32',
  });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout || `lark-cli exited ${result.status}`);
  return result.stdout;
}

function notificationKey(botKey, phase) {
  return createHash('sha256').update(`${botKey}:${phase}`).digest('hex').slice(0, 40);
}

function notify(args, botKey, phase, markdown) {
  if (!args.notify_chat_id) return;
  cli(args.lark_cli, args.notify_profile, [
    'im', '+messages-send', '--chat-id', args.notify_chat_id, '--markdown', markdown,
    '--idempotency-key', notificationKey(botKey, phase), '--as', 'bot',
  ]);
}

function bestEffortNotify(args, botKey, phase, markdown) {
  try { notify(args, botKey, phase, markdown); }
  catch (error) { process.stderr.write(`[notify-warning] ${error?.message || error}\n`); }
}

function inventoryOf(file) {
  if (!fs.existsSync(file)) {
    return { version: '2.0.0', kind: 'digital-office-feishu-bot-inventory', bots: {} };
  }
  const current = readJson(file);
  if (current.version === '2.0.0' && current.bots && typeof current.bots === 'object') return current;
  if (current.team_id && current.agents && typeof current.agents === 'object') {
    const bots = {};
    for (const [agentId, record] of Object.entries(current.agents)) {
      bots[`${current.team_id}/${agentId}`] = { team_id: current.team_id, agent_id: agentId, ...record };
    }
    return { version: '2.0.0', kind: 'digital-office-feishu-bot-inventory', bots };
  }
  throw new Error('unsupported bot inventory format');
}

async function sdkFrom(root) {
  const require = createRequire(path.resolve(root, 'package.json'));
  try { return require('@larksuiteoapi/node-sdk'); }
  catch { fail(`Feishu SDK not installed. Run: npm --prefix "${root}" install`); }
}

function tasksOf(args) {
  const selectors = new Set(args.only);
  const tasks = [];
  for (const manifestPath of args.manifests) {
    const manifest = readJson(path.resolve(manifestPath));
    for (const agent of manifest.agents || []) {
      const botKey = `${manifest.team_id}/${agent.agent_id}`;
      if (!selectors.size || selectors.has(agent.agent_id) || selectors.has(botKey)) {
        tasks.push({ manifest, agent, botKey });
      }
    }
  }
  const known = new Set(tasks.map(({ botKey }) => botKey));
  if (known.size !== tasks.length) fail('duplicate team_id/agent_id Bot identity across manifests');
  const profiles = new Set(tasks.map(({ agent }) => agent.profile));
  if (profiles.size !== tasks.length) fail('each selected Bot must use a unique lark-cli profile');
  for (const selector of selectors) {
    const matched = tasks.some(({ botKey, agent }) => selector === botKey || selector === agent.agent_id);
    if (!matched) fail(`unknown agent selector: ${selector}`);
  }
  return tasks;
}

async function main() {
  const args = argumentsOf(process.argv.slice(2));
  const tasks = tasksOf(args);
  const plan = {
    action: 'register_feishu_agent_bots', count: tasks.length,
    bots: tasks.map(({ manifest, agent, botKey }) => ({
      bot_key: botKey, team_id: manifest.team_id, agent_id: agent.agent_id, profile: agent.profile,
    })),
    notification_target: args.notify_chat_id ? { chat_id: args.notify_chat_id, profile: args.notify_profile } : null,
    requires_online_confirmation_per_missing_bot: true,
    resumes_ready_bots_without_reauthorization: true,
    app_secret_storage: 'lark-cli profile credential store; never inventory, chat, or stdout',
  };
  if (!args.confirm) {
    process.stdout.write(`${JSON.stringify({ dry_run: true, ...plan }, null, 2)}\n`);
    return;
  }

  const lark = await sdkFrom(args.sdk_root);
  const inventory = inventoryOf(args.output);
  let readyCount = 0;
  appendEvent(args, 'session_started', { bot_count: tasks.length });
  for (const { manifest, agent, botKey } of tasks) {
    if (inventory.bots[botKey]?.status === 'ready') {
      readyCount += 1;
      process.stderr.write(`[skip] ${botKey} already ready in inventory\n`);
      appendEvent(args, 'already_ready', { bot_key: botKey, display_name: agent.display_name || botKey, ready_count: readyCount, bot_count: tasks.length });
      bestEffortNotify(args, botKey, 'already-ready', `✅ **${agent.display_name || botKey}** 已导入，无需再次授权。（${readyCount}/${tasks.length}）`);
      continue;
    }
    process.stderr.write(`[authorize] ${botKey}\n`);
    appendEvent(args, 'authorizing', { bot_key: botKey, display_name: agent.display_name || botKey, ready_count: readyCount, bot_count: tasks.length });
    try {
      const created = await lark.registerApp({
        createOnly: true,
        source: 'digital-office-agent-team',
        appPreset: {
          name: agent.display_name || `Digital Office ${agent.agent_id}`,
          desc: `Project specialist Agent: ${botKey}`,
        },
        onQRCodeReady(info) {
          process.stderr.write(`[confirm:${botKey}] ${info.url} (expires in ${info.expireIn}s)\n`);
          appendEvent(args, 'authorization_required', {
            bot_key: botKey, display_name: agent.display_name || botKey,
            authorization_url: info.url, expires_in: info.expireIn,
            ready_count: readyCount, bot_count: tasks.length,
          });
          bestEffortNotify(
            args, botKey, `authorization-required:${info.url}`,
            `### 需要授权：${agent.display_name || botKey}\n请在 ${info.expireIn} 秒内[打开飞书授权页面](${info.url})并确认。完成后导入会自动继续。\n\n角色标识：\`${botKey}\``,
          );
        },
        onStatusChange(info) { process.stderr.write(`[${botKey}] ${info.status}\n`); },
      });
      cli(args.lark_cli, null, ['profile', 'add', '--name', agent.profile, '--app-id', created.client_id, '--app-secret-stdin'], `${created.client_secret}\n`);
      const botInfo = JSON.parse(cli(args.lark_cli, agent.profile, ['api', 'GET', '/open-apis/bot/v3/info', '--json']));
      const bot = botInfo.bot || botInfo.data?.bot || botInfo.data || {};
      inventory.bots[botKey] = {
        status: 'ready', team_id: manifest.team_id, agent_id: agent.agent_id,
        profile: agent.profile, app_id: created.client_id,
        open_id: bot.open_id || bot.bot?.open_id || '',
        app_id_env: agent.app_id_env, open_id_env: agent.open_id_env,
      };
      readyCount += 1;
      writeInventory(args.output, inventory);
      process.stderr.write(`[ready] ${botKey}\n`);
      appendEvent(args, 'ready', { bot_key: botKey, display_name: agent.display_name || botKey, ready_count: readyCount, bot_count: tasks.length });
      bestEffortNotify(args, botKey, 'ready', `✅ **${agent.display_name || botKey}** 已完成导入。（${readyCount}/${tasks.length}）`);
    } catch (error) {
      inventory.bots[botKey] = {
        status: 'authorization_required', team_id: manifest.team_id, agent_id: agent.agent_id,
        profile: agent.profile, app_id_env: agent.app_id_env, open_id_env: agent.open_id_env,
      };
      writeInventory(args.output, inventory);
      appendEvent(args, 'failed', {
        bot_key: botKey, display_name: agent.display_name || botKey,
        error_code: 'registration_failed', ready_count: readyCount, bot_count: tasks.length,
      });
      bestEffortNotify(args, botKey, 'retry-required', `⚠️ **${agent.display_name || botKey}** 尚未完成授权。请重新执行导入命令；已完成角色会自动跳过。`);
      throw error;
    }
  }
  appendEvent(args, 'session_complete', { ready_count: readyCount, bot_count: tasks.length });
  bestEffortNotify(args, 'all-selected-bots', 'complete', `🎉 Agent 导入完成：${readyCount}/${tasks.length}。现在可以发布任务并确认项目编组。`);
  process.stdout.write(`${JSON.stringify({
    status: 'ready', inventory: path.resolve(args.output), bot_keys: tasks.map(({ botKey }) => botKey),
  }, null, 2)}\n`);
}

main().catch((error) => fail(error?.message || String(error)));
