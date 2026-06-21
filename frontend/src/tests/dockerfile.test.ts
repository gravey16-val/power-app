import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

// Regression guard for ticket #83: the frontend Docker build failed/hung at the
// `COPY . .` step following dependency install. Two root causes are locked down:
//   1. A missing .dockerignore let the host's platform-specific node_modules be
//      copied over the deps installed inside the image.
//   2. `npm install` (ignoring the now-committed lockfile) produced
//      non-reproducible installs; the build now uses `npm ci` against the lock.
//
// Tests run inside the frontend container where the build context root is the
// working directory (/app), so the Dockerfile and .dockerignore sit at cwd.
function read(file: string): string {
  return readFileSync(join(process.cwd(), file), 'utf-8')
}

// Strip blank lines and `#` comments so we assert on real Dockerfile
// instructions, not the prose that explains them.
function instructionLines(contents: string): string[] {
  return contents
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0 && !line.startsWith('#'))
}

function dockerignoreEntries(contents: string): string[] {
  return instructionLines(contents)
}

describe('frontend Docker build config', () => {
  it('installs dependencies reproducibly with npm ci and the committed lockfile', () => {
    const lines = instructionLines(read('Dockerfile'))
    const dockerfile = lines.join('\n')
    // Both the manifest and the lockfile must be copied before installing,
    // otherwise `npm ci` has nothing to install from.
    expect(dockerfile).toMatch(/COPY\s+package\.json\s+package-lock\.json/)
    expect(dockerfile).toMatch(/RUN\s+npm\s+ci\b/)
    // The non-deterministic `npm install` must not creep back into an
    // actual instruction (comments mentioning it are fine).
    expect(lines.some((line) => /npm\s+install\b/.test(line))).toBe(false)
  })

  it('excludes node_modules from the build context via .dockerignore', () => {
    const entries = dockerignoreEntries(read('.dockerignore'))
    // node_modules is the entry that prevents a host-built, wrong-platform
    // dependency tree from overwriting the image's deps at `COPY . .`.
    expect(entries).toContain('node_modules')
  })
})

// Build-time environment configuration (this ticket). VITE_API_URL is inlined
// into the bundle by Vite at build time, so it must be a declared build ARG —
// otherwise `docker build` / `docker buildx bake` cannot supply it and the
// build silently falls back to a default.
describe('frontend build-time env configuration', () => {
  it('declares VITE_API_URL as a build ARG so bake/build can pass it', () => {
    const lines = instructionLines(read('Dockerfile'))
    const dockerfile = lines.join('\n')
    // The ARG makes the value injectable via --build-arg / bake / compose args.
    expect(dockerfile).toMatch(/ARG\s+VITE_API_URL/)
    // Promoting it to ENV makes the same value reach the dev server at runtime.
    expect(dockerfile).toMatch(/ENV\s+VITE_API_URL=\$VITE_API_URL/)
  })

  it('keeps secrets out of the build context but keeps required build files', () => {
    const entries = dockerignoreEntries(read('.dockerignore'))
    // .env must be excluded so local secrets are never baked into a layer...
    expect(entries).toContain('.env')
    // ...but the files the build genuinely needs must NOT be excluded.
    for (const required of ['package.json', 'package-lock.json', 'Dockerfile']) {
      expect(entries).not.toContain(required)
    }
  })
})
