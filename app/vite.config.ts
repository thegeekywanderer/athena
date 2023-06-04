import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default ({ mode }) => {
    process.env = { ...process.env, ...loadEnv(mode, process.cwd(), "") };

    return defineConfig({
        plugins: [react()],
        build: {
            outDir: "../backend/static",
            emptyOutDir: true,
            sourcemap: true
        },
        server: {
            proxy: {
                "/ask": process.env.BACKEND_ENDPOINT,
                "/chat": process.env.BACKEND_ENDPOINT,
                "/file/upload": process.env.BACKEND_ENDPOINT
            }
        }
    });
};
