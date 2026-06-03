const logger = require('./logger');

function errorHandler(err, req, res, _next) {
    const status = err.status || 500;
    if (status >= 500) {
        logger.error('request.error', { path: req.path, message: err.message, stack: err.stack });
    } else {
        logger.warn('request.failed', { path: req.path, message: err.message, status });
    }
    res.status(status).json({
        error: { message: status >= 500 ? 'Erro interno' : err.message },
    });
}

module.exports = errorHandler;
