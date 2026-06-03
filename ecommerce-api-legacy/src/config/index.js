const config = {
    port: parseInt(process.env.PORT || '3000', 10),
    dbPath: process.env.DB_PATH || './lms.db',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    smtpUser: process.env.SMTP_USER || '',
    smtpPass: process.env.SMTP_PASS || '',
    seedDefaultPassword: process.env.SEED_DEFAULT_PASSWORD || 'changeme',
    logLevel: process.env.LOG_LEVEL || 'info',
};

module.exports = { config };
