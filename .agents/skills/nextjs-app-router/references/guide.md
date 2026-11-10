# nextjs-app-router: project guide

Verified against Next.js 16.4 docs (nextjs.org/docs/app/getting-started). Every docs page serves Markdown; the version installed in the project ships its docs at `node_modules/next/dist/docs/` — prefer those for exact behavior of the installed release.

## Starting a project
- `npx create-next-app@latest` — recommended defaults: TypeScript, ESLint, Tailwind CSS, App Router, Turbopack, Cache Components, import alias `@/*`, and an `AGENTS.md` for coding agents. Use them unless the project says otherwise.
- `next dev` and `next build` run on Turbopack by default; Webpack via `next dev --webpack` / `next build --webpack`.
- Scripts: `dev`, `build`, `start`, `lint` (ESLint CLI — `next lint` was removed in 16; Biome is also supported).

## Structure conventions
- `app/` — routes: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, `template.tsx`, `default.tsx`, `route.ts`, `proxy.ts`, `instrumentation.ts` / `instrumentation-client.ts`.
- Route groups `(name)`, dynamic `[id]` / `[...slug]`, parallel routes `@slot`, intercepting routes `(.)path`, metadata files (favicon, manifest, robots.txt, sitemap.xml, opengraph-image).
- Optional `src/` for separating app code from config. Alias `@/*` in `tsconfig.json` paths.
- Label same-named files in the editor: VS Code/Cursor `workbench.editor.customLabels.patterns` for `page.tsx`/`layout.tsx`/... (see installation docs §Set up your editor).

## Environment and config
- `NEXT_PUBLIC_*` for client-exposed values; everything else stays server-only. Config via environment, never in code.
- `next.config.ts` — key options: `cacheComponents`, `cacheHandlers`, `turbopack*`, `output`, `serverExternalPackages`, `transpilePackages`, `typedRoutes`, `images`, `deploymentId`, `allowedDevOrigins`.

## Keeping current
- `npx next upgrade` upgrades the package; docs update with it. `npx next@canary upgrade --agent=latest` runs a coding-agent upgrade with verification policies.
- Next.js exposes an MCP endpoint for coding agents and the "AI coding agents" guide — use them for inspection and issue reporting when the project has it enabled.
- Version-skew protection via `deploymentId` keeps old browser tabs compatible with new deploys.

## Tooling
- TypeScript first (`next dev` generates/maintains `tsconfig.json`); workspace TS version in the IDE.
- ESLint via explicit `eslint.config.mjs` or Biome; lint in CI, not in build.
- Testing: Vitest (units), Playwright (E2E), Jest still documented; cache build output in CI (`docs/app/guides/ci-build-caching`).

## Pitfalls
- Baking the Pages Router mental model into App Router code (no `pages/` conventions, no `getServerSideProps`).
- Skipping the upgrade step until versions drift years apart — small upgrades stay small.
- Committing `next.config` hacks copied from old blog posts instead of current docs.
