const userService = require('../services/userService');
const { ok } = require('../middlewares/response');

async function remove(req, res, next) {
    try {
        const result = await userService.remove(req.db, req.params.id);
        return ok(res, { message: 'Usuário removido com cascade de matrículas e pagamentos', ...result });
    } catch (err) {
        next(err);
    }
}

module.exports = { remove };
