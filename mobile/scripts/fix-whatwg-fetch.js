const fs = require("fs");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..");

const ensureFile = ({ source, destination }) => {
  if (fs.existsSync(destination)) {
    return;
  }

  if (!fs.existsSync(source)) {
    return;
  }

  try {
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.copyFileSync(source, destination);
  } catch (error) {
    // Avoid failing install on best-effort fix.
  }
};

// Fix missing dist file for whatwg-fetch.
const fetchRoot = path.join(projectRoot, "node_modules", "whatwg-fetch");
ensureFile({
  source: path.join(fetchRoot, "fetch.js"),
  destination: path.join(fetchRoot, "dist", "fetch.umd.js"),
});

// Fix missing helper file in @babel/runtime (callSuper).
const babelRuntimeRoot = path.join(projectRoot, "node_modules", "@babel", "runtime");
ensureFile({
  source: path.join(babelRuntimeRoot, "helpers", "esm", "callSuper.js"),
  destination: path.join(babelRuntimeRoot, "helpers", "callSuper.js"),
});
