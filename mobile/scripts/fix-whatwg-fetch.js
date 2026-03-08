const fs = require("fs");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..");
const pkgRoot = path.join(projectRoot, "node_modules", "whatwg-fetch");
const distDir = path.join(pkgRoot, "dist");
const distFile = path.join(distDir, "fetch.umd.js");
const sourceFile = path.join(pkgRoot, "fetch.js");

if (fs.existsSync(distFile)) {
  process.exit(0);
}

if (!fs.existsSync(sourceFile)) {
  process.exit(0);
}

try {
  fs.mkdirSync(distDir, { recursive: true });
  fs.copyFileSync(sourceFile, distFile);
} catch (error) {
  // Avoid failing install on best-effort fix.
  process.exit(0);
}
