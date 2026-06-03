function ok(res, data, status = 200) {
    return res.status(status).json({ data });
}

function created(res, data) {
    return ok(res, data, 201);
}

module.exports = { ok, created };
