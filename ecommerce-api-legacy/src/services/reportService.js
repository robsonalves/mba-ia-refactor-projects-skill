async function financialReport(db) {
    const rows = await db.all(`
        SELECT
            c.id AS course_id,
            c.title AS course,
            u.name AS student_name,
            p.amount AS paid_amount,
            p.status AS payment_status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN payments p ON p.enrollment_id = e.id
        ORDER BY c.id
    `);

    const byCourse = new Map();
    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, { course: row.course, revenue: 0, students: [] });
        }
        const bucket = byCourse.get(row.course_id);
        if (row.student_name) {
            const paid = row.payment_status === 'PAID' ? row.paid_amount : 0;
            bucket.revenue += paid || 0;
            bucket.students.push({
                student: row.student_name,
                paid: row.paid_amount || 0,
            });
        }
    }

    return Array.from(byCourse.values());
}

module.exports = { financialReport };
