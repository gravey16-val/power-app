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
