const crypto = require('crypto');
const logger = require('../middlewares/logger');

function maskCard(cardNumber) {
    if (!cardNumber || cardNumber.length < 4) return '****';
    return `****${cardNumber.slice(-4)}`;
}

async function charge({ cardNumber, amount }) {
    if (!cardNumber || typeof cardNumber !== 'string') {
        throw Object.assign(new Error('Cartão inválido'), { status: 400 });
    }
    logger.info('payment.attempt', { card: maskCard(cardNumber), amount });

    const status = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
    return {
        status,
        transactionId: crypto.randomUUID(),
        amount,
    };
}

module.exports = { charge, maskCard };
