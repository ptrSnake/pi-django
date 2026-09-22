/**
 * Local harness: loads extensions/index.ts with a stub ExtensionAPI and runs the
 * django_scaffold tool with mocked exec (no real uv) against /tmp targets.
 * Run with: node --experimental-strip-types test/load-test.ts
 */
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import piDjangoExtension from "../extensions/index.ts";

interface MockTool {
	name: string;
	execute: (
		_toolCallId: string,
		params: Record<string, unknown>,
		_signal: AbortSignal | undefined,
		_onUpdate: unknown,
		ctx: unknown,
	) => Promise<{ content: { type: string; text: string }[]; details: unknown }>;
}

const tools: MockTool[] = [];
const commands: string[] = [];

const pi = {
	registerTool: (tool: MockTool) => tools.push(tool),
	registerCommand: (name: string) => commands.push(name),
	exec: async (_cmd: string, _args: string[]) => ({ stdout: "", stderr: "", code: 0, killed: false }),
} as never;

piDjangoExtension(pi as never);

const tool = tools.find((t) => t.name === "django_scaffold");
if (!tool) {
	console.error("FAIL: django_scaffold tool not registered");
	process.exit(1);
}
console.log("tool registered ✓ | commands:", commands.join(", "));

const ui = {
	async select(_title: string, options: string[]): Promise<string | undefined> {
		return options[0];
	},
	notify(_msg: string, _kind?: string): void {},
};

const results: string[] = [];
for (const framework of ["standard", "drf", "ninja"]) {
	const dir = await mkdtemp(join(tmpdir(), `pi-django-${framework}-`));
	const ctx = { hasUI: false, cwd: dir, ui };
	const res = await tool.execute(
		"id",
		{ project_name: "demo", framework, python_version: "3.13", target_dir: "." },
		undefined,
		undefined,
		ctx as never,
	);
	const ok = res.details && (res.details as { error?: boolean }).error !== true;
	if (!ok) {
		console.error(`FAIL ${framework}:`, res.content[0]?.text);
		results.push(`FAIL ${framework}`);
	} else {
		console.log(`OK   ${framework}: ${res.content[0]?.text.split("\n")[0]}`);
		results.push(`OK ${framework}`);
	}
	await rm(dir, { recursive: true, force: true });
}
console.log("\n" + results.join("\n"));