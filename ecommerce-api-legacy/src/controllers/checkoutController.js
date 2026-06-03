const checkoutService = require('../services/checkoutService');
const { cache } = require('../services/cacheService');
const { created } = require('../middlewares/response');

function validateBody(body) {
    const errors = [];
    const name = body.usr || body.name;
    const email = body.eml || body.email;
    const password = body.pwd || body.password;
    const courseId = body.c_id || body.courseId;
    const cardNumber = body.card || body.cardNumber;
    if (!name) errors.push('name (usr) é obrigatório');
    if (!email) errors.push('email (eml) é obrigatório');
    if (!courseId) errors.push('courseId (c_id) é obrigatório');
    if (!cardNumber) errors.push('cardNumber (card) é obrigatório');
    if (errors.length) {
        const err = new Error(errors.join('; '));
        err.status = 400;
        throw err;
    }
    return { name, email, password, courseId, cardNumber };
}

async function checkout(req, res, next) {
    try {
        const data = validateBody(req.body);
        const result = await checkoutService.checkout(req.db, data);
        cache.set(`last_checkout_${result.userId}`, result.course);
        return created(res, { message: 'Sucesso', enrollment_id: result.enrollmentId });
    } catch (err) {
        next(err);
    }
}

module.exports = { checkout };
