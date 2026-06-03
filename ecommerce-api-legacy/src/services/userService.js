const userModel = require('../models/userModel');

async function remove(db, id) {
    const userId = parseInt(id, 10);
    if (Number.isNaN(userId)) {
        throw Object.assign(new Error('ID inválido'), { status: 400 });
    }
    const result = await userModel.remove(db, userId);
    if (result.changes === 0) {
        throw Object.assign(new Error('Usuário não encontrado'), { status: 404 });
    }
    return { id: userId, deletedDependencies: 'cascade' };
}

module.exports = { remove };
