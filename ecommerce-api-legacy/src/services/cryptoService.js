const crypto = require('crypto');

const ITERATIONS = 100000;
const KEYLEN = 32;
const DIGEST = 'sha256';

function hashPassword(password) {
    return new Promise((resolve, reject) => {
        const salt = crypto.randomBytes(16).toString('hex');
        crypto.pbkdf2(password, salt, ITERATIONS, KEYLEN, DIGEST, (err, derived) => {
            if (err) return reject(err);
            resolve(`pbkdf2$${ITERATIONS}$${salt}$${derived.toString('hex')}`);
        });
    });
}

function verifyPassword(password, stored) {
    return new Promise((resolve, reject) => {
        if (!stored || !stored.startsWith('pbkdf2$')) return resolve(false);
        const [, iter, salt, hashHex] = stored.split('$');
        crypto.pbkdf2(password, salt, parseInt(iter, 10), KEYLEN, DIGEST, (err, derived) => {
            if (err) return reject(err);
            const expected = Buffer.from(hashHex, 'hex');
            resolve(crypto.timingSafeEqual(expected, derived));
        });
    });
}

module.exports = { hashPassword, verifyPassword };
