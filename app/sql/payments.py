CREATE_PAYMENT = """
    INSERT INTO payments (
        realm, contract_id, payment_number, amount, payment_date,
        payment_method, notes, created_by, status, proof_of_payment_url
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending', $9)
    RETURNING id;
"""

GET_PENDING_PAYMENTS_BY_REALM = """
    SELECT * FROM payments WHERE realm = $1 AND status = 'pending' ORDER BY payment_date DESC;
"""

APPROVE_PAYMENT = """
    UPDATE payments SET status = 'approved' WHERE id = $1 AND realm = $2;
"""

GET_PAYMENTS_BY_TENANT = """
    SELECT * FROM payments WHERE created_by = $1 AND realm = $2 ORDER BY payment_date DESC;
"""
