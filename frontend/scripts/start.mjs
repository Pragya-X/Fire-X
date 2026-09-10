// Serve the standalone build with the same assets copied by the Docker runner.
import { cp, access } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const output = path.join(root, ".next", "standalone");
const server = path.join(output, "server.js");
try {
  await access(server);
} catch {
  console.error("Production build is missing. Run npm run build before npm start.");
  process.exit(1);
}
await cp(path.join(root, ".next", "static"), path.join(output, ".next", "static"), { recursive: true });
try {
  await access(path.join(root, "public"));
  await cp(path.join(root, "public"), path.join(output, "public"), { recursive: true });
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}
process.env.PORT ??= "3000";
process.env.HOSTNAME ??= "0.0.0.0";
await import(pathToFileURL(server).href);
