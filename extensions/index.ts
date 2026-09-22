/**
 * pi-django: scaffold Django projects following the Django Styleguide conventions.
 *
 * Registers:
 *  - tool `django_scaffold`: the model can call it to create a whole Django project
 *    (uv-based) in one shot, asking the user for the framework and Python version
 *    when they are not provided.
 *  - command `/django-scaffold`: same logic, usable directly:
 *    `/django-scaffold <project-name> [standard|drf|ninja] [python-version]`
 */

import { StringEnum } from "@earendil-works/pi-ai";
import type {
	ExtensionAPI,
	ExtensionContext,
	ExtensionCommandContext,
} from "@earendil-works/pi-coding-agent";
import { randomBytes } from "node:crypto";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { basename, dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { Static } from "typebox";
import { Type } from "typebox";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TEMPLATES_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..", "templates");

const FRAMEWORKS = ["standard", "drf", "ninja"] as const;
type Framework = (typeof FRAMEWORKS)[number];

const DEFAULT_FRAMEWORK: Framework = "standard";
const PYTHON_VERSIONS = ["3.14", "3.13", "3.12"] as const;
const DEFAULT_PYTHON_VERSION = "3.14";

const FRAMEWORK_LABELS: Record<Framework, string> = {
	standard: "Django standard (server-rendered views + forms + templates)",
	drf: "Django REST Framework (JWT auth)",
	ninja: "Django Ninja (JWT auth)",
};

const RUNTIME_DEPS: Record<Framework, string[]> = {
	standard: ["django", "django-environ", "django-filter"],
	drf: [
		"django",
		"django-environ",
		"django-filter",
		"djangorestframework",
		"djangorestframework-simplejwt",
	],
	ninja: [
		"django",
		"django-environ",
		"django-filter",
		"django-ninja",
		"django-ninja-jwt",
		"djangorestframework-simplejwt", // used directly for RefreshToken in users/api.py
	],
};

const DEV_DEPS = ["ruff", "pytest", "pytest-django", "factory-boy", "django-extensions"];

const UV_TIMEOUT_MS = 600_000; // uv can download a managed Python + resolve deps on first run

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

const ScaffoldParams = Type.Object({
	project_name: Type.String({
		description:
			"Project name (slug, e.g. my-blog). Use '.' to scaffold into the current directory.",
	}),
	framework: Type.Optional(StringEnum(FRAMEWORKS)),
	python_version: Type.Optional(
		Type.String({ description: "Python version, e.g. 3.14 (default: newest stable)" }),
	),
	target_dir: Type.Optional(
		Type.String({
			description:
				"Parent directory where the project folder is created (default: current working directory)",
		}),
	),
});
type ScaffoldParams = Static<typeof ScaffoldParams>;

interface RenderContext {
	projectName: string;
	projectTitle: string;
	pythonVersion: string;
	requiresPython: string;
	ruffTarget: string;
}

interface Fragments {
	thirdPartyApps: string;
	frameworkExtra: string;
}

interface EnvLike {
	hasUI: boolean;
	cwd: string;
	exec: (command: string, args: string[], options?: { cwd?: string; timeout?: number; signal?: AbortSignal }) => Promise<{ stdout: string; stderr: string; code: number; killed: boolean }>;
	ui: {
		select: (title: string, options: string[]) => Promise<string | undefined>;
		notify: (message: string, kind?: "info" | "warning" | "error") => void;
	};
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function slugify(input: string): string {
	return input
		.trim()
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-+|-+$/g, "");
}

function isValidSlug(value: string): boolean {
	return /^[a-z0-9][a-z0-9-]*$/.test(value) && !value.startsWith("-") && !value.endsWith("-");
}

function toTitle(value: string): string {
	return value
		.split("-")
		.map((part) => (part ? part[0]!.toUpperCase() + part.slice(1) : part))
		.join(" ");
}

function normalizePythonVersion(value: string): string {
	const match = /^3\.(\d+)$/.exec(value.trim());
	if (!match) throw new Error(`Invalid Python version: "${value}" (use e.g. 3.14)`);
	return `3.${match[1]}`;
}

function renderTemplate(text: string, ctx: RenderContext, fragments: Fragments): string {
	return text.replace(/__([A-Z_]+)__/g, (match, token: string) => {
		switch (token) {
			case "PROJECT_NAME":
				return ctx.projectName;
			case "PROJECT_TITLE":
				return ctx.projectTitle;
			case "PYTHON_VERSION":
				return ctx.pythonVersion;
			case "REQUIRES_PYTHON":
				return ctx.requiresPython;
			case "RUFF_TARGET":
				return ctx.ruffTarget;
			case "THIRD_PARTY_APPS":
				return fragments.thirdPartyApps;
			case "FRAMEWORK_EXTRA":
				return fragments.frameworkExtra;
			default:
				return match;
		}
	});
}

async function copyRendered(
	srcDir: string,
	destDir: string,
	ctx: RenderContext,
	fragments: Fragments,
): Promise<string[]> {
	const written: string[] = [];
	await mkdir(destDir, { recursive: true });
	const entries = await readdir(srcDir, { withFileTypes: true });
	for (const entry of entries) {
		const src = join(srcDir, entry.name);
		const dest = join(destDir, entry.name);
		if (entry.isDirectory()) {
			written.push(...(await copyRendered(src, dest, ctx, fragments)));
		} else {
			const content = await readFile(src, "utf8");
			await writeFile(dest, renderTemplate(content, ctx, fragments));
			written.push(dest);
		}
	}
	return written;
}

async function loadFragments(framework: Framework): Promise<Fragments> {
	const base = join(TEMPLATES_DIR, "fragments", framework);
	return {
		thirdPartyApps: (await readFile(join(base, "base_apps.txt"), "utf8")).replace(/\n+$/, ""),
		frameworkExtra: (await readFile(join(base, "base_extra.txt"), "utf8")).replace(/\n+$/, ""),
	};
}

function secretKey(): string {
	return randomBytes(50).toString("base64");
}

async function targetDirIsEmpty(dir: string): Promise<boolean> {
	try {
		const entries = await readdir(dir);
		return entries.length === 0;
	} catch {
		return true; // directory does not exist yet
	}
}

async function runUv(
	env: EnvLike,
	args: string[],
	options: { cwd: string; timeout?: number; signal?: AbortSignal },
): Promise<{ output: string; code: number }> {
	const result = await env.exec("uv", args, {
		cwd: options.cwd,
		timeout: options.timeout ?? UV_TIMEOUT_MS,
		signal: options.signal,
	});
	const output = [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
	if (result.killed) {
		throw new Error(`Command cancelled: uv ${args.join(" ")}\n${output}`);
	}
	return { output, code: result.code };
}

async function checkUv(env: EnvLike): Promise<void> {
	const result = await env.exec("uv", ["--version"], { timeout: 30_000 });
	if (result.code !== 0) {
		throw new Error(
			"uv is not available. Install it first: https://docs.astral.sh/uv/ (e.g. curl -LsSf https://astral.sh/uv/install.sh | sh)",
		);
	}
}

// ---------------------------------------------------------------------------
// Scaffold core
// ---------------------------------------------------------------------------

interface ScaffoldOptions {
	projectName: string;
	framework: Framework;
	pythonVersion: string;
	targetDir: string;
}

async function scaffoldProject(
	options: ScaffoldOptions,
	env: EnvLike,
	progress: (text: string) => void,
	signal?: AbortSignal,
): Promise<{ projectDir: string; files: string[]; summary: string }> {
	const isCwd = options.projectName === ".";
	const targetDir = resolve(env.cwd, options.targetDir);
	const slug = isCwd ? slugify(basename(targetDir)) : options.projectName;
	const projectDir = isCwd ? targetDir : resolve(targetDir, slug);

	if (!isValidSlug(slug)) {
		throw new Error(`Invalid project name "${slug}". Use a lowercase slug, e.g. my-blog.`);
	}
	if (!(await targetDirIsEmpty(projectDir))) {
		throw new Error(
			`Directory ${relative(env.cwd, projectDir) || "."} already exists and is not empty. Pick a new project name or an empty directory.`,
		);
	}

	await checkUv(env);

	const pythonVersion = normalizePythonVersion(options.pythonVersion);
	const ctx: RenderContext = {
		projectName: slug,
		projectTitle: toTitle(slug),
		pythonVersion,
		requiresPython: `>=${pythonVersion}`,
		ruffTarget: `py${pythonVersion.replace(".", "")}`,
	};
	const fragments = await loadFragments(options.framework);

	// 1. uv init
	progress("Initializing project with uv…");
	const initArgs = [
		"init",
		"--bare",
		"--no-workspace",
		"--name",
		slug,
		"--python",
		pythonVersion,
		projectDir,
	];
	const init = await runUv(env, initArgs, { cwd: env.cwd, signal });
	if (init.code !== 0) {
		throw new Error(`uv init failed:\n${init.output}`);
	}

	// 2. Pin the requested Python version, then render project files on top of the uv skeleton
	await mkdir(projectDir, { recursive: true });
	await writeFile(join(projectDir, ".python-version"), `${pythonVersion}\n`);
	progress("Writing project files…");
	const files = await copyRendered(join(TEMPLATES_DIR, "common"), projectDir, ctx, fragments);
	const frameworkFiles = await copyRendered(
		join(TEMPLATES_DIR, options.framework),
		projectDir,
		ctx,
		fragments,
	);
	files.push(...frameworkFiles);

	// 3. Runtime dependencies
	progress(`Installing runtime dependencies (${RUNTIME_DEPS[options.framework].join(", ")})…`);
	const add = await runUv(env, ["add", ...RUNTIME_DEPS[options.framework]], {
		cwd: projectDir,
		signal,
	});
	if (add.code !== 0) {
		throw new Error(`uv add failed:\n${add.output}`);
	}

	// 4. Dev dependencies
	progress(`Installing dev dependencies (${DEV_DEPS.join(", ")})…`);
	const dev = await runUv(env, ["add", "--dev", ...DEV_DEPS], { cwd: projectDir, signal });
	if (dev.code !== 0) {
		throw new Error(`uv add --dev failed:\n${dev.output}`);
	}

	// 5. .env with a generated secret key
	await writeFile(
		join(projectDir, ".env"),
		`DJANGO_SECRET_KEY=${secretKey()}\nDJANGO_DEBUG=True\nDJANGO_ALLOWED_HOSTS=localhost,127.0.0.1\n`,
	);

	// 6. Generate the users app migration
	progress("Generating migrations for the users app…");
	const migrate = await runUv(env, ["run", "python", "manage.py", "makemigrations", "users"], {
		cwd: projectDir,
		signal,
	});
	if (migrate.code !== 0) {
		throw new Error(`makemigrations failed:\n${migrate.output}`);
	}

	// 7. Sanity check
	progress("Running django check…");
	const check = await runUv(env, ["run", "python", "manage.py", "check"], { cwd: projectDir, signal });
	if (check.code !== 0) {
		throw new Error(`django check failed:\n${check.output}`);
	}

	const nextSteps =
		options.framework === "standard"
			? [
					"uv run python manage.py migrate",
					"uv run python manage.py createsuperuser",
					"uv run python manage.py runserver   # then open http://localhost:8000/register",
				]
			: options.framework === "drf"
				? [
						"uv run python manage.py migrate",
						"uv run python manage.py createsuperuser",
						"uv run python manage.py runserver",
						"POST /api/auth/register  POST /api/auth/token  GET /api/auth/me (Bearer <token>)",
					]
				: [
						"uv run python manage.py migrate",
						"uv run python manage.py createsuperuser",
						"uv run python manage.py runserver",
						"API docs: http://localhost:8000/api/docs",
					];

	const summary = [
		`Django project "${slug}" created (framework: ${options.framework}, Python ${pythonVersion}).`,
		`Location: ${projectDir}`,
		"",
		"Next steps:",
		...nextSteps.map((step) => `  - ${step}`),
		"",
		"Structure follows Django Styleguide: config/django settings package, UUID users app",
		"with services/selectors/filters/tests, ruff + pytest configured in pyproject.toml.",
	].join("\n");

	return { projectDir, files, summary };
}

// ---------------------------------------------------------------------------
// Tool + command registration
// ---------------------------------------------------------------------------

export default function piDjangoExtension(pi: ExtensionAPI): void {
	pi.registerTool({
		name: "django_scaffold",
		label: "Django Scaffold",
		description:
			"Create a new Django project from scratch, initialized with uv and following the Django Styleguide conventions (config/django settings, UUID users app with auth, ruff, pytest). Asks the user which framework to use (standard / DRF / Ninja) and the Python version when they are not provided.",
		promptSnippet: "Create a new Django project from scratch with uv",
		promptGuidelines: [
			"Use django_scaffold when the user asks to create or initialize a new Django project, not for changes to an existing project.",
			"Ask the user which framework they want (standard / drf / ninja) and the Python version before calling django_scaffold when they were not already specified.",
		],
		parameters: ScaffoldParams,
		prepareArguments(args: unknown): ScaffoldParams {
			if (!args || typeof args !== "object") return {} as ScaffoldParams;
			const input = args as Record<string, unknown>;
			const result: ScaffoldParams = {
				project_name: String(input.project_name ?? "project"),
			};
			if (typeof input.framework === "string") result.framework = input.framework as Framework;
			if (typeof input.python_version === "string") result.python_version = input.python_version;
			if (typeof input.target_dir === "string") result.target_dir = input.target_dir;
			return result;
		},
		async execute(
			_toolCallId: string,
			params: ScaffoldParams,
			signal: AbortSignal | undefined,
			onUpdate: ((update: { content: { type: "text"; text: string }[]; details: unknown }) => void) | undefined,
			ctx: ExtensionContext,
		): Promise<{ content: { type: "text"; text: string }[]; details: unknown }> {
			const env = toEnvLike(ctx, pi);
			const progress = (text: string): void => {
				onUpdate?.({ content: [{ type: "text", text }], details: { progress: text } });
			};

			try {
				if (signal?.aborted) {
					return { content: [{ type: "text", text: "Scaffold cancelled." }], details: { cancelled: true } };
				}

				// framework: param > ui prompt > default
				let framework = params.framework;
				if (!framework && env.hasUI) {
					const choice = await env.ui.select("Django framework", FRAMEWORKS.map((f) => `${f} — ${FRAMEWORK_LABELS[f]}`));
					framework = choice ? (choice.split(" — ")[0] as Framework) : undefined;
				}
				if (!framework) framework = DEFAULT_FRAMEWORK;
				if (!FRAMEWORKS.includes(framework)) {
					throw new Error(`Unknown framework "${framework}". Use one of: ${FRAMEWORKS.join(", ")}.`);
				}

				// python version: param > ui prompt > default
				let pythonVersion = params.python_version;
				if (!pythonVersion && env.hasUI) {
					const choice = await env.ui.select("Python version", [...PYTHON_VERSIONS]);
					pythonVersion = choice ?? DEFAULT_PYTHON_VERSION;
				}
				if (!pythonVersion) pythonVersion = DEFAULT_PYTHON_VERSION;
				normalizePythonVersion(pythonVersion); // throws on invalid input

				const result = await scaffoldProject(
					{
						projectName: params.project_name,
						framework,
						pythonVersion,
						targetDir: params.target_dir ?? ".",
					},
					env,
					progress,
					signal,
				);

				return {
					content: [{ type: "text", text: result.summary }],
					details: { projectDir: result.projectDir, files: result.files },
				};
			} catch (error) {
				const message = error instanceof Error ? error.message : String(error);
				return {
					content: [{ type: "text", text: `django_scaffold failed: ${message}` }],
					details: { error: true, message },
				};
			}
		},
	});

	pi.registerCommand("django-scaffold", {
		description:
			"Scaffold a new Django project with uv following the Django Styleguide. Usage: /django-scaffold <project-name> [standard|drf|ninja] [python-version]",
		handler: async (args: string, ctx: ExtensionCommandContext): Promise<void> => {
			const parts = args.trim().split(/\s+/).filter(Boolean);
			if (parts.length === 0) {
				ctx.ui.notify("Usage: /django-scaffold <project-name> [standard|drf|ninja] [python-version]", "warning");
				return;
			}
			const [name, frameworkArg, pythonArg] = parts;
			const framework = (frameworkArg ?? DEFAULT_FRAMEWORK) as Framework;
			if (!FRAMEWORKS.includes(framework)) {
				ctx.ui.notify(`Unknown framework "${frameworkArg}". Use one of: ${FRAMEWORKS.join(", ")}.`, "error");
				return;
			}
			const pythonVersion = pythonArg ?? DEFAULT_PYTHON_VERSION;
			try {
				normalizePythonVersion(pythonVersion);
			} catch (error) {
				ctx.ui.notify(error instanceof Error ? error.message : String(error), "error");
				return;
			}

			const env = toEnvLike(ctx, pi);
			const logs: string[] = [];
			const progress = (text: string): void => logs.push(text);

			try {
				const result = await scaffoldProject(
					{ projectName: name, framework, pythonVersion, targetDir: "." },
					env,
					progress,
				);
				ctx.ui.notify(`Created ${result.projectDir}`, "info");
				ctx.ui.notify(logs.join(" → "), "info");
			} catch (error) {
				const message = error instanceof Error ? error.message : String(error);
				ctx.ui.notify(`django-scaffold failed: ${message}`, "error");
			}
		},
	});
}

function toEnvLike(ctx: ExtensionContext, pi: ExtensionAPI): EnvLike {
	return {
		hasUI: ctx.hasUI,
		cwd: ctx.cwd,
		exec: (command, args, options) => pi.exec(command, args, options),
		ui: {
			select: (title, options) => ctx.ui.select(title, options),
			notify: (message, kind) => ctx.ui.notify(message, kind),
		},
	};
}