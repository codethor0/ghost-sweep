import { defineConfig, globalIgnores } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import eslintConfigPrettier from "eslint-config-prettier";

export default defineConfig([
  ...nextCoreWebVitals,
  eslintConfigPrettier,
  globalIgnores([".next/**", "node_modules/**", "next-env.d.ts", "coverage/**"]),
]);
