CREATE_CONTRACT = """
    INSERT INTO contracts (
        realm,
        contract_number,
        room_id,
        tenant_username,
        start_date,
        end_date,
        monthly_rate,
        deposit_amount,
        status
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, 'active'
    ) RETURNING id;
"""

GET_CONTRACT_WITH_PAYMENTS = """
    SELECT 
        c.*,
        json_agg(p.*) as payments
    FROM contracts c
    LEFT JOIN payments p ON p.contract_id = c.id
    WHERE c.id = $1 AND c.realm = $2
    GROUP BY c.id;
"""

GET_ALL_CONTRACTS_BY_REALM = """
    SELECT * FROM contracts WHERE realm = $1 ORDER BY start_date DESC;
"""

GET_ACTIVE_CONTRACT_BY_TENANT = """
    SELECT * FROM contracts WHERE tenant_username = $1 AND status = 'active' AND realm = $2;
"""