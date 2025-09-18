import { createPyodide } from "cloudflare-workers-pyodide";

const loader = createPyodide();

export default {
  async fetch(request, env, ctx) {
    const pyodide = await loader;
    return pyodide.fetch(request, env, ctx);
  },
};