const sqlite3 = require('sqlite3');
const { promisify } = require('util');
const { config } = require('./index');
const { hashPassword } = require('../services/cryptoService');

function createDb() {
    const db = new sqlite3.Database(config.dbPath);
    db.run('PRAGMA foreign_keys = ON');
    return db;
}

function wrap(db) {
    return {
        raw: db,
        run: (sql, params = []) => new Promise((resolve, reject) => {
            db.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        }),
        get: promisify(db.get.bind(db)),
        all: promisify(db.all.bind(db)),
        exec: promisify(db.exec.bind(db)),
        close: promisify(db.close.bind(db)),
    };
}

async function initSchema(db) {
    await db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            pass TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
            amount REAL NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY,
            action TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    `);
}

async function seedIfEmpty(db) {
    const row = await db.get('SELECT COUNT(*) AS count FROM users');
    if (row.count > 0) return;

    const passHash = await hashPassword(config.seedDefaultPassword);
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', passHash]);
    await db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1)");
    await db.run("INSERT INTO courses (title, price, active) VALUES ('Docker', 497.00, 1)");
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { createDb, wrap, initSchema, seedIfEmpty };
