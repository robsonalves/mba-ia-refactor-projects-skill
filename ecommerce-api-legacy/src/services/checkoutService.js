const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditModel = require('../models/auditModel');
const cryptoService = require('./cryptoService');
const paymentGateway = require('./paymentGateway');

async function checkout(db, { name, email, password, courseId, cardNumber }) {
    const course = await courseModel.findActiveById(db, courseId);
    if (!course) {
        throw Object.assign(new Error('Curso não encontrado'), { status: 404 });
    }

    await db.run('BEGIN TRANSACTION');
    try {
        let user = await userModel.findByEmail(db, email);
        let userId = user ? user.id : null;
        if (!userId) {
            const passHash = await cryptoService.hashPassword(password || 'changeme');
            userId = await userModel.insert(db, { name, email, passHash });
        }

        const paymentResult = await paymentGateway.charge({
            cardNumber,
            amount: course.price,
        });

        if (paymentResult.status !== 'PAID') {
            await db.run('ROLLBACK');
            throw Object.assign(new Error('Pagamento recusado'), { status: 402 });
        }

        const enrollmentId = await enrollmentModel.insert(db, { userId, courseId });
        await paymentModel.insert(db, {
            enrollmentId,
            amount: course.price,
            status: paymentResult.status,
        });
        await auditModel.log(db, `Checkout curso ${courseId} por ${userId}`);

        await db.run('COMMIT');
        return { enrollmentId, userId, course: course.title };
    } catch (err) {
        try {
            await db.run('ROLLBACK');
        } catch (_rbErr) {}
        throw err;
    }
}

module.exports = { checkout };
