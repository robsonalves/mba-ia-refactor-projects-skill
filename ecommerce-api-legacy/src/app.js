const express = require('express');

const { config } = require('./config');
const { createDb, wrap, initSchema, seedIfEmpty } = require('./config/database');
const { registerRoutes } = require('./routes');
const errorHandler = require('./middlewares/errorHandler');
const logger = require('./middlewares/logger');

async function createApp() {
    const db = wrap(createDb());
    await initSchema(db);
    await seedIfEmpty(db);

    const app = express();
    app.use(express.json());

    app.use((req, _res, next) => {
        req.db = db;
        next();
    });

    registerRoutes(app);
    app.use(errorHandler);

    return { app, db };
}

if (require.main === module) {
    createApp()
        .then(({ app }) => {
            app.listen(config.port, () => {
                logger.info('server.started', { port: config.port });
            });
        })
        .catch((err) => {
            logger.error('server.startup_failed', { message: err.message, stack: err.stack });
            process.exit(1);
        });
}

module.exports = { createApp };
