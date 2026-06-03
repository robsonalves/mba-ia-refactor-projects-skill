function findByEmail(db, email) {
    return db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
}

async function insert(db, { name, email, passHash }) {
    const result = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, passHash]
    );
    return result.lastID;
}

function remove(db, id) {
    return db.run('DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, insert, remove };
