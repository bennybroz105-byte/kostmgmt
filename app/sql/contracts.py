CREATE_CONTRACT = """
    INSERT INTO contracts (
        contract_number,
        room_id,
        tenant_username,
        start_date,
        end_date,
        monthly_rate,
        deposit_amount,
        status
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, 'active'
    ) RETURNING id;
"""

GET_CONTRACT_WITH_PAYMENTS = """
    SELECT 
        c.*,
        json_agg(p.*) as payments
    FROM contracts c
    LEFT JOIN payments p ON p.contract_id = c.id
    WHERE c.id = $1
    GROUP BY c.id;
"""