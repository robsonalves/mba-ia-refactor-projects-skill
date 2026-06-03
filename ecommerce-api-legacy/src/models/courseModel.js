function findActiveById(db, id) {
    return db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]);
}

function findAll(db) {
    return db.all('SELECT id, title, price, active FROM courses');
}

module.exports = { findActiveById, findAll };
