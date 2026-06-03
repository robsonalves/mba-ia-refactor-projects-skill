const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');

function registerRoutes(app) {
    app.post('/api/checkout', checkoutController.checkout);
    app.get('/api/admin/financial-report', reportController.financial);
    app.delete('/api/users/:id', userController.remove);
}

module.exports = { registerRoutes };
