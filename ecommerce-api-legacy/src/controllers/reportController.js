const reportService = require('../services/reportService');
const { ok } = require('../middlewares/response');

async function financial(req, res, next) {
    try {
        const data = await reportService.financialReport(req.db);
        return ok(res, data);
    } catch (err) {
        next(err);
    }
}

module.exports = { financial };
