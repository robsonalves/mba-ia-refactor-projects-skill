function log(db, action) {
    return db.run('INSERT INTO audit_logs (action) VALUES (?)', [action]);
}

module.exports = { log };
